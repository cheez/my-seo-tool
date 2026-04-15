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
st.set_page_config(page_title="Professional SEO Analyzer v1.7", layout="wide")

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
                if load_speed > 3: st.error("⚠️ 느림 (3초 이내 권장)")
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
                st.subheader("메타 태그 정보")
                st.write(f"**Title:** {title_text}")
                st.write(f"**Description:** {desc_text}")
                if not title_tag or len(title_text) < 10: 
                    st.warning("💡 제목을 30~60자 사이로 구체적으로 작성하는 것이 SEO에 유리합니다.")
            with m_col2:
                st.subheader("SNS 공유 미리보기")
                if og_img_tag: 
                    st.image(og_img_tag['content'], caption="og:image 미리보기", use_container_width=True)
                else: 
                    st.error("❌ SNS 공유용 이미지가 설정되지 않았습니다.")

            st.divider()

            # --- 3. 콘텐츠 키워드 분석 ---
            st.header("3️⃣ 콘텐츠 키워드 분석 (Top 10)")
            words = re.findall(r'[가-힣a-zA-Z]{2,}', text_content)
            common_words = Counter(words).most_common(10)
            
            if common_words:
                k_df = pd.DataFrame(common_words, columns=['키워드', '빈도수'])
                k_col1, k_col2 = st.columns([1, 1])
                with k_col1:
                    st.write("**키워드 빈도수 표**")
                    st.table(k_df)
                with k_col2:
                    st.write("**키워드 분포 차트**")
                    st.bar_chart(k_df.set_index('키워드'))
            else:
                st.info("텍스트 데이터가 부족하여 분석할 수 없습니다.")

            st.divider()

            # --- 4. 웹 표준 및 구조 점검 ---
            st.header("4️⃣ 웹 표준 및 문서 구조")
            h1s = [h.get_text().strip() for h in soup.find_all('h1')]
            ext_links = soup.find_all('a', href=True, target="_blank")
            unsafe = [l for l in ext_links if 'noopener' not in (l.get('rel') or [])]
            
            c_w1, c_w2 = st.columns(2)
            with c_w1:
                st.subheader("Heading (H1) 구조")
                st.write(f"**H1 태그 개수:** {len(h1s)}개")
                if len(h1s) != 1: 
                    st.error("💡 H1 태그는 페이지당 반드시 1개만 사용하는 것을 권장합니다.")
                for idx, h_txt in enumerate(h1s):
                    st.caption(f"H1-{idx+1}: {h_txt}")
            with c_w2:
                st.subheader("보안 및 링크")
                st.write(f"**보안 취약 링크:** {len(unsafe)}개")
                if unsafe: 
                    st.info("💡 외부 링크(target='_blank') 사용 시 보안을 위해 `rel='noopener'`를 추가하세요.")

            st.divider()

            # --- 5. 이미지 분석 (최하단 배치 및 스크롤 제거) ---
            st.header("5️⃣ 이미지 분석 및 Alt 속성 (전체 리스트)")
            imgs = soup.find_all('img')
            img_list = []
            dummy_patterns = ['blank', 'pixel', 'spacer', 'loading', 'transparent', 'common/img']

            for i in imgs:
                # 모든 속성에서 유효한 이미지 경로 추출
                candidates = []
                for attr, value in i.attrs.items():
                    if any(s in attr.lower() for s in ['src', 'orig', 'lazy']):
                        if value and isinstance(value, str) and not any(p in value.lower() for p in dummy_patterns):
                            candidates.append(value)
                
                raw_src = candidates[0] if candidates else i.get('src')
                
                if raw_src:
                    if ',' in raw_src: raw_src = raw_src.split(',')[0].split(' ')[0].strip()
                    if raw_src.startswith('//'): full_src = "https:" + raw_src
                    elif raw_src.startswith('data:image'): full_src = "내장 이미지(Base64)"
                    else: full_src = urljoin(base_url, raw_src)
                else:
                    full_src = "경로 찾을 수 없음"

                img_list.append({
                    "상태": "✅" if i.get('alt') else "❌ 누락",
                    "Alt 내용": i.get('alt', '내용 없음').strip(),
                    "이미지 경로": full_src
                })

            if img_list:
                df = pd.DataFrame(img_list)
                # 스크롤 없이 전체 노출
                st.table(df)
                st.info(f"총 {len(img_list)}개의 이미지를 발견했습니다.")
            else:
                st.info("발견된 이미지가 없습니다.")

        except Exception as e:
            st.error(f"분석 중 오류 발생: {str(e)}")
    else:
        st.warning("정확한 URL을 입력해 주세요.")
