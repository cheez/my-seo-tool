import streamlit as st
import cloudscraper
from bs4 import BeautifulSoup
import pandas as pd
from fake_useragent import UserAgent
from urllib.parse import urlparse

# 페이지 설정
st.set_page_config(page_title="SEO & Best Practices Full Report", layout="wide")

st.title("📑 SEO & 웹 표준 종합 진단 리포트(김상희 개인의것.)")
st.caption("모든 진단 항목과 해결책을 한 페이지에 나열합니다.")
st.markdown("---")

url = st.text_input("진단할 사이트 주소 (https:// 필수)", "https://")

if st.button("전체 리포트 생성"):
    if url.startswith("http"):
        try:
            ua = UserAgent()
            scraper = cloudscraper.create_scraper()
            res = scraper.get(url, headers={'User-Agent': ua.random}, timeout=20)
            res.raise_for_status()
            res.encoding = res.apparent_encoding
            html_content = res.text
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # --- 1. 기술적 접근성 ---
            st.header("1️⃣ 기술적 접근성 (Technical)")
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            t_col1, t_col2, t_col3 = st.columns(3)
            try:
                rb_res = scraper.get(f"{base_url}/robots.txt", timeout=5)
                has_robots = rb_res.status_code == 200
            except: has_robots = False
                
            with t_col1:
                st.metric("보안 연결(HTTPS)", "✅ 안전" if url.startswith("https") else "⚠️ 위험")
            with t_col2:
                st.metric("Robots.txt", "✅ 발견" if has_robots else "❌ 미발견")
            with t_col3:
                text_len = len(soup.get_text())
                html_len = len(html_content)
                ratio = round((text_len / html_len) * 100, 1) if html_len > 0 else 0
                st.metric("콘텐츠 비중", f"{ratio}%")

            if not url.startswith("https"):
                st.warning("💡 **해결책:** 보안 강화를 위해 SSL 인증서를 설치하고 https로 전환하세요.")
            if not has_robots:
                st.warning("💡 **해결책:** 사이트 루트 경로에 `robots.txt` 파일을 생성하여 검색 로봇의 접근을 허용하세요.")
            
            st.divider()

            # --- 2. 메타 데이터 ---
            st.header("2️⃣ 메타 데이터 및 SNS 설정")
            title = soup.find('title')
            desc = soup.find('meta', attrs={'name': 'description'})
            og_img = soup.find('meta', attrs={'property': 'og:image'})
            
            m_col1, m_col2 = st.columns([2, 1])
            with m_col1:
                st.subheader("검색 엔진 정보")
                st.write(f"**Title:** {title.text if title else '❌ 누락'}")
                st.write(f"**Description:** {desc.get('content') if desc else '❌ 누락'}")
                
                if not title: st.error("💡 **해결책:** `<title>` 태그를 추가해 페이지의 제목을 명시하세요.")
                if not desc: st.error("💡 **해결책:** `<meta name='description'>` 태그를 추가해 검색 결과 요약문을 작성하세요.")
                
            with m_col2:
                st.subheader("공유 이미지(OG)")
                if og_img:
                    st.image(og_img['content'], caption="SNS 공유 시 노출 이미지", use_container_width=True)
                else:
                    st.error("❌ 공유 이미지가 없습니다.")
                    st.caption("💡 **해결책:** `og:image` 메타 태그를 추가해 링크 공유 시 이미지가 뜨게 하세요.")

            st.divider()

            # --- 3. 웹 표준 권장사항 ---
            st.header("3️⃣ 웹 표준 권장사항 (Best Practices)")
            
            # 외부 링크 보안
            external_links = soup.find_all('a', href=True, target="_blank")
            unsafe_links = [l for l in external_links if 'noopener' not in (l.get('rel') or [])]
            
            # 이미지 규격
            imgs = soup.find_all('img')
            no_size_imgs = [i for i in imgs if not (i.get('width') and i.get('height'))]
            
            c_b1, c_b2 = st.columns(2)
            with c_b1:
                st.subheader("🔗 외부 링크 보안")
                if unsafe_links:
                    st.error(f"⚠️ 보안 취약점 {len(unsafe_links)}개 발견")
                    st.info("💡 **해결책:** 모든 `target='_blank'` 링크에 `rel='noopener'` 속성을 추가하여 보안을 강화하세요.")
                else:
                    st.success("✅ 모든 외부 링크가 안전합니다.")
            
            with c_b2:
                st.subheader("🖼️ 이미지 레이아웃")
                if no_size_imgs:
                    st.warning(f"⚠️ 크기 미지정 이미지 {len(no_size_imgs)}개")
                    st.info("💡 **해결책:** `<img>` 태그에 `width`와 `height` 값을 명시하여 로딩 시 화면 흔들림을 방지하세요.")
                else:
                    st.success("✅ 모든 이미지 크기가 지정되었습니다.")

            st.divider()

            # --- 4. 문서 구조 분석 ---
            st.header("4️⃣ 문서 구조 (Heading 위계)")
            h1s = [h.get_text().strip() for h in soup.find_all('h1')]
            h2s = [h.get_text().strip() for h in soup.find_all('h2')]
            
            h_c1, h_c2 = st.columns(2)
            with h_c1:
                st.subheader(f"H1 태그 ({len(h1s)}개)")
                for h in h1s: st.write(f"- {h}")
                if len(h1s) != 1: 
                    st.error("💡 **해결책:** H1 태그는 페이지당 반드시 '하나'만 사용해야 검색 엔진이 주제를 명확히 파악합니다.")
            
            with h_c2:
                st.subheader(f"H2 태그 ({len(h2s)}개)")
                for h in h2s[:5]: st.write(f"- {h}")
                if not h2s: st.warning("💡 **해결책:** 주요 소제목에 H2 태그를 사용하여 문서의 구조를 잡으세요.")

            st.divider()

            # --- 5. 이미지 Alt 속성 상세 리스트 ---
            st.header("5️⃣ 이미지 Alt 속성 전수 조사")
            img_list = []
            for i in imgs:
                alt = i.get('alt')
                img_list.append({
                    "상태": "✅ 정상" if alt and alt.strip() else "❌ 누락",
                    "Alt 내용": alt if alt else "(비어있음)",
                    "이미지 경로": i.get('src')
                })
            
            if img_list:
                df = pd.DataFrame(img_list)
                missing_alt = len(df[df["상태"] == "❌ 누락"])
                if missing_alt > 0:
                    st.error(f"💡 **해결책:** 아래 리스트 중 '❌ 누락'된 {missing_alt}개의 이미지에 `alt` 설명을 추가하세요.")
                st.dataframe(df, use_container_width=True)

        except Exception as e:
            st.error(f"진단 중 오류 발생: {str(e)}")
    else:
        st.warning("URL을 입력해 주세요.")
