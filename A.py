import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import platform

# -----------------------------
# 한글 폰트 설정
# -----------------------------
def set_korean_font():
    system = platform.system()

    if system == "Windows":
        font_list = ["Malgun Gothic", "맑은 고딕"]
    elif system == "Darwin":  # Mac
        font_list = ["AppleGothic"]
    else:  # Linux 등
        font_list = ["NanumGothic", "DejaVu Sans"]

    available_fonts = [f.name for f in fm.fontManager.ttflist]

    for font in font_list:
        if font in available_fonts:
            plt.rcParams["font.family"] = font
            break

    plt.rcParams["axes.unicode_minus"] = False

# -----------------------------
# 엑셀 파일을 읽어 DataFrame으로 반환하는 함수
# -----------------------------
def load_excel(file, start_row):
    try:
        df = pd.read_excel(file, header=None, engine="openpyxl")
        return df.iloc[start_row - 1:].reset_index(drop=True)
    except Exception as e:
        st.error(f"엑셀 파일을 불러오는 중 오류가 발생했습니다: {e}")
        return None

# -----------------------------
# 원본 파일의 처음 20줄을 텍스트 형태로 보여주는 함수
# -----------------------------
def show_raw_preview(df):
    st.text(df.head(20).to_string(index=False, header=False))

# -----------------------------
# 필요한 열(B, C, D)만 추출하고 컬럼명을 변경하는 함수
# -----------------------------
def process_data(df):
    try:
        processed = df.iloc[:, [1, 2, 3]].copy()
        processed.columns = ["지역명", "인구구조_항목", "2025년_수치"]
        processed["2025년_수치"] = pd.to_numeric(processed["2025년_수치"], errors="coerce")
        processed = processed.dropna(subset=["지역명", "인구구조_항목", "2025년_수치"]).reset_index(drop=True)
        return processed
    except Exception as e:
        st.error(f"데이터 처리 중 오류가 발생했습니다: {e}")
        return None

# -----------------------------
# 최종 데이터 정보를 화면에 출력하는 함수
# -----------------------------
def show_result(df):
    st.subheader("최종 데이터")
    st.dataframe(df, use_container_width=True)

    st.subheader("요약 정보")
    st.write(f"총 데이터 건수: {len(df)}")
    st.write(f"컬럼 목록: {list(df.columns)}")

# -----------------------------
# 지역별 인구구조 분석 함수
# -----------------------------
def analyze_population_structure(df):
    try:
        set_korean_font()

        st.subheader("지역별 인구구조 분석")

        # 관심 항목만 필터링
        target_items = ["유소년인구", "생산인구", "노년인구"]
        filtered = df[df["인구구조_항목"].isin(target_items)].copy()

        if filtered.empty:
            st.warning("유소년인구, 생산인구, 노년인구 데이터가 없습니다.")
            return

        # 지역명 + 인구구조_항목 기준으로 피벗
        pivot_df = filtered.pivot_table(
            index="지역명",
            columns="인구구조_항목",
            values="2025년_수치",
            aggfunc="sum",
            fill_value=0
        )

        # 컬럼 순서 정리
        for col in target_items:
            if col not in pivot_df.columns:
                pivot_df[col] = 0

        pivot_df = pivot_df[target_items]

        # 지역별 합계
        pivot_df["합계"] = pivot_df.sum(axis=1)

        # 100% 기준 비율 계산
        ratio_df = pivot_df[target_items].div(pivot_df["합계"], axis=0) * 100
        ratio_df = ratio_df.fillna(0)

        # 결과 테이블 출력
        result_show = ratio_df.copy()
        result_show.index.name = "지역명"
        st.write("지역별 인구구조 비율(%)")
        st.dataframe(result_show.reset_index(), use_container_width=True)

        # 100% 누적 막대그래프
        fig, ax = plt.subplots(figsize=(14, 7))

        bottom = pd.Series([0] * len(ratio_df), index=ratio_df.index)

        colors = {
            "유소년인구": "#4C78A8",
            "생산인구": "#F58518",
            "노년인구": "#54A24B"
        }

        for col in target_items:
            ax.bar(
                ratio_df.index,
                ratio_df[col],
                bottom=bottom,
                label=col,
                color=colors[col]
            )
            bottom += ratio_df[col]

        ax.set_xlabel("지역명")
        ax.set_ylabel("비율(%)")
        ax.set_title("지역별 인구구조 100% 누적 막대그래프")
        ax.set_ylim(0, 100)
        ax.legend()
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()

        st.pyplot(fig)

    except Exception as e:
        st.error(f"지역별 인구구조 분석 중 오류가 발생했습니다: {e}")

# -----------------------------
# 메인 화면 구성
# -----------------------------
def main():
    st.title("지역별 인구구조 분석 프로그램")

    uploaded_file = st.file_uploader("엑셀 파일(.xlsx)을 업로드하세요", type=["xlsx"])

    if uploaded_file is not None:
        start_row = st.number_input("데이터 시작 행 번호", min_value=1, value=6, step=1)

        st.subheader("원본 파일 내용 확인")
        with st.expander("처음 20줄 보기"):
            raw_df = pd.read_excel(uploaded_file, header=None, engine="openpyxl")
            show_raw_preview(raw_df)

        uploaded_file.seek(0)
        df = load_excel(uploaded_file, start_row)

        if df is not None:
            st.subheader("시작 행부터 읽은 데이터")
            st.dataframe(df.head(20), use_container_width=True)

            result_df = process_data(df)

            if result_df is not None:
                show_result(result_df)

                if st.button("지역별 인구구조 분석"):
                    analyze_population_structure(result_df)

if __name__ == "__main__":
    main()
  
