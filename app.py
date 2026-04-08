import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

# 페이지 설정
st.set_page_config(page_title="SEO Health Checker", layout="wide")

st.title("🔍 SEO 통합 검증 대시보드")
st.subheader("URL을 입력하면 실시간으로 SEO 상태를 점검합니다.")

url = st.text_input("검사할 사이트 주소를 입력하세요 (https:// 필수)", "https://")

if st.button("분석 시작"):
    if url.startswith("http"):
        try:
            res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            res.raise_for_status()
            soup = BeautifulSoup(res.text, 'html.parser')
            
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### 📝 기본 태그 점검")
                title = soup.find('title')
                desc = soup.find('meta', attrs={'name': 'description'})
                st.info(f"**Title:** {title.text if title else '❌ 누락'}")
                st.info(f"**Description:** {desc['content'] if desc else '❌ 누락'}")

            with col2:
                st.markdown("### 🏗️ 구조(Heading) 점검")
                h1_tags = [h.text.strip() for h in soup.find_all('h1')]
                if not h1_tags:
                    st.error("❌ H1 태그가 없습니다. (검색 최적화에 치명적)")
                else:
                    st.success(f"✅ H1 태그 발견: {h1_tags[0]}")

            st.divider()

            st.markdown("### 🖼️ 이미지 Alt 속성 리스트")
            img_data = []
            images = soup.find_all('img')
            
            for img in images:
                src = img.get('src', 'N/A')
                alt = img.get('alt', None)
                status = "✅ 정상" if alt is not None and alt.strip() != "" else "❌ 누락"
                img_data.append({"이미지 주소": src, "Alt 내용": alt if alt else "(비어있음)", "상태": status})
            
            df = pd.DataFrame(img_data)
            st.dataframe(df, use_container_width=True)

            missing_count = len(df[df['상태'] == "❌ 누락"])
            st.warning(f"전체 이미지 {len(images)}개 중 **{missing_count}개**의 Alt 값이 비어 있습니다.")

        except Exception as e:
            st.error(f"분석 중 오류가 발생했습니다: {e}")
    else:
        st.warning("올바른 URL 형식을 입력해 주세요.")