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
st.set_page_config(page_title="Professional SEO Analyzer v1.5", layout="wide")

st.title("SEO & 이미지 정밀 분석 리포트")
st.caption("On-Page SEO부터 지연 로딩 이미지(data-src) 경로 분석까지 한 번에 진단합니다.")
st.markdown("---")

url = st.text_input("진단할 사이트 주소 (https:// 필수)", "https://")

if st.button("종합 분석 시작"):
    if url.startswith("http"):
        try:
            with st.spinner('사이트 데이터를 정밀 분석 중입니다...'):
                start_time = time.time()
                ua = UserAgent()
                scraper = cloudscraper.create_scraper()
                
                # 타임아웃 및 랜덤 유저 에이전트 적용
                res = scraper.get(url, headers={'User-Agent': ua.random}, timeout=20)
                res.raise_for_status()
                
                load_speed = round((time.time() - start_time), 2)
                res.encoding = res.apparent_encoding
                soup = BeautifulSoup(res.text, 'html.parser')
                
                parsed_url = urlparse(url)
                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                text_content = soup.get_text()

            # --- 1. 사이트 퍼포먼스 및 기술 점검 ---
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

            # --- 2. 검색 및 SNS 노출 최적화 ---
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
                    st.warning("💡 제목을 구체적으로 작성하여 클릭률을 높이세요.")
            with m_col2:
                if og_img_tag: 
                    st.image(og_img_tag['content'], caption="SNS 공유 미리보기", use_container_width=True)
                else: 
                    st.error("❌ og:image가 설정되지 않았습니다.")

            st.divider()

            # --- 3. 콘텐츠 키워드 분석 ---
            st.header("3️⃣ 콘텐츠 키워드 분석 (Top 10)")
            words = re.findall(r'[가-힣a-zA-Z]{2,}', text_content)
            common_words = Counter(words).most_common(10)
            
            if common_words:
                k_df = pd.DataFrame(common_words, columns=['키워드', '빈도수'])
                k_col1, k_col2 = st.columns([1, 1])
                with k_col1: st.table(k_df)
                with k_col2: st.bar_chart(k_df.set_index('키워드'))

            st.divider()

            # --- 4. 웹 표준 및 구조 점검 ---
            st.header("4️⃣ 웹 표준 및 문서 구조")
            h1s = [h.get_text().strip() for h in soup.find_all('h1')]
            ext_links = soup.find_all('a', href=True, target="_blank")
            unsafe = [l for l in ext_links if 'noopener' not in (l.get('rel') or [])]
            
            c_w1, c_w2 = st.columns(2)
            with c_w1:
                st.subheader("Heading (H1)")
                st.write(f"**H1 개수:** {len(h1s)}개")
                if len(h1s) == 0: st.error("❌ H1 태그가 없습니다.")
                elif len(h1s) > 1: st.warning("⚠️ H1은 하나만 권장됩니다.")
                for h in h1s: st.caption(f"내용: {h}")
            with c_w2:
                st.subheader("보안 취약점")
                st.write(f"**위험한 외부 링크:** {len(unsafe)}개")
                if unsafe: st.info("💡 target='_blank' 사용 시 rel='noopener'를 권장합니다.")

            st.divider()

            # --- 5. 이미지 분석 (경로 정밀 추출 및 스크롤 제거) ---
            st.header("5️⃣ 이미지 분석 및 Alt 속성 (전체 리스트)")
            imgs = soup.find_all('img')
            img_list = []
            dummy_keywords = ['blank', 'pixel', 'spacer', 'loading', 'transparent']

            for i in imgs:
                # [중요] 경로 추출 우선순위 조정 (data-src 등 지연 로딩 속성 우선 탐색)
                attr_candidates = [
                    'data-src', 'data-original', 'original-src', 
                    'data-lazy-src', 'data-srcset', 'src', 'srcset'
                ]
                
                raw_src = None
                for attr in attr_candidates:
                    val = i.get(attr)
                    if val and not any(dk in val.lower() for dk in dummy_keywords):
                        raw_src = val
                        break
                
                # 경로 가공
                if raw_src:
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
                st.table(df) # 스크롤 없이 전체 데이터를 아래로 쭉 출력
                st.info(f"총 {len(img_list)}개의 이미지를 분석했습니다.")
            else:
                st.info("페이지에서 이미지를 찾을 수 없습니다.")

        except Exception as e:
            st.error(f"분석 중 오류 발생: {str(e)}")
    else:
        st.warning("정확한 URL을 입력해 주세요.")
