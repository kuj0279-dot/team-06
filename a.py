import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False


# CSV 파일 읽기
def load_csv(file):

    encodings = ["utf-8", "cp949", "euc-kr"]

    for encoding in encodings:
        try:
            file.seek(0)

            raw_text = file.read().decode(encoding)

            df = pd.read_csv(
                StringIO(raw_text),
                skiprows=2
            )

            return raw_text, df

        except:
            continue

    return None, None


# 원본 파일 확인
def show_raw_text(raw_text, file_name):

    with st.expander(f"{file_name} 원본 CSV 내용 확인"):

        lines = raw_text.splitlines()[:20]

        st.text("\n".join(lines))


# 데이터 전처리
def preprocess_data(df):

    # 필요한 컬럼만 사용
    df = df.iloc[:, :10]

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

        df[col] = (
            df[col]
            .astype(str)
            .str.replace(",", "", regex=False)
        )

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    df = df.dropna()

    return df


# 지역별 대출권수 비교
def plot_loan_chart(df):

    st.subheader("지역별 인쇄자료 대출권수")

    loan_df = (
        df.groupby("지역")["인쇄_합계"]
        .sum()
        .sort_values(ascending=False)
    )

    fig, ax = plt.subplots(figsize=(12, 5))

    ax.bar(loan_df.index, loan_df.values)

    ax.set_title("지역별 인쇄자료 대출권수")
    ax.set_xlabel("지역")
    ax.set_ylabel("대출권수")

    plt.xticks(rotation=45)

    st.pyplot(fig)


# 지역별 전자자료 이용자수 비교
def plot_user_chart(df):

    st.subheader("지역별 전자자료 이용자수")

    user_df = (
        df.groupby("지역")["전자_합계"]
        .sum()
        .sort_values(ascending=False)
    )

    fig, ax = plt.subplots(figsize=(12, 5))

    ax.bar(user_df.index, user_df.values)

    ax.set_title("지역별 전자자료 이용자수")
    ax.set_xlabel("지역")
    ax.set_ylabel("이용자수")

    plt.xticks(rotation=45)

    st.pyplot(fig)


# 연령별 이용 비교
def plot_age_chart(df):

    st.subheader("연령별 이용 현황")

    age_df = pd.DataFrame({
        "인쇄자료": [
            df["인쇄_어린이"].sum(),
            df["인쇄_청소년"].sum(),
            df["인쇄_성인"].sum()
        ],
        "전자자료": [
            df["전자_어린이"].sum(),
            df["전자_청소년"].sum(),
            df["전자_성인"].sum()
        ]
    },
    index=["어린이", "청소년", "성인"])

    fig, ax = plt.subplots(figsize=(8, 5))

    age_df.plot(
        kind="bar",
        ax=ax
    )

    ax.set_title("연령별 인쇄자료·전자자료 이용 비교")
    ax.set_xlabel("연령대")
    ax.set_ylabel("이용 건수")

    st.pyplot(fig)


# 지역별 도서관 수 비교
def plot_library_chart(df):

    st.subheader("지역별 공공도서관 수")

    library_df = (
        df.groupby("지역")["도서관"]
        .count()
        .sort_values(ascending=False)
    )

    fig, ax = plt.subplots(figsize=(12, 5))

    ax.bar(
        library_df.index,
        library_df.values
    )

    ax.set_title("지역별 공공도서관 수")
    ax.set_xlabel("지역")
    ax.set_ylabel("도서관 수")

    plt.xticks(rotation=45)

    st.pyplot(fig)


# 데이터 특징 해석
def analyze_data(df):

    st.subheader("데이터 특징 해석")

    print_total = {
        "어린이": df["인쇄_어린이"].sum(),
        "청소년": df["인쇄_청소년"].sum(),
        "성인": df["인쇄_성인"].sum()
    }

    electronic_total = {
        "어린이": df["전자_어린이"].sum(),
        "청소년": df["전자_청소년"].sum(),
        "성인": df["전자_성인"].sum()
    }

    print_max = max(print_total, key=print_total.get)
    electronic_max = max(electronic_total, key=electronic_total.get)

    st.write(f"인쇄자료 이용이 가장 많은 연령대: {print_max}")
    st.write(f"전자자료 이용이 가장 많은 연령대: {electronic_max}")

    st.write(
        f"전체 인쇄자료 이용 건수: {df['인쇄_합계'].sum():,.0f}"
    )

    st.write(
        f"전체 전자자료 이용 건수: {df['전자_합계'].sum():,.0f}"
    )


# 메인 함수
def main():

    st.title("연령별 도서관 이용 현황 프로그램")

    uploaded_files = st.file_uploader(
        "CSV 파일 6개 업로드",
        type=["csv"],
        accept_multiple_files=True
    )

    if uploaded_files:

        # 파일 개수 제한
        if len(uploaded_files) > 6:
            st.error("CSV 파일은 최대 6개까지 업로드 가능합니다.")
            return

        all_df = []

        for uploaded_file in uploaded_files:

            st.markdown(f"## 파일명 : {uploaded_file.name}")

            raw_text, df = load_csv(uploaded_file)

            if df is not None:

                show_raw_text(raw_text, uploaded_file.name)

                df = preprocess_data(df)

                all_df.append(df)

            else:

                st.error(f"{uploaded_file.name} 파일을 읽을 수 없습니다.")

        # 모든 파일 합치기
        if len(all_df) > 0:

            merged_df = pd.concat(
                all_df,
                ignore_index=True
            )

            st.subheader("통합 전처리 데이터")

            st.dataframe(merged_df)

            st.write(f"총 데이터 건수 : {len(merged_df)}")

            st.write("컬럼 목록")

            st.write(list(merged_df.columns))

            # 그래프 출력
            plot_loan_chart(merged_df)

            plot_user_chart(merged_df)

            plot_age_chart(merged_df)

            plot_library_chart(merged_df)

            analyze_data(merged_df)


if __name__ == "__main__":
    main()
