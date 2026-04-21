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
st.set_page_config(page_title="Professional SEO Analyzer v1.9", layout="wide")

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

            # --- 1~4 섹션 생략 (디자인 유지) ---
            # (중간 섹션들은 기존과 동일하게 작동하므로 생략하거나 합치시면 됩니다.)

            st.divider()

            # --- 5. 이미지 분석 (Alt 인식 오류 해결 최종판) ---
            st.header("5️⃣ 이미지 분석 및 Alt 속성 (전체 리스트)")
            imgs = soup.find_all('img')
            img_data = []
            
            for i in imgs:
                # [수정 1] Alt 속성 추출 방식을 가장 엄격하게 변경
                # 속성 자체가 없는 경우와, 있지만 비어있는 경우를 확실히 구분합니다.
                alt_text = i.get('alt')
                if alt_text is not None:
                    alt_text = alt_text.strip()
                else:
                    alt_text = "" # 속성 자체가 없는 경우
                
                # [수정 2] 경로 추출 시 alt가 있는 해당 태그의 src를 최우선으로 잡음
                raw_src = i.get('src', '').strip()
                
                # 불필요한 더미 이미지 필터링
                if not raw_src or any(p in raw_src.lower() for p in ['blank', 'pixel', 'spacer', 'transparent']):
                    continue

                # 전체 경로 생성
                if raw_src.startswith('//'): 
                    full_src = "https:" + raw_src
                else: 
                    full_src = urljoin(base_url, raw_src)
                
                # 클릭 가능한 링크 생성
                clickable_path = f'<a href="{full_src}" target="_blank" style="text-decoration: none; color: #007bff; word-break: break-all;">{full_src}</a>'

                img_data.append({
                    "상태": "✅" if alt_text else "❌ 누락",
                    "Alt 내용": alt_text if alt_text else "내용 없음",
                    "이미지 경로 (클릭 가능)": clickable_path
                })

            if img_data:
                df = pd.DataFrame(img_data)
                # [수정 3] 스크롤 없이 하단으로 쭉 나열 (to_html 사용)
                # 열 너비 조절 및 중앙 정렬을 위한 스타일 추가
                table_html = df.to_html(escape=False, index=False, justify='center')
                st.write(table_html, unsafe_allow_html=True)
                st.info(f"총 {len(img_data)}개의 이미지를 발견했습니다.")
            else:
                st.info("발견된 이미지가 없습니다.")

        except Exception as e:
            st.error(f"분석 중 오류 발생: {str(e)}")
    else:
        st.warning("URL을 정확히 입력해 주세요.")
