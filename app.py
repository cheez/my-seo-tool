import streamlit as st
import cloudscraper
from bs4 import BeautifulSoup
import pandas as pd
from fake_useragent import UserAgent
from urllib.parse import urlparse, urljoin
import time
import re
from collections import Counter

st.set_page_config(page_title="Professional SEO Analyzer v1.8", layout="wide")

st.title("SEO & 키워드 종합 분석 리포트(sanghee kim - ICS 제외)")
st.caption("On-Page SEO부터 정밀 이미지 경로 분석까지, 전문적인 진단 결과를 제공합니다.")
st.markdown("---")

url = st.text_input("진단할 사이트 주소 (https:// 필수)", "https://")

if st.button("종합 분석 시작"):
    if url.startswith("http"):
        try:
            with st.spinner('사이트 데이터를 정밀 분석 중입니다...'):
                start_time = time.time()
                ua = UserAgent()
                scraper = cloudscraper.create_scraper()
                
                # 데이터 요청 및 인코딩 설정
                res = scraper.get(url, headers={'User-Agent': ua.random}, timeout=20)
                res.raise_for_status()
                
                # 한글 깨짐 방지 로직
                if res.encoding == 'ISO-8859-1':
                    res.encoding = res.apparent_encoding
                
                load_speed = round((time.time() - start_time), 2)
                soup = BeautifulSoup(res.text, 'html.parser')
                parsed_url = urlparse(url)
                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                text_content = soup.get_text()

            # --- 1. 사이트 퍼포먼스 ---
            st.header("1️⃣ 사이트 퍼포먼스 및 기술 점검")
            t_col1, t_col2, t_col3, t_col4 = st.columns(4)
            viewport = soup.find('meta', attrs={'name': 'viewport'})
            with t_col1:
                st.metric("로딩 속도", f"{load_speed}초")
                if load_speed > 3: st.error("⚠️ 느림")
                else: st.success("✅ 빠름")
            with t_col2:
                st.metric("모바일 최적화", "✅ 확인" if viewport else "❌ 미설정")
            with t_col3:
                st.metric("보안 연결(HTTPS)", "✅ 안전" if url.startswith("https") else "⚠️ 위험")
            with t_col4:
                ratio = round((len(text_content) / len(res.text)) * 100, 1) if len(res.text) > 0 else 0
                st.metric("콘텐츠 비중", f"{ratio}%")

            st.divider()

            # --- 2. 검색 및 SNS 노출 ---
            st.header("2️⃣ 검색 및 SNS 노출 최적화")
            title_tag = soup.find('title')
            desc_tag = soup.find('meta', attrs={'name': 'description'})
            og_img_tag = soup.find('meta', attrs={'property': 'og:image'})
            
            title_text = title_tag.get_text().strip() if title_tag else "❌ 누락"
            desc_text = desc_tag.get('content').strip() if desc_tag else "❌ 누락"

            m_col1, m_col2 = st.columns([2, 1])
            with m_col1:
                st.subheader("메타 태그 정보")
                st.write(f"**Title:** {title_text}")
                st.write(f"**Description:** {desc_text}")
            with m_col2:
                st.subheader("SNS 공유 미리보기")
                if og_img_tag: st.image(og_img_tag['content'], use_container_width=True)
                else: st.error("❌ SNS 이미지 누락")

            st.divider()

            # --- 3. 콘텐츠 키워드 분석 ---
            st.header("3️⃣ 콘텐츠 키워드 분석 (Top 10)")
            words = re.findall(r'[가-힣a-zA-Z]{2,}', text_content)
            common_words = Counter(words).most_common(10)
            if common_words:
                k_df = pd.DataFrame(common_words, columns=['키워드', '빈도수'])
                k_col1, k_col2 = st.columns(2)
                with k_col1: st.table(k_df)
                with k_col2: st.bar_chart(k_df.set_index('키워드'))

            st.divider()

            # --- 4. 웹 표준 및 구조 ---
            st.header("4️⃣ 웹 표준 및 문서 구조")
            h1s = [h.get_text().strip() for h in soup.find_all('h1')]
            c_w1, c_w2 = st.columns(2)
            with c_w1:
                st.subheader("Heading (H1) 구조")
                st.write(f"H1 태그 개수: {len(h1s)}개")
                for h_txt in h1s: st.caption(f"• {h_txt}")
            with c_w2:
                st.subheader("보안 및 링크")
                ext_links = soup.find_all('a', href=True, target="_blank")
                unsafe = [l for l in ext_links if 'noopener' not in (l.get('rel') or [])]
                st.write(f"보안 취약 외부 링크: {len(unsafe)}개")

            st.divider()

            # --- 5. 이미지 분석 (Alt 인식 오류 수정 완료) ---
            st.header("5️⃣ 이미지 분석 및 Alt 속성 (전체 리스트)")
            imgs = soup.find_all('img')
            img_list = []
            
            for i in imgs:
                # [수정포인트] Alt 속성을 더 정밀하게 체크합니다.
                alt_val = i.get('alt', '').strip()
                
                # 불필요한 이미지(픽셀, 공백 등) 제외 로직
                raw_src = i.get('src', '')
                if any(p in raw_src.lower() for p in ['blank', 'pixel', 'spacer', 'transparent']):
                    continue

                # 경로 생성
                if raw_src:
                    if raw_src.startswith('//'): full_src = "https:" + raw_src
                    else: full_src = urljoin(base_url, raw_src)
                else:
                    full_src = "경로 찾을 수 없음"

                img_list.append({
                    "상태": "✅" if alt_val else "❌ 누락",
                    "Alt 내용": alt_val if alt_val else "내용 없음",
                    "이미지 경로": full_src
                })

            if img_list:
                # 스크롤 없이 전체 노출을 원하시면 st.table(df)을 쓰셔도 됩니다.
                # 하지만 데이터가 많을 때의 안정성을 위해 st.dataframe을 추천합니다.
                st.dataframe(pd.DataFrame(img_list), use_container_width=True, height=600)
                st.info(f"총 {len(img_list)}개의 이미지를 발견했습니다.")
            else:
                st.info("발견된 이미지가 없습니다.")

        except Exception as e:
            st.error(f"분석 중 오류 발생: {str(e)}")
    else:
        st.warning("URL을 정확히 입력해 주세요.")
