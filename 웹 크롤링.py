import re
import requests
from bs4 import BeautifulSoup
import streamlit as st

def fetch_wikipedia_hierarchical_data(url: str) -> list:
    """
    위키백과 URL에서 h2, h3, p 태그를 문서 등장 순서대로 스캔하여
    목차와 본문이 종속되는 계층 구조 데이터를 생성합니다.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        st.error(f"웹페이지를 가져오는데 실패했습니다: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    content_div = soup.find(class_="mw-parser-output")
    
    if not content_div:
        st.error("위키백과 본문 내용을 찾을 수 없습니다. 올바른 위키백과 링크인지 확인해주세요.")
        return []

    structure = []
    current_h2 = None
    current_h3 = None

    # h2, h3, p 태그를 HTML 문서에 등장하는 순서대로 추적
    for tag in content_div.find_all(["h2", "h3", "p"]):
        
        if tag.name == "h2":
            title_text = tag.get_text().replace("[편집]", "").strip()
            if title_text in ["개요", "목차", "각주", "같이 보기", "외부 링크", "참고 문헌"]:
                current_h2 = None
                current_h3 = None
                continue
            
            current_h2 = {
                "title": title_text,
                "paragraphs": [],   # h3가 나오기 전, h2 직속 본문
                "h3_sections": []   # h2 하위의 h3 섹션들
            }
            current_h3 = None
            structure.append(current_h2)
            
        elif tag.name == "h3" and current_h2 is not None:
            title_text = tag.get_text().replace("[편집]", "").strip()
            current_h3 = {
                "title": title_text,
                "paragraphs": []    # h3 직속 본문
            }
            current_h2["h3_sections"].append(current_h3)
            
        elif tag.name == "p" and current_h2 is not None:
            p_text = tag.get_text().strip()
            p_text = re.sub(r'\[\d+\]|\[출처\s*필요\]', '', p_text)
            
            if p_text:
                if current_h3 is not None:
                    current_h3["paragraphs"].append(p_text)
                else:
                    current_h2["paragraphs"].append(p_text)

    return structure

def main():
    st.set_page_config(page_title="위키백과 목차-본문 연동 크롤러", layout="centered")
    st.title("위키백과 목차-본문 연동 크롤러")

    default_url = "https://ko.wikipedia.org/wiki/%EB%8C%8C%ED%95%9C%EB%AF%BC%EA%B5%AD%EC%9D%98_%EC%9D%B靈%EA%B5%AC"
    url_input = st.text_input("위키백과 URL을 입력하세요:", value=default_url)

    if st.button("크롤링 시작"):
        if not url_input.startswith("https://ko.wikipedia.org/"):
            st.warning("올바른 한국어 위키백과 URL 주소를 입력해주세요.")
            return

        with st.spinner("데이터를 분석하고 계층 구조를 생성하는 중입니다..."):
            data = fetch_wikipedia_hierarchical_data(url_input)
            
            if not data:
                return

            st.success("크롤링 완료!")
            
            # ----------------------------------------------------
            # 1. [상단 - 전체 목차 요약] (변동 없음)
            # ----------------------------------------------------
            st.write("### 전체 목차 요약")
            with st.container(border=True):
                for h2_idx, h2_item in enumerate(data, start=1):
                    st.markdown(f"**{h2_idx}. {h2_item['title']}**")
                    for h3_idx, h3_item in enumerate(h2_item["h3_sections"], start=1):
                        st.write(f"&nbsp;&nbsp;&nbsp;&nbsp; {h2_idx}.{h3_idx}. {h3_item['title']}")
            
            st.write("---")
            
            # ----------------------------------------------------
            # 2. [하단 - 상세 본문 접어보기] -> UI 개선 (2중 탭/토글 구조)
            # ----------------------------------------------------
            st.write("### 상세 본문 보기 (목차를 단계별로 클릭해 보세요)")

            for h2_idx, h2_item in enumerate(data, start=1):
                h2_title_with_num = f"{h2_idx}. {h2_item['title']}"
                
                # 1단계 대분류: h2 접기/펴기
                with st.expander(h2_title_with_num):
                    
                    # 예외 처리: h3가 나오기 전, h2 바로 아래에 붙어있는 본문이 있다면 먼저 출력
                    if h2_item["paragraphs"]:
                        for p in h2_item["paragraphs"]:
                            st.markdown(f"**[{h2_idx} 본문]**")
                            st.caption(p)
                        st.write("")
                    
                    # 2단계 소분류: h2 내부에 h3가 존재한다면 h3를 각각 또 하나의 expander로 감싸기
                    if h2_item["h3_sections"]:
                        for h3_idx, h3_item in enumerate(h2_item["h3_sections"], start=1):
                            current_prefix = f"{h2_idx}.{h3_idx}"
                            h3_title_with_num = f"{current_prefix}. {h3_item['title']}"
                            
                            # h3를 접었다 펼 수 있게 만듦으로써 세로 스크롤 폭발 방지
                            with st.expander(h3_title_with_num):
                                if h3_item["paragraphs"]:
                                    for p in h3_item["paragraphs"]:
                                        st.markdown(f"**[{current_prefix} 본문]**")
                                        st.write(p)
                                else:
                                    st.caption("해당 소목차에 표시할 본문 내용이 없습니다.")
                            
                    # 진짜 아무 내용도 없는 껍데기 섹션일 경우
                    if not h2_item["paragraphs"] and not h2_item["h3_sections"]:
                        st.caption("해당 섹션에 표시할 하위 항목이나 본문 내용이 없습니다.")

if __name__ == "__main__":
    main()
