바이탈뷰티와 같이 자바스크립트로 이미지를 지연 로딩(Lazy Loading)하는 사이트에서도 경로를 최대한 찾아낼 수 있도록 이미지 추출 로직을 대폭 강화하여 업데이트했습니다.

이번 업데이트의 핵심 변경 사항
다중 속성 탐색: 단순히 src만 보는 것이 아니라 data-src, data-original, data-lazy-src, data-srcset 등 실제 이미지 주소가 숨겨져 있을 법한 모든 속성을 순차적으로 검사합니다.

더미 이미지 필터링: 페이지 로딩 중에 임시로 보여주는 투명 이미지(blank.gif, pixel.png 등)는 무시하고 실제 콘텐츠 이미지를 찾습니다.

자바스크립트 변수 패턴 대응: 이미지 주소에 //로 시작하는 프로토콜 상대 경로가 있을 경우 https:를 자동으로 붙여주는 처리를 추가했습니다.

업데이트된 코드
Python
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
st.caption("On-Page SEO부터 키워드 밀도, 로딩 속도까지 한 번에 진단합니다. (이미지 경로 탐색 강화 버전)")
st.markdown("---")

url = st.text_input("진단할 사이트 주소 (https:// 필수)", "https://")

if st.button("종합 분석 시작"):
    if url.startswith("http"):
        try:
            with st.spinner('사이트 데이터를 심층 분석 중입니다...'):
                start_time = time.time()
                
                ua = UserAgent()
                scraper = cloudscraper.create_scraper()
                # 바이탈뷰티 같은 대형 사이트의 봇 차단을 방지하기 위한 설정
                res = scraper.get(url, headers={'User-Agent': ua.random}, timeout=20)
                res.raise_for_status()
                
                end_time = time.time()
                load_speed = round((end_time - start_time), 2)
                
                res.encoding = res.apparent_encoding
                soup = BeautifulSoup(res.text, 'html.parser')
                
                # 상대 경로 해결을 위한 베이스 URL
                parsed_url = urlparse(url)
                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

            # --- 1. 퍼포먼스 및 기술 점검 ---
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
                text_content = soup.get_text()
                text_len = len(text_content)
                html_len = len(res.text)
                ratio = round((text_len / html_len) * 100, 1) if html_len > 0 else 0
                st.metric("콘텐츠 비중", f"{ratio}%")

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
            with m_col2:
                if og_img_tag: 
                    st.image(og_img_tag['content'], caption="SNS 공유 이미지", use_container_width=True)
                else: 
                    st.error("❌ SNS 공유 이미지(og:image) 미설정")

            st.divider()

            # --- 3. 키워드 분석 ---
            st.header("3️⃣ 콘텐츠 키워드 분석 (Top 10)")
            words = re.findall(r'[가-힣a-zA-Z]{2,}', text_content)
            common_words = Counter(words).most_common(10)
            
            if common_words:
                k_df = pd.DataFrame(common_words, columns=['키워드', '빈도수'])
                k_col1, k_col2 = st.columns([1, 1])
                with k_col1: st.table(k_df)
                with k_col2: st.bar_chart(k_df.set_index('키워드'))

            st.divider()

            # --- 4. 이미지 및 Alt 속성 (정밀 탐색 업데이트) ---
            st.header("4️⃣ 이미지 분석 및 Alt 속성")
            imgs = soup.find_all('img')
            img_list = []
            
            # 필터링할 더미 이미지 키워드
            dummy_keywords = ['blank', 'pixel', 'spacer', 'loading', 'data:image']

            for i in imgs:
                # 1. 실제 경로가 숨어있을 만한 모든 속성을 순차적으로 검사
                # src, data-src, data-original, data-lazy-src, data-srcset 순
                possible_attrs = ['data-src', 'data-original', 'data-lazy-src', 'src', 'data-srcset']
                raw_src = None
                
                for attr in possible_attrs:
                    val = i.get(attr)
                    if val:
                        # 더미 이미지인지 확인 (단, data:image는 경로 없음 대신 '내장 데이터'로 표시하기 위해 일단 통과)
                        if any(dk in val.lower() for dk in dummy_keywords if dk != 'data:image'):
                            continue
                        raw_src = val
                        break
                
                # 2. 경로 정제
                if raw_src:
                    # //로 시작하는 프로토콜 상대 경로 처리
                    if raw_src.startswith('//'):
                        full_src = "https:" + raw_src
                    # data:image로 시작하는 내장 데이터 처리
                    elif raw_src.startswith('data:image'):
                        full_src = "내장 이미지 데이터(Base64)"
                    # 그 외 상대 경로를 절대 경로로 변환
                    else:
                        full_src = urljoin(base_url, raw_src)
                else:
                    full_src = "경로 찾을 수 없음"

                img_list.append({
                    "상태": "✅" if i.get('alt') else "❌ 누락",
                    "Alt 내용": i.get('alt', '내용 없음'),
                    "이미지 경로": full_src
                })

            if img_list:
                df = pd.DataFrame(img_list)
                st.dataframe(df, use_container_width=True)
                
                # 요약 정보
                total_imgs = len(img_list)
                missing_alt = len([img for img in img_list if img['상태'] == "❌ 누락"])
                st.info(f"총 {total_imgs}개의 이미지를 발견했습니다. (Alt 누락: {missing_alt}개)")
            else:
                st.info("이미지를 찾을 수 없습니다.")

        except Exception as e:
            st.error(f"진단 중 오류 발생: {str(e)}")
    else:
        st.warning("정확한 URL을 입력해 주세요.")
