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
st.set_page_config(page_title="Professional SEO Analyzer v1.8", layout="wide")

# 원래 제목 유지
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
                
                res = scraper.get(url, headers={'User-Agent': ua.random}, timeout=20)
                res.raise_for_status()
                
                if res.encoding == 'ISO-8859-1':
                    res.encoding = res.apparent_encoding
                
                load_speed = round((time.time() - start_time), 2)
                soup = BeautifulSoup(res.text, 'html.parser')
                parsed_url = urlparse(url)
                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                text_content = soup.get_text()

            # --- 1~4 섹션 (기존 로직 유지) ---
            st.header("1️⃣ 사이트 퍼포먼스 및 기술 점검")
            t_col1, t_col2, t_col3, t_col4 = st.columns(4)
            viewport = soup.find('meta', attrs={'name': 'viewport'})
            with t_col1: st.metric("로딩 속도", f"{load_speed}초")
            with t_col2: st.metric("모바일 최적화", "✅ 확인" if viewport else "❌ 미설정")
            with t_col3: st.metric("보안 연결(HTTPS)", "✅ 안전" if url.startswith("https") else "⚠️ 위험")
            with t_col4:
                ratio = round((len(text_content) / len(res.text)) * 100, 1) if len(res.text) > 0 else 0
                st.metric("콘텐츠 비중", f"{ratio}%")

            st.divider()
            st.header("2️⃣ 검색 및 SNS 노출 최적화")
            title_tag = soup.find('title')
            desc_tag = soup.find('meta', attrs={'name': 'description'})
            title_text = title_tag.get_text().strip() if title_tag else "❌ 누락"
            desc_text = desc_tag.get('content').strip() if desc_tag else "❌ 누락"
            st.write(f"**Title:** {title_text}")
            st.write(f"**Description:** {desc_text}")

            st.divider()
            st.header("3️⃣ 콘텐츠 키워드 분석 (Top 10)")
            words = re.findall(r'[가-힣a-zA-Z]{2,}', text_content)
            common_words = Counter(words).most_common(10)
            if common_words:
                k_df = pd.DataFrame(common_words, columns=['키워드', '빈도수'])
                st.table(k_df)

            st.divider()
            st.header("4️⃣ 웹 표준 및 문서 구조")
            h1s = [h.get_text().strip() for h in soup.find_all('h1')]
            st.write(f"H1 태그 개수: {len(h1s)}개")
            for h_txt in h1s: st.caption(f"• {h_txt}")

            st.divider()

            # --- 5. 이미지 분석 (요청사항 반영: 전체 URL 표시 + 클릭 가능 + 스크롤 제거) ---
            st.header("5️⃣ 이미지 분석 및 Alt 속성 (전체 리스트)")
            imgs = soup.find_all('img')
            img_list = []
            
            for i in imgs:
                alt_val = i.get('alt', '').strip()
                raw_src = i.get('src', '')
                
                # 불필요한 이미지 제외
                if any(p in raw_src.lower() for p in ['blank', 'pixel', 'spacer', 'transparent']):
                    continue

                if raw_src:
                    if raw_src.startswith('//'): full_src = "https:" + raw_src
                    else: full_src = urljoin(base_url, raw_src)
                    
                    # [핵심] 전체 URL을 보여주면서 클릭하면 새창으로 열리게 세팅
                    clickable_path = f'<a href="{full_src}" target="_blank" style="text-decoration: none; color: #007bff;">{full_src}</a>'
                else:
                    clickable_path = "경로 찾을 수 없음"

                img_list.append({
                    "상태": "✅" if alt_val else "❌ 누락",
                    "Alt 내용": alt_val if alt_val else "내용 없음",
                    "이미지 경로 (클릭 가능)": clickable_path
                })

            if img_list:
                df = pd.DataFrame(img_list)
                # HTML 렌더링으로 표를 쭉 나열 (스크롤 없음)
                # escape=False를 해야 <a> 태그가 실제 링크로 작동합니다.
                st.write(df.to_html(escape=False, index=False), unsafe_allow_html=True)
                st.info(f"총 {len(img_list)}개의 이미지를 발견했습니다.")
            else:
                st.info("발견된 이미지가 없습니다.")

        except Exception as e:
            st.error(f"분석 중 오류 발생: {str(e)}")
    else:
        st.warning("URL을 정확히 입력해 주세요.")
