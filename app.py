import streamlit as st
import cloudscraper
from bs4 import BeautifulSoup
import pandas as pd
from fake_useragent import UserAgent
from urllib.parse import urlparse, urljoin
import time
import re
from collections import Counter

# 페이지 설정
st.set_page_config(page_title="Professional SEO Analyzer", layout="wide")

st.title("SEO & 키워드 분석 리포트")
st.caption("On-Page SEO부터 키워드 밀도, 로딩 속도까지 한 번에 진단합니다.")
st.markdown("---")

url = st.text_input("진단할 사이트 주소 (https:// 필수)", "https://")

if st.button("종합 분석 시작"):
    if url.startswith("http"):
        try:
            with st.spinner('사이트 데이터를 분석 중입니다. 잠시만 기다려 주세요...'):
                start_time = time.time()
                
                ua = UserAgent()
                scraper = cloudscraper.create_scraper()
                # 타임아웃 및 랜덤 유저에이전트 설정
                res = scraper.get(url, headers={'User-Agent': ua.random}, timeout=20)
                res.raise_for_status()
                
                end_time = time.time()
                load_speed = round((end_time - start_time), 2)
                
                res.encoding = res.apparent_encoding
                soup = BeautifulSoup(res.text, 'html.parser')
                
                # 상대 경로 해결을 위한 베이스 URL 추출
                parsed_url = urlparse(url)
                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

            # --- 1. 퍼포먼스 및 기술 점검 ---
            st.header("1️⃣ 사이트 퍼포먼스 및 기술 점검")
            t_col1, t_col2, t_col3, t_col4 = st.columns(4)
            
            viewport = soup.find('meta', attrs={'name': 'viewport'})
            
            with t_col1:
                st.metric("로딩 속도", f"{load_speed}초")
                if load_speed > 3: st.error("⚠️ 느림 (3초 이내 권장)")
                else: st.success("✅ 빠름")
            with t_col2:
                st.metric("모바일 최적화", "✅ 확인" if viewport else "❌ 미설정")
            with t_col3:
                st.metric("보안 연결(HTTPS)", "✅ 안전" if url.startswith("https") else "⚠️ 위험")
            with t_col4:
                text_content = soup.get_text()
                text_len = len(text_content)
                html_len = len(res.text)
                ratio = round((text_len / html_len) * 100, 1) if html_len > 0 else 0
                st.metric("콘텐츠 비중", f"{ratio}%")

            if not viewport:
                st.info("💡 **해결책:** 모바일 대응을 위해 `<meta name='viewport' content='width=device-width, initial-scale=1'>` 태그를 추가하세요.")

            st.divider()

            # --- 2. 메타 데이터 및 SNS ---
            st.header("2️⃣ 검색 및 SNS 노출 최적화")
            title_tag = soup.find('title')
            desc_tag = soup.find('meta', attrs={'name': 'description'})
            og_img_tag = soup.find('meta', attrs={'property': 'og:image'})
            
            title_text = title_tag.get_text().strip() if title_tag else "❌ 누락"
            desc_text = desc_tag.get('content').strip() if desc_tag else "❌ 누락"

            m_col1, m_col2 = st.columns([2, 1])
            with m_col1:
                st.write(f"**Title:** {title_text}")
                st.write(f"**Description:** {desc_text}")
                if not title_tag or len(title_text) < 10: 
                    st.warning("💡 **해결책:** 제목이 너무 짧거나 누락되었습니다. 30~60자 사이를 권장합니다.")
            with m_col2:
                if og_img_tag: 
                    st.image(og_img_tag['content'], caption="SNS 공유 미리보기 이미지", use_container_width=True)
                else: 
                    st.error("❌ SNS 공유용(og:image) 이미지가 없습니다.")

            st.divider()

            # --- 3. 키워드 분석 (시각화 포함) ---
            st.header("3️⃣ 콘텐츠 키워드 분석 (Top 10)")
            words = re.findall(r'[가-힣a-zA-Z]{2,}', text_content)
            common_words = Counter(words).most_common(10)
            
            if common_words:
                k_df = pd.DataFrame(common_words, columns=['키워드', '빈도수'])
                k_col1, k_col2 = st.columns([1, 1])
                with k_col1:
                    st.table(k_df)
                with k_col2:
                    st.bar_chart(k_df.set_index('키워드'))
            else:
                st.info("텍스트 데이터가 부족하여 분석할 수 없습니다.")

            st.divider()

            # --- 4. 웹 표준 및 구조 ---
            st.header("4️⃣ 웹 표준 및 문서 구조")
            ext_links = soup.find_all('a', href=True, target="_blank")
            unsafe = [l for l in ext_links if 'noopener' not in (l.get('rel') or [])]
            h1s = [h.get_text().strip() for h in soup.find_all('h1')]
            
            c_w1, c_w2 = st.columns(2)
            with c_w1:
                st.subheader("보안 취약점")
                st.write(f"**보안 위험 외부 링크:** {len(unsafe)}개")
                if unsafe: st.info("💡 **해결책:** 외부 링크에 `rel='noopener'`를 추가하여 보안을 강화하세요.")
            with c_w2:
                st.subheader("H1 태그")
                st.write(f"**H1 개수:** {len(h1s)}개")
                if len(h1s) != 1: 
                    st.error("💡 **해결책:** H1 태그는 페이지당 1개만 사용해야 검색 엔진이 주제를 정확히 파악합니다.")

            st.divider()

            # --- 5. 이미지 및 Alt 속성 (경로 최적화) ---
            st.header("5️⃣ 이미지 분석 및 Alt 속성")
            imgs = soup.find_all('img')
            img_list = []
            
            for i in imgs:
                # 1. src 우선 추출, 없으면 lazy-loading 속성들 확인
                raw_src = i.get('src') or i.get('data-src') or i.get('data-original') or i.get('lazy-src') or ""
                
                # 2. 상대 경로를 절대 경로로 변환
                full_src = urljoin(base_url, raw_src) if raw_src else "경로 없음"
                
                # 3. Base64 데이터 이미지인 경우 처리
                if full_src.startswith('data:image'):
                    display_src = "내장 이미지 데이터(Base64)"
                else:
                    display_src = full_src

                img_list.append({
                    "상태": "✅" if i.get('alt') else "❌ 누락",
                    "Alt 내용": i.get('alt', '내용 없음'),
                    "이미지 경로": display_src
                })

            if img_list:
                df = pd.DataFrame(img_list)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("페이지 내 이미지가 발견되지 않았습니다.")

        except Exception as e:
            st.error(f"진단 중 오류 발생: {str(e)}")
    else:
        st.warning("URL을 입력해 주세요.")
