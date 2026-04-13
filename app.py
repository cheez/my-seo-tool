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
st.set_page_config(page_title="Professional SEO Analyzer", layout="wide")

st.title("SEO & 키워드 분석 리포트")
st.caption("On-Page SEO부터 이미지 경로 정밀 분석까지 한 번에 진단합니다.")
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

            # --- 1. 퍼포먼스 점검 ---
            st.header("1️⃣ 사이트 퍼포먼스")
            t_col1, t_col2, t_col3, t_col4 = st.columns(4)
            with t_col1: st.metric("로딩 속도", f"{load_speed}초")
            with t_col2: st.metric("모바일 최적화", "✅" if soup.find('meta', attrs={'name': 'viewport'}) else "❌")
            with t_col3: st.metric("HTTPS", "✅" if url.startswith("https") else "⚠️")
            with t_col4:
                ratio = round((len(soup.get_text()) / len(res.text)) * 100, 1) if len(res.text) > 0 else 0
                st.metric("콘텐츠 비중", f"{ratio}%")

            st.divider()

            # --- 2. 이미지 및 Alt 속성 (스크롤 제거 및 경로 추출 강화) ---
            st.header("2️⃣ 이미지 분석 및 Alt 속성 (전체 리스트)")
            imgs = soup.find_all('img')
            img_list = []
            
            # 필터링할 무의미한 이미지
            dummy_keywords = ['blank', 'pixel', 'spacer', 'loading', 'transparent']

            for i in imgs:
                # [핵심] 실제 경로가 숨어있을 가능성이 있는 모든 속성 리스트
                attr_candidates = [
                    'data-src', 'data-original', 'data-lazy-src', 'data-srcset', 
                    'original-src', 'data-original-src', 'src', 'srcset'
                ]
                
                raw_src = None
                for attr in attr_candidates:
                    val = i.get(attr)
                    if val:
                        # 더미 이미지 키워드가 포함된 경우 건너뜀
                        if any(dk in val.lower() for dk in dummy_keywords):
                            continue
                        raw_src = val
                        break
                
                # 경로 정제 로직
                if raw_src:
                    # srcset 처리 (공백 기준으로 첫 번째 주소만 추출)
                    if ',' in raw_src:
                        raw_src = raw_src.split(',')[0].split(' ')[0]
                    
                    if raw_src.startswith('//'):
                        full_src = "https:" + raw_src
                    elif raw_src.startswith('data:image'):
                        full_src = "내장 이미지(Base64)"
                    else:
                        full_src = urljoin(base_url, raw_src)
                else:
                    full_src = "경로 찾을 수 없음"

                img_list.append({
                    "상태": "✅" if i.get('alt') else "❌ 누락",
                    "Alt 내용": i.get('alt', '내용 없음').strip(),
                    "이미지 경로": full_src
                })

            if img_list:
                df = pd.DataFrame(img_list)
                # st.table을 사용하여 스크롤 없이 전체 노출
                st.table(df)
                
                total_imgs = len(img_list)
                missing_alt = len([img for img in img_list if img['상태'] == "❌ 누락"])
                st.info(f"총 {total_imgs}개의 이미지를 발견했습니다. (Alt 누락: {missing_alt}개)")
            else:
                st.info("이미지를 찾을 수 없습니다.")

        except Exception as e:
            st.error(f"진단 중 오류 발생: {str(e)}")
    else:
        st.warning("URL을 입력해 주세요.")
