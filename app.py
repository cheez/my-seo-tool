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
            # 보완: 실제 브라우저와 거의 동일한 헤더 정보를 구성합니다.
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                'Referer': 'https://www.google.com/',
                'Connection': 'keep-alive'
            }
            
            # 타임아웃을 넉넉히 주어 서버 응답을 기다립니다.
            res = requests.get(url, headers=headers, timeout=20)
            res.raise_for_status()
            
            # 한글 깨짐 방지를 위해 인코딩 설정
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
                # alt 속성이 아예 없거나, 빈 문자열인 경우 체크
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
                st.info("이 페이지에는 분석할 수 있는 이미지가 없습니다.")

        except requests.exceptions.HTTPError as errh:
            st.error(f"❌ HTTP 오류: {errh}")
            st.write("사이트에서 차단했거나 페이지가 존재하지 않습니다.")
        except Exception as e:
            st.error(f"⚠️ 기타 오류 발생: {str(e)}")
    else:
        st.warning("올바른 URL 형식을 입력해 주세요 (https:// 포함)")
