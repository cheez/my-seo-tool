import streamlit as st
import cloudscraper
from bs4 import BeautifulSoup
import pandas as pd
from fake_useragent import UserAgent
from urllib.parse import urlparse
import time
import re
from collections import Counter

# 페이지 설정
st.set_page_config(page_title="Professional SEO Analyzer", layout="wide")

st.title("🚀 전문 SEO & 키워드 분석 리포트")
st.caption("On-Page SEO부터 키워드 밀도, 로딩 속도까지 한 번에 진단합니다.")
st.markdown("---")

url = st.text_input("진단할 사이트 주소 (https:// 필수)", "https://")

if st.button("종합 분석 시작"):
    if url.startswith("http"):
        try:
            start_time = time.time() # 속도 측정 시작
            
            ua = UserAgent()
            scraper = cloudscraper.create_scraper()
            res = scraper.get(url, headers={'User-Agent': ua.random}, timeout=20)
            res.raise_for_status()
            
            end_time = time.time() # 속도 측정 종료
            load_speed = round((end_time - start_time), 2)
            
            res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # --- 1. 퍼포먼스 및 기술 점검 ---
            st.header("1️⃣ 사이트 퍼포먼스 및 기술 점검")
            t_col1, t_col2, t_col3, t_col4 = st.columns(4)
            
            # 모바일 뷰포트 체크
            viewport = soup.find('meta', attrs={'name': 'viewport'})
            # Robots.txt 체크 (도메인 추출)
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            with t_col1:
                st.metric("로딩 속도", f"{load_speed}초")
                if load_speed > 3: st.error("⚠️ 느림 (3초 이내 권장)")
                else: st.success("✅ 빠름")
            with t_col2:
                st.metric("모바일 최적화", "✅ 확인" if viewport else "❌ 미설정")
            with t_col3:
                st.metric("보안 연결(HTTPS)", "✅ 안전" if url.startswith("https") else "⚠️ 위험")
            with t_col4:
                text_len = len(soup.get_text())
                html_len = len(res.text)
                ratio = round((text_len / html_len) * 100, 1) if html_len > 0 else 0
                st.metric("콘텐츠 비중", f"{ratio}%")

            if not viewport:
                st.info("💡 **해결책:** 모바일 대응을 위해 `<meta name='viewport' content='width=device-width, initial-scale=1'>` 태그를 추가하세요.")

            st.divider()

            # --- 2. 메타 데이터 및 SNS ---
            st.header("2️⃣ 검색 및 SNS 노출 최적화")
            title = soup.find('title')
            desc = soup.find('meta', attrs={'name': 'description'})
            og_img = soup.find('meta', attrs={'property': 'og:image'})
            
            m_col1, m_col2 = st.columns([2, 1])
            with m_col1:
                st.write(f"**Title:** {title.text if title else '❌ 누락'}")
                st.write(f"**Description:** {desc.get('content') if desc else '❌ 누락'}")
                if not title or len(title.text) < 10: st.warning("💡 **해결책:** 제목을 30~60자 사이로 구체적으로 작성하세요.")
            with m_col2:
                if og_img: st.image(og_img['content'], caption="공유 이미지", use_container_width=True)
                else: st.error("❌ SNS 공유 이미지가 설정되지 않았습니다.")

            st.divider()

            # --- 3. 키워드 밀도 분석 (NEW!) ---
            st.header("3️⃣ 콘텐츠 키워드 분석 (Top 10)")
            # 한글, 영문 단어만 추출 (2글자 이상)
            words = re.findall(r'[가-힣a-zA-Z]{2,}', soup.get_text())
            common_words = Counter(words).most_common(10)
            
            if common_words:
                k_df = pd.DataFrame(common_words, columns=['키워드', '빈도수'])
                st.table(k_df.T) # 가로로 보기 편하게 출력
                st.caption("💡 **팁:** 상위 키워드들이 실제 판매 상품이나 서비스와 관련이 있는지 확인하세요.")
            else:
                st.info("분석할 텍스트 데이터가 부족합니다.")

            st.divider()

            # --- 4. 웹 표준 및 구조 ---
            st.header("4️⃣ 웹 표준 및 문서 구조")
            # 외부 링크 보안
            ext_links = soup.find_all('a', href=True, target="_blank")
            unsafe = [l for l in ext_links if 'noopener' not in (l.get('rel') or [])]
            # Heading 구조
            h1s = [h.get_text().strip() for h in soup.find_all('h1')]
            
            c_w1, c_w2 = st.columns(2)
            with c_w1:
                st.subheader("보안 및 성능")
                st.write(f"**보안 취약 링크:** {len(unsafe)}개")
                if unsafe: st.info("💡 **해결책:** 외부 링크에 `rel='noopener'` 속성을 추가하세요.")
            with c_w2:
                st.subheader("H1 태그 구조")
                st.write(f"**H1 개수:** {len(h1s)}개")
                if len(h1s) != 1: st.error("💡 **해결책:** H1은 반드시 한 페이지에 1개만 사용하세요.")

            st.divider()

            # --- 5. 이미지 리스트 ---
            st.header("5️⃣ 이미지 Alt 속성 리스트")
            imgs = soup.find_all('img')
            img_list = [{"상태": "✅" if i.get('alt') else "❌ 누락", "Alt 내용": i.get('alt'), "경로": i.get('src')} for i in imgs]
            if img_list:
                df = pd.DataFrame(img_list)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("이미지가 없습니다.")

        except Exception as e:
            st.error(f"진단 중 오류 발생: {str(e)}")
    else:
        st.warning("URL을 입력해 주세요.")
