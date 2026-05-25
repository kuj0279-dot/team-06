import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO

# CSV 파일 읽기 함수
def load_csv(file):

    encodings = ["utf-8", "cp949", "euc-kr"]

    for encoding in encodings:

        try:
            file.seek(0)

            # 원본 텍스트 읽기
            raw_text = file.read().decode(encoding)

            # CSV 읽기
            df = pd.read_csv(
                StringIO(raw_text),
                skiprows=2
            )

            return raw_text, df

        except:
            continue

    return None, None


# 원본 파일 내용 표시 함수
def show_raw_text(raw_text):

    with st.expander("원본 CSV 내용 확인"):

        lines = raw_text.splitlines()[:20]

        st.text("\n".join(lines))


# 데이터 전처리 함수
def preprocess_data(df):

    # 컬럼명 변경
    df.columns = [
        "도서관",
        "지역",
        "인쇄_어린이",
        "인쇄_청소년",
        "인쇄_성인",
        "인쇄_합계",
        "전자_어린이",
        "전자_청소년",
        "전자_성인",
        "전자_합계"
    ]

    # 숫자형 변환
    numeric_cols = [
        "인쇄_어린이",
        "인쇄_청소년",
        "인쇄_성인",
        "인쇄_합계",
        "전자_어린이",
        "전자_청소년",
        "전자_성인",
        "전자_합계"
    ]

    for col in numeric_cols:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    # 결측치 제거
    df = df.dropna()

    return df


# 인쇄자료 대출자 수 그래프
def plot_print_chart(df):

    st.subheader("인쇄자료 대출자 수")

    values = [
        df["인쇄_어린이"].sum(),
        df["인쇄_청소년"].sum(),
        df["인쇄_성인"].sum(),
        df["인쇄_합계"].sum()
    ]

    labels = [
        "어린이",
        "청소년",
        "성인",
        "합계"
    ]

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.bar(labels, values)

    ax.set_title("인쇄자료 대출자 수")

    st.pyplot(fig)


# 전자자료 이용자 수 그래프
def plot_electronic_chart(df):

    st.subheader("전자자료 이용자 수")

    values = [
        df["전자_어린이"].sum(),
        df["전자_청소년"].sum(),
        df["전자_성인"].sum(),
        df["전자_합계"].sum()
    ]

    labels = [
        "어린이",
        "청소년",
        "성인",
        "합계"
    ]

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.bar(labels, values)

    ax.set_title("전자자료 이용자 수")

    st.pyplot(fig)


# 데이터 특징 분석 함수
def analyze_data(df):

    st.subheader("데이터 특징 해석")

    print_max = max(
        {
            "어린이": df["인쇄_어린이"].sum(),
            "청소년": df["인쇄_청소년"].sum(),
            "성인": df["인쇄_성인"].sum()
        },
        key=lambda x: {
            "어린이": df["인쇄_어린이"].sum(),
            "청소년": df["인쇄_청소년"].sum(),
            "성인": df["인쇄_성인"].sum()
        }[x]
    )

    electronic_max = max(
        {
            "어린이": df["전자_어린이"].sum(),
            "청소년": df["전자_청소년"].sum(),
            "성인": df["전자_성인"].sum()
        },
        key=lambda x: {
            "어린이": df["전자_어린이"].sum(),
            "청소년": df["전자_청소년"].sum(),
            "성인": df["전자_성인"].sum()
        }[x]
    )

    st.write(f"인쇄자료 이용이 가장 많은 연령대: {print_max}")

    st.write(f"전자자료 이용이 가장 많은 연령대: {electronic_max}")


# 메인 함수
def main():

    st.title("지역별 공공도서관 이용현황 분석 프로그램")

    # CSV 파일 업로드
    uploaded_file = st.file_uploader(
        "CSV 파일 업로드",
        type=["csv"]
    )

    if uploaded_file is not None:

        # CSV 읽기
        raw_text, df = load_csv(uploaded_file)

        if df is not None:

            # 원본 파일 내용 표시
            show_raw_text(raw_text)

            # 데이터 전처리
            df = preprocess_data(df)

            # 데이터 미리보기
            st.subheader("데이터 미리보기")

            st.dataframe(df)

            st.write(f"총 데이터 건수: {len(df)}")

            st.write("컬럼 목록")
            st.write(list(df.columns))

            # 그래프 출력
            plot_print_chart(df)

            plot_electronic_chart(df)

            # 데이터 특징 분석
            analyze_data(df)

        else:

            st.error("CSV 파일을 읽을 수 없습니다.")


# 프로그램 실행
if __name__ == "__main__":
    main()
