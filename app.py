import streamlit as st
import cloudscraper
from bs4 import BeautifulSoup
import pandas as pd
from fake_useragent import UserAgent

# 페이지 설정
st.set_page_config(page_title="Comprehensive SEO Report", layout="wide")

st.title("📑 SEO 통합 분석 리포트")
st.info("입력하신 URL의 모든 SEO 요소를 한 페이지로 상세히 나열합니다.")

url = st.text_input("분석할 사이트 주소 (https:// 포함)", "https://")

if st.button("전체 리포트 생성"):
    if url.startswith("http"):
        try:
            ua = UserAgent()
            scraper = cloudscraper.create_scraper()
            res = scraper.get(url, headers={'User-Agent': ua.random}, timeout=20)
            res.raise_for_status()
            res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # --- 섹션 1: 핵심 메타 데이터 ---
            st.header("1️⃣ 핵심 메타 데이터 (Metadata)")
            c1, c2, c3 = st.columns(3)
            
            title_tag = soup.find('title')
            desc_tag = soup.find('meta', attrs={'name': 'description'})
            canonical_tag = soup.find('link', attrs={'rel': 'canonical'})
            
            with c1:
                st.subheader("Title")
                st.write(title_tag.text if title_tag else "❌ 누락됨")
            with c2:
                st.subheader("Description")
                st.write(desc_tag.get('content') if desc_tag else "❌ 누락됨")
            with c3:
                st.subheader("Canonical URL")
                st.write(canonical_tag.get('href') if canonical_tag else "❌ 누락됨")
            
            st.divider()

            # --- 섹션 2: SNS 공유 설정 (Open Graph) ---
            st.header("2️⃣ SNS 공유 설정 (Open Graph)")
            og_title = soup.find('meta', attrs={'property': 'og:title'})
            og_img = soup.find('meta', attrs={'property': 'og:image'})
            og_desc = soup.find('meta', attrs={'property': 'og:description'})
            
            og_col1, og_col2 = st.columns([2, 1])
            with og_col1:
                st.write(f"**OG 제목:** {og_title['content'] if og_title else '❌ 누락'}")
                st.write(f"**OG 설명:** {og_desc['content'] if og_desc else '❌ 누락'}")
            with og_col2:
                if og_img:
                    st.image(og_img['content'], caption="공유 미리보기 이미지", use_container_width=True)
                else:
                    st.warning("OG 이미지가 없습니다.")
            
            st.divider()

            # --- 섹션 3: 문서 구조 (Heading 위계) ---
            st.header("3️⃣ 문서 구조 (Heading Tags)")
            h_col1, h_col2, h_col3 = st.columns(3)
            
            # H1~H3 태그 추출
            h1s = [h.get_text().strip() for h in soup.find_all('h1')]
            h2s = [h.get_text().strip() for h in soup.find_all('h2')]
            h3s = [h.get_text().strip() for h in soup.find_all('h3')]

            with h_col1:
                st.subheader(f"H1 ({len(h1s)}개)")
                if h1s:
                    for h in h1s: st.write(f"- {h}")
                else: st.error("H1 태그가 없습니다!")
                
            with h_col2:
                st.subheader(f"H2 ({len(h2s)}개)")
                for h in h2s[:10]: st.write(f"- {h}") # 너무 많을까봐 10개만
                if len(h2s) > 10: st.caption(f"...외 {len(h2s)-10}개 더 있음")
                
            with h_col3:
                st.subheader(f"H3 ({len(h3s)}개)")
                for h in h3s[:10]: st.write(f"- {h}")
                if len(h3s) > 10: st.caption(f"...외 {len(h3s)-10}개 더 있음")

            st.divider()

            # --- 섹션 4: 이미지 분석 (Alt 속성 전수 조사) ---
            st.header("4️⃣ 이미지 Alt 속성 분석")
            img_list = []
            all_images = soup.find_all('img')
            
            for img in all_images:
                src = img.get('src', 'N/A')
                alt = img.get('alt', None)
                # alt가 None이거나 공백만 있는 경우 ❌ 누락
                is_missing = alt is None or alt.strip() == ""
                status = "❌ 누락" if is_missing else "✅ 정상"
                img_list.append({
                    "상태": status,
                    "Alt 내용": alt if alt else "(비어있음)",
                    "이미지 경로": src
                })
            
            if img_list:
                df = pd.DataFrame(img_list)
                # 상태가 누락인 것을 상단으로 정렬하여 보여줌
                df = df.sort_values(by="상태", ascending=False)
                
                missing_count = len(df[df['상태'] == "❌ 누락"])
                st.warning(f"총 {len(all_images)}개의 이미지 중 **{missing_count}개**의 Alt 속성이 누락되었습니다.")
                st.dataframe(df, use_container_width=True)
            else:
                st.info("이 페이지에는 분석할 이미지가 없습니다.")

        except Exception as e:
            st.error(f"분석 중 오류 발생: {str(e)}")
    else:
        st.warning("형식에 맞는 URL을 입력해 주세요.")
