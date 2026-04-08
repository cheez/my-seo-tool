import streamlit as st
import cloudscraper
from bs4 import BeautifulSoup
import pandas as pd

# 페이지 설정
st.set_page_config(page_title="SEO Health Checker", layout="wide")

st.title("🔍 SEO 통합 검증 대시보드 (보안 우회형)")
st.subheader("보안이 강한 대기업 사이트도 분석을 시도합니다.")

url = st.text_input("검사할 사이트 주소를 입력하세요 (https:// 필수)", "https://")

if st.button("분석 시작"):
    if url.startswith("http"):
        try:
            # 보완: cloudscraper를 사용하여 보안 장벽(Cloudflare 등)을 우회합니다.
            scraper = cloudscraper.create_scraper()
            
            # 실제 브라우저처럼 보이게 만듭니다.
            res = scraper.get(url, timeout=20)
            res.raise_for_status()
            
            # 한글 깨짐 방지
            res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, 'html.parser')
            
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### 📝 기본 태그 점검")
                title = soup.find('title')
                desc = soup.find('meta', attrs={'name': 'description'})
                
                st.info(f"**Title:** {title.get_text() if title else '❌ 누락'}")
                st.info(f"**Description:** {desc.get('content') if desc and desc.get('content') else '❌ 누락'}")

            with col2:
                st.markdown("### 🏗️ 구조(Heading) 점검")
                h1_tags = [h.get_text().strip() for h in soup.find_all('h1')]
                if not h1_tags:
                    st.error("❌ H1 태그가 없습니다.")
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
                img_data.append({
                    "이미지 주소": src, 
                    "Alt 내용": alt if alt else "(비어있음)", 
                    "상태": status
                })
            
            if img_data:
                df = pd.DataFrame(img_data)
                st.dataframe(df, use_container_width=True)
                missing_count = len(df[df['상태'] == "❌ 누락"])
                st.warning(f"전체 이미지 {len(images)}개 중 **{missing_count}개**의 Alt 값이 비어 있습니다.")
            else:
                st.info("이 페이지에서 분석 가능한 이미지를 찾지 못했습니다.")

        except Exception as e:
            st.error(f"⚠️ 분석 중 오류 발생: {str(e)}")
            st.write("해당 사이트가 고도의 봇 방지 시스템을 사용 중일 수 있습니다.")
    else:
        st.warning("올바른 URL 형식을 입력해 주세요.")
