import streamlit as st
import cloudscraper
from bs4 import BeautifulSoup
import pandas as pd

# 페이지 설정
st.set_page_config(page_title="Professional SEO Checker", layout="wide")

st.title("🚀 전문 SEO 분석 대시보드 v2.0")
st.info("URL을 입력하면 핵심 SEO 요소 10가지를 즉시 점검합니다.")

url = st.text_input("분석할 사이트 주소 (https:// 포함)", "https://")

if st.button("상세 분석 시작"):
    if url.startswith("http"):
        try:
            scraper = cloudscraper.create_scraper()
            res = scraper.get(url, timeout=20)
            res.raise_for_status()
            res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # --- 1. 헤드라인 영역 (Title, Meta, Canonical) ---
            st.markdown("### 📋 메타 데이터 분석")
            c1, c2, c3 = st.columns(3)
            
            title_tag = soup.find('title')
            desc_tag = soup.find('meta', attrs={'name': 'description'})
            canonical_tag = soup.find('link', attrs={'rel': 'canonical'})
            
            with c1:
                st.metric("Title 존재 여부", "✅ 있음" if title_tag else "❌ 누락")
                if title_tag: st.caption(f"내용: {title_tag.text}")
            with c2:
                st.metric("Description 존재", "✅ 있음" if desc_tag else "❌ 누락")
                if desc_tag: st.caption(f"내용: {desc_tag.get('content')[:50]}...")
            with c3:
                st.metric("Canonical 설정", "✅ 설정됨" if canonical_tag else "❌ 누락")

            st.divider()

            # --- 2. SNS 공유 점검 (Open Graph) ---
            st.markdown("### 📱 SNS 공유 설정 (Open Graph)")
            og_title = soup.find('meta', attrs={'property': 'og:title'})
            og_img = soup.find('meta', attrs={'property': 'og:image'})
            
            col_og1, col_og2 = st.columns(2)
            with col_og1:
                st.write(f"**OG 제목:** {og_title['content'] if og_title else '❌ 없음'}")
            with col_og2:
                if og_img:
                    st.image(og_img['content'], caption="공유 시 노출될 이미지", width=200)
                else:
                    st.write("**OG 이미지:** ❌ 없음")

            st.divider()

            # --- 3. 태그 위계 및 이미지 점검 ---
            st.markdown("### 🏗️ 구조 및 이미지 분석")
            tab1, tab2 = st.tabs(["Heading 구조", "이미지 Alt 속성"])
            
            with tab1:
                for i in range(1, 4):
                    tags = soup.find_all(f'h{i}')
                    st.write(f"**H{i} 태그:** {len(tags)}개 발견")
                    for t in tags[:3]: # 상위 3개만 미리보기
                        st.caption(f"- {t.get_text().strip()}")
            
            with tab2:
                img_list = []
                for img in soup.find_all('img'):
                    src = img.get('src', 'N/A')
                    alt = img.get('alt', None)
                    status = "✅ 정상" if alt and alt.strip() else "❌ 누락"
                    img_list.append({"주소": src, "Alt 내용": alt, "상태": status})
                
                if img_list:
                    img_df = pd.DataFrame(img_list)
                    st.dataframe(img_df, use_container_width=True)
                else:
                    st.write("이미지가 없는 페이지입니다.")

        except Exception as e:
            st.error(f"분석 중 오류 발생: {str(e)}")
    else:
        st.warning("형식에 맞는 URL을 입력해 주세요.")
