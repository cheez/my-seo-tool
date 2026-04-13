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
st.set_page_config(page_title="Professional SEO Analyzer v1.6", layout="wide")

st.title("SEO & 이미지 정밀 분석 리포트")
st.caption("복잡한 지연 로딩 구조(바이탈뷰티 등)에서도 이미지 경로를 놓치지 않도록 로직을 강화했습니다.")
st.markdown("---")

url = st.text_input("진단할 사이트 주소 (https:// 필수)", "https://")

if st.button("종합 분석 시작"):
    if url.startswith("http"):
        try:
            with st.spinner('이미지 경로를 심층 추적 중입니다...'):
                start_time = time.time()
                ua = UserAgent()
                scraper = cloudscraper.create_scraper()
                res = scraper.get(url, headers={'User-Agent': ua.random}, timeout=20)
                res.raise_for_status()
                
                load_speed = round((time.time() - start_time), 2)
                res.encoding = res.apparent_encoding
                soup = BeautifulSoup(res.text, 'html.parser')
                
                parsed_url = urlparse(url)
                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                text_content = soup.get_text()

            # --- 1. 사이트 요약 ---
            st.header("1️⃣ 분석 요약")
            t_col1, t_col2, t_col3 = st.columns(3)
            with t_col1: st.metric("로딩 속도", f"{load_speed}초")
            with t_col2: st.metric("보안 연결", "✅ HTTPS" if url.startswith("https") else "⚠️ 위험")
            with t_col3: st.metric("H1 태그", f"{len(soup.find_all('h1'))}개")

            st.divider()

            # --- 2. 이미지 정밀 분석 (모든 잠재적 경로 추적) ---
            st.header("2️⃣ 이미지 및 Alt 속성 분석 (스크롤 없음)")
            
            img_list = []
            # 무시해야 할 더미 이미지 패턴
            dummy_patterns = ['blank', 'pixel', 'spacer', 'loading', 'transparent', 'common/img', 'dot.gif']

            all_imgs = soup.find_all('img')
            for i in all_imgs:
                # [강력한 추출 로직] 
                # 1. 모든 속성을 다 뒤져서 URL 형태를 가진 것들을 후보군으로 수집
                candidates = []
                
                # 'src' 관련 모든 속성을 검사 (data-src, original-src, src 등)
                for attr, value in i.attrs.items():
                    if any(s in attr.lower() for s in ['src', 'orig', 'lazy']):
                        if value and isinstance(value, str) and not any(p in value.lower() for p in dummy_patterns):
                            candidates.append(value)
                
                # 2. 수집된 후보 중 가장 유효한 주소 선택 (보통 첫 번째가 실제 주소)
                raw_src = candidates[0] if candidates else i.get('src')
                
                # 3. 경로 정제 및 절대 경로 변환
                if raw_src:
                    # srcset의 경우 첫 번째 주소만 취함
                    if ',' in raw_src:
                        raw_src = raw_src.split(',')[0].split(' ')[0].strip()
                        
                    if raw_src.startswith('//'): 
                        full_src = "https:" + raw_src
                    elif raw_src.startswith('data:image'): 
                        full_src = "내장 이미지(Base64)"
                    else: 
                        full_src = urljoin(base_url, raw_src)
                else:
                    full_src = "경로 찾을 수 없음"

                img_list.append({
                    "상태": "✅" if i.get('alt') else "❌ 누락",
                    "Alt 내용": i.get('alt', '내용 없음').strip(),
                    "이미지 경로": full_src
                })

            if img_list:
                df = pd.DataFrame(img_list)
                st.table(df) # 스크롤 없이 전체 데이터 출력
                st.info(f"총 {len(img_list)}개의 이미지를 분석했습니다.")
            else:
                st.info("이미지를 찾을 수 없습니다.")

            # --- 3. 나머지 분석 섹션 (기존 기능 유지) ---
            st.divider()
            st.header("3️⃣ 콘텐츠 및 구조 분석")
            k_col1, k_col2 = st.columns(2)
            
            with k_col1:
                st.subheader("키워드 TOP 10")
                words = re.findall(r'[가-힣a-zA-Z]{2,}', text_content)
                common = Counter(words).most_common(10)
                if common:
                    st.table(pd.DataFrame(common, columns=['키워드', '빈도']))
            
            with k_col2:
                st.subheader("H1 태그 목록")
                h1s = [h.get_text().strip() for h in soup.find_all('h1')]
                if h1s:
                    for h in h1s: st.write(f"- {h}")
                else:
                    st.write("발견된 H1 태그가 없습니다.")

        except Exception as e:
            st.error(f"분석 중 오류 발생: {str(e)}")
    else:
        st.warning("정확한 URL을 입력해 주세요.")
