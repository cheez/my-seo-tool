import streamlit as st
import subprocess
import sys
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urlparse, urljoin
import time
import re
from collections import Counter
 
# Playwright chromium 설치 (최초 1회)
@st.cache_resource(show_spinner=False)
def install_playwright():
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"],
                   capture_output=True)
 
install_playwright()
 
st.set_page_config(page_title="Professional SEO Analyzer v2.1", layout="wide")
st.title("SEO & 키워드 종합 분석 리포트(sanghee kim - ICS 제외)")
st.caption("On-Page SEO부터 정밀 이미지 경로 분석까지, 전문적인 진단 결과를 제공합니다.")
st.markdown("---")
 
url = st.text_input("진단할 사이트 주소 (https:// 필수)", "https://")
 
if st.button("종합 분석 시작"):
    if url.startswith("http"):
        try:
            with st.spinner('사이트 데이터를 정밀 분석 중입니다... (JS 렌더링 포함, 약 10~20초 소요)'):
                from playwright.sync_api import sync_playwright
                start_time = time.time()
 
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    )
                    page = context.new_page()
                    page.goto(url, timeout=60000, wait_until='domcontentloaded')
                    page.wait_for_timeout(3000)
                    html = page.content()
                    browser.close()
 
                load_speed = round((time.time() - start_time), 2)
                soup = BeautifulSoup(html, 'html.parser')
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
                ratio = round((len(text_content) / len(html)) * 100, 1) if len(html) > 0 else 0
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
 
            # --- 5️⃣ 이미지 분석 ---
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
                    i.get('ec-data-src', '').strip() or
                    i.get('src', '').strip() or
                    i.get('data-src', '').strip() or
                    i.get('data-lazy-src', '').strip() or
                    i.get('data-original', '').strip()
                )
                if not raw_src or 'data:image' in raw_src or any(p in raw_src.lower() for p in ['blank', 'pixel', 'spacer']):
                    continue
 
                full_src = urljoin(base_url, raw_src) if not raw_src.startswith('//') else "https:" + raw_src
                clickable_path = f'<a href="{full_src}" target="_blank" style="text-decoration:none; color:#007bff; word-break:break-all;">{full_src}</a>'
 
                if alt_text:
                    status = "✅ 있음"
                    alt_ok += 1
                elif has_alt_attr:
                    status = "⚠️ 빈 alt"
                    alt_empty += 1
                else:
                    status = "❌ 누락"
                    alt_missing += 1
                    
                # 접근성 텍스트 추출: figcaption 또는 sr-only 요소
                a11y_text = ""
                parent = i.parent
                if parent:
                    sr = parent.select_one('[class*="sr-only"]')
                    if sr:
                        a11y_text = ' '.join(sr.get_text(separator=' ').split())
                if not a11y_text:
                    parent_figure = i.find_parent('figure')
                    if parent_figure:
                        figcaption = parent_figure.find('figcaption')
                        if figcaption:
                            a11y_text = ' '.join(figcaption.get_text(separator=' ').split())

                img_data.append({
                    "상태": status,
                    "Alt 내용": alt_text if alt_text else ("(장식 이미지)" if has_alt_attr else "없음"),
                    "접근성 텍스트(sr-only/figcaption)": a11y_text if a11y_text else "-",
                    "이미지 경로": clickable_path
                })

            if img_data:
                total = len(img_data)
                s_col1, s_col2, s_col3, s_col4 = st.columns(4)
                with s_col1: st.metric("전체 이미지", f"{total}개")
                with s_col2: st.metric("✅ Alt 있음", f"{alt_ok}개")
                with s_col3: st.metric("⚠️ 빈 alt", f"{alt_empty}개")
                with s_col4: st.metric("❌ Alt 누락", f"{alt_missing}개")
                st.caption("⚠️ 빈 alt: alt 속성은 존재하지만 내용이 없음 (장식 이미지일 경우 정상, 의미 있는 이미지라면 수정 필요)")
 
                html_table = pd.DataFrame(img_data).to_html(escape=False, index=False)
                html_table = html_table.replace('<table border="1" class="dataframe">', '<table class="img-table">')
                styled = """
<style>

table.img-table { width:100%; border-collapse:collapse; font-size:13px; table-layout:fixed; }
table.img-table thead tr { background-color:#f0f2f6; }
table.img-table th { padding:10px 12px; text-align:center; font-weight:600; border-bottom:2px solid #dee2e6; white-space:nowrap; }
table.img-table td { padding:8px 12px; border-bottom:1px solid #eee; vertical-align:middle; }
table.img-table td:nth-child(1) { text-align:center; white-space:nowrap; width:90px; }
table.img-table td:nth-child(2) { width:250px; word-break:break-word; }
table.img-table td:nth-child(3) { word-break:break-all; }
table.img-table tr:hover { background-color:#f8f9fa; }
</style>
"""
                st.markdown(styled + html_table, unsafe_allow_html=True)
            else:
                st.info("발견된 이미지가 없습니다.")
 
            st.divider()

            # --- 6️⃣ 클릭 추적 속성 분석 ---
            st.header("6️⃣ 클릭 추적 속성 분석 (ap-click)")
            click_attrs = ['ap-click-area', 'aria-hidden', 'ap-click-name', 'ap-click-data']
            anchors = soup.find_all('a')
            click_data = []

            for a in anchors:
                has_click_attr = any(a.has_attr(attr) for attr in click_attrs)
                if not has_click_attr:
                    continue

                href = a.get('href', '').strip()
                full_href = urljoin(base_url, href) if href and not href.startswith(('http', '//', '#', 'javascript')) else href
                link_html = f'<a href="{full_href}" target="_blank" style="text-decoration:none; color:#007bff; word-break:break-all;">{full_href or "-"}</a>' if full_href and full_href not in ('-', '', 'javascript:void(0)', 'javascript:;') else (full_href or "-")
                link_text = ' '.join(a.get_text(separator=' ').split())[:80]

                click_data.append({
                    "링크 텍스트": link_text if link_text else "-",
                    "ap-click-area": a.get('ap-click-area', '-'),
                    "aria-hidden": a.get('aria-hidden', '-'),
                    "ap-click-name": a.get('ap-click-name', '-'),
                    "ap-click-data": a.get('ap-click-data', '-'),
                    "링크 경로": link_html,
                })

            if click_data:
                st.metric("클릭 추적 a 태그 수", f"{len(click_data)}개")
                html_click_table = pd.DataFrame(click_data).to_html(escape=False, index=False)
                html_click_table = html_click_table.replace('<table border="1" class="dataframe">', '<table class="click-table">')
                click_styled = """
<style>
table.click-table { width:100%; border-collapse:collapse; font-size:13px; table-layout:fixed; }
table.click-table thead tr { background-color:#e8f4fd; }
table.click-table th { padding:10px 12px; text-align:center; font-weight:600; border-bottom:2px solid #bee3f8; white-space:nowrap; }
table.click-table td { padding:8px 12px; border-bottom:1px solid #eee; vertical-align:middle; word-break:break-word; }
table.click-table td:nth-child(1) { width:130px; }
table.click-table td:nth-child(2) { width:130px; text-align:center; }
table.click-table td:nth-child(3) { width:90px; text-align:center; }
table.click-table td:nth-child(4) { width:160px; }
table.click-table td:nth-child(5) { width:180px; }
table.click-table td:nth-child(6) { word-break:break-all; }
table.click-table tr:hover { background-color:#f0f8ff; }
</style>
"""
                st.markdown(click_styled + html_click_table, unsafe_allow_html=True)
            else:
                st.info("ap-click 관련 속성을 가진 a 태그가 없습니다.")

        except Exception as e:
            st.error(f"오류 발생: {str(e)}")
