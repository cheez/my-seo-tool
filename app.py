import streamlit as st
import cloudscraper
from bs4 import BeautifulSoup
import pandas as pd
from fake_useragent import UserAgent
from urllib.parse import urlparse

# 페이지 설정
st.set_page_config(page_title="Ultimate SEO & Best Practices Audit", layout="wide")

st.title("🏆 프리미엄 SEO & 웹 표준 진단 리포트")
st.markdown("---")

url = st.text_input("진단할 사이트 주소 (https:// 필수)", "https://")

if st.button("종합 리포트 생성"):
    if url.startswith("http"):
        try:
            ua = UserAgent()
            scraper = cloudscraper.create_scraper()
            res = scraper.get(url, headers={'User-Agent': ua.random}, timeout=20)
            res.raise_for_status()
            res.encoding = res.apparent_encoding
            html_content = res.text
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # --- 섹션 1: 기술적 접근성 ---
            st.header("1️⃣ 기술적 접근성 점검 (Technical)")
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            t_col1, t_col2, t_col3 = st.columns(3)
            try:
                rb_res = scraper.get(f"{base_url}/robots.txt", timeout=5)
                has_robots = rb_res.status_code == 200
            except: has_robots = False
                
            with t_col1:
                st.metric("HTTPS 보안 연결", "✅ 안전" if url.startswith("https") else "⚠️ 위험")
            with t_col2:
                st.metric("Robots.txt 존재", "✅ 발견" if has_robots else "❌ 미발견")
            with t_col3:
                text_len = len(soup.get_text())
                html_len = len(html_content)
                ratio = round((text_len / html_len) * 100, 1)
                st.metric("콘텐츠 비중", f"{ratio}%")

            st.divider()

            # --- 섹션 2: 메타 데이터 ---
            st.header("2️⃣ 메타 데이터 및 SNS 설정")
            m_col1, m_col2 = st.columns(2)
            title = soup.find('title')
            desc = soup.find('meta', attrs={'name': 'description'})
            og_img = soup.find('meta', attrs={'property': 'og:image'})
            
            with m_col1:
                st.subheader("검색 엔진 노출")
                st.write(f"**제목:** {title.text if title else '❌ 누락'}")
                st.write(f"**설명:** {desc.get('content')[:100] + '...' if desc else '❌ 누락'}")
            with m_col2:
                st.subheader("SNS 공유 이미지 (OG)")
                if og_img: st.image(og_img['content'], width=200)
                else: st.warning("공유 이미지가 없습니다.")

            st.divider()

# --- 섹션 3: 웹 표준 권장사항 ---
            st.header("3️⃣ 웹 표준 권장사항 (Best Practices)")
            b_col1, b_col2 = st.columns(2)
            
            # 1) 외부 링크 보안 체크
            external_links = soup.find_all('a', href=True, target="_blank")
            unsafe_links = [l for l in external_links if 'noopener' not in (l.get('rel') or [])]
            
            # 2) 이미지 규격 체크 (width와 height 속성이 모두 있는지 확인)
            imgs = soup.find_all('img')
            no_size_imgs = [i for i in imgs if not (i.get('width') and i.get('height'))]
            
            with b_col1:
                st.subheader("🔗 외부 링크 보안")
                if not unsafe_links:
                    st.success("✅ 모든 외부 링크가 안전하게 설정되었습니다.")
                else:
                    st.error(f"⚠️ 보안 취약점: {len(unsafe_links)}개의 외부 링크에 'noopener' 속성이 없습니다.")
                    st.caption("새 창으로 링크를 열 때 사이트 성능과 보안을 위해 필수입니다.")

            with b_col2:
                st.subheader("🖼️ 이미지 레이아웃 안정성")
                if not no_size_imgs:
                    st.success("✅ 모든 이미지에 크기(width/height)가 지정되었습니다.")
                else:
                    st.warning(f"⚠️ 주의: {len(no_size_imgs)}개의 이미지에 크기 속성이 없습니다.")
                    st.caption("크기 미지정 시 로딩 중 화면이 흔들리는(CLS) 현상이 발생할 수 있습니다.")

            st.divider()

            # --- 섹션 4: 상세 구조 분석 ---
            st.header("4️⃣ 상세 구조 분석 (Headings & Alt)")
            tab1, tab2 = st.tabs(["Heading 위계", "전체 이미지 리스트"])
            
            with tab1:
                h1s = [h.get_text().strip() for h in soup.find_all('h1')]
                st.write(f"**H1 태그 ({len(h1s)}개):**")
                for h in h1s: 
                    st.write(f"- {h}")
                if len(h1s) != 1: 
                    st.error("H1은 반드시 1개여야 최적입니다.")
                
            with tab2:
                img_data = []
                for i in imgs:
                    alt = i.get('alt')
                    img_data.append({
                        "상태": "✅" if alt and alt.strip() else "❌ 누락",
                        "Alt": alt if alt else "(비어있음)",
                        "경로": i.get('src')
                    })
                
                if img_data:
                    st.dataframe(pd.DataFrame(img_data), use_container_width=True)
                else:
                    st.info("분석할 이미지가 없습니다.")

        except Exception as e:
            st.error(f"진단 중 오류 발생: {str(e)}")
    else:
        st.warning("URL을 입력해 주세요.")
