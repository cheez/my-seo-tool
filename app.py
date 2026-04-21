import streamlit as st
import cloudscraper
from bs4 import BeautifulSoup
import pandas as pd
from fake_useragent import UserAgent
from urllib.parse import urlparse, urljoin
import time
import re
from collections import Counter

# 1. 페이지 설정
st.set_page_config(page_title="Professional SEO Analyzer v2.0", layout="wide")

# 2. 원래 제목 유지
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
                
                # 데이터 요청
                res = scraper.get(url, headers={'User-Agent': ua.random}, timeout=20)
                res.raise_for_status()
                
                # 한글 인코딩 보정
                if res.encoding == 'ISO-8859-1':
                    res.encoding = res.apparent_encoding
                
                load_speed = round((time.time() - start_time), 2)
                soup = BeautifulSoup(res.text, 'html.parser')
                parsed_url = urlparse(url)
                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                text_content = soup.get_text()

            # --- 1️⃣ 사이트 퍼포먼스 및 기술 점검 ---
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

            # --- 2️⃣ 검색 및 SNS 노출 최적화 ---
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

            # --- 3️⃣ 콘텐츠 키워드 분석 (Top 10) ---
            st.header("3️⃣ 콘텐츠 키워드 분석 (Top 10)")
            words = re.findall(r'[가-힣a-zA-Z]{2,}', text_content)
            common_words = Counter(words).most_common(10)
            if common_words:
                k_df = pd.DataFrame(common_words, columns=['키워드', '빈도수'])
                k_col1, k_col2 = st.columns(2)
                with k_col1: st.table(k_df)
                with k_col2: st.bar_chart(k_df.set_index('키워드'))

            st.divider()

            # --- 4️⃣ 웹 표준 및 문서 구조 ---
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

            # --- 5️⃣ 이미지 분석 및 Alt 속성 (오류 수정 및 전체 경로 노출) ---
            st.header("5️⃣ 이미지 분석 및 Alt 속성 (전체 리스트)")
            imgs = soup.find_all('img')
            img_data = []
            
            for i in imgs:
                # [수정] Alt 존재 여부를 속성 단위로 체크하여 정확도 극대화
                alt_val = i.get('alt')
                alt_text = alt_val.strip() if alt_val is not None else ""
                
                raw_src = i.get('src', '').strip()
                if not raw_src or any(p in raw_src.lower() for p in ['blank', 'pixel', 'spacer', 'transparent']):
                    continue

                if raw_src.startswith('//'): full_src = "https:" + raw_src
                else: full_src = urljoin(base_url, raw_src)
                
                # 전체 경로를 보여주면서 클릭 가능한 <a> 태그 생성
                clickable_path = f'<a href="{full_src}" target="_blank" style="text-decoration: none; color: #007bff; word-break: break-all;">{full_src}</a>'

                img_data.append({
                    "상태": "✅" if alt_text else "❌ 누락",
                    "Alt 내용": alt_text if alt_text else "내용 없음",
                    "이미지 경로 (클릭 가능)": clickable_path
                })

            if img_data:
                df = pd.DataFrame(img_data)
                # 스크롤 없이 하단으로 쭉 나열하는 HTML 테이블
                table_html = df.to_html(escape=False, index=False, justify='left')
                st.write(table_html, unsafe_allow_html=True)
                st.info(f"총 {len(img_data)}개의 유효 이미지를 발견했습니다.")
            else:
                st.info("발견된 이미지가 없습니다.")

        except Exception as e:
            st.error(f"분석 중 오류 발생: {str(e)}")
    else:
        st.warning("URL을 정확히 입력해 주세요.")
