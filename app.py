import streamlit as st
import cloudscraper
from bs4 import BeautifulSoup
import pandas as pd
from fake_useragent import UserAgent
from urllib.parse import urlparse, urljoin
import time
import re
from collections import Counter

# [1] 페이지 설정 및 제목 (원본 유지)
st.set_page_config(page_title="Professional SEO Analyzer v2.1", layout="wide")

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

            # --- 1️⃣ 사이트 퍼포먼스 ---
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

            # --- 2️⃣ 검색 및 SNS 노출 ---
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
                if og_img_tag: st.image(og_img_tag['content'], use_container_width=True)

            st.divider()

            # --- 3️⃣ 콘텐츠 키워드 분석 ---
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
            st.write(f"H1 태그 개수: {len(h1s)}개")
            for h_txt in h1s: st.caption(f"• {h_txt}")

            st.divider()

            # --- 5️⃣ 이미지 분석 (Alt 완벽 해결 및 스크롤 제거) ---
            st.header("5️⃣ 이미지 분석 및 Alt 속성 (전체 리스트)")
            imgs = soup.find_all('img')
            img_data = []

            alt_ok = 0
            alt_empty = 0
            alt_missing = 0

            for i in imgs:
                has_alt_attr = i.has_attr('alt')
                alt_text = i.get('alt', '').strip()
                raw_src = (
                    i.get('src', '').strip() or
                    i.get('data-src', '').strip() or
                    i.get('data-lazy-src', '').strip() or
                    i.get('data-original', '').strip()
                )
                
                # ▼ 디버그 추가 (확인 후 삭제)
                st.write(f"src={raw_src[:60]} | has_alt={has_alt_attr} | alt='{alt_text}'")
                
                if not raw_src or any(p in raw_src.lower() for p in ['blank', 'pixel', 'spacer']):        
                    continue

                full_src = urljoin(base_url, raw_src) if not raw_src.startswith('//') else "https:" + raw_src
                clickable_path = f'<a href="{full_src}" target="_blank" style="text-decoration: none; color: #007bff; word-break: break-all;">{full_src}</a>'

                # 상태를 3단계로 구분
                if alt_text:
                    status = "✅ 있음"
                    alt_ok += 1
                elif has_alt_attr:
                    status = "⚠️ 빈 alt"   # alt=""인 경우 (장식 이미지로 의도된 경우일 수 있음)
                    alt_empty += 1
                else:
                    status = "❌ 누락"      # alt 속성 자체가 없는 경우
                    alt_missing += 1

                img_data.append({
                    "상태": status,
                    "Alt 내용": alt_text if alt_text else ("(장식 이미지 처리)" if has_alt_attr else "없음"),
                    "이미지 경로 (클릭 가능)": clickable_path
                })

            if img_data:
                # 요약 지표
                total = len(img_data)
                s_col1, s_col2, s_col3, s_col4 = st.columns(4)
                with s_col1: st.metric("전체 이미지", f"{total}개")
                with s_col2: st.metric("✅ Alt 있음", f"{alt_ok}개")
                with s_col3: st.metric("⚠️ 빈 alt", f"{alt_empty}개")
                with s_col4: st.metric("❌ Alt 누락", f"{alt_missing}개")

                st.caption("⚠️ 빈 alt: alt 속성은 존재하지만 내용이 없음 (장식 이미지일 경우 정상, 의미 있는 이미지라면 수정 필요)")

                # HTML 렌더링으로 스크롤 없이 전체 출력
                st.write(pd.DataFrame(img_data).to_html(escape=False, index=False), unsafe_allow_html=True)
            else:
                st.info("발견된 이미지가 없습니다.")

        except Exception as e:
            st.error(f"오류 발생: {str(e)}")
