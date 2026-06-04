import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False


# CSV 읽기
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
def show_raw_text(raw_text, title):

    with st.expander(f"{title} 원본 CSV 확인"):

        lines = raw_text.splitlines()[:20]

        st.text("\n".join(lines))


# 데이터 전처리
def preprocess_data(df):

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


# 인쇄자료 그래프
def plot_print_chart(df):

    st.subheader("인쇄자료 이용 현황")

    values = [
        df["인쇄_어린이"].sum(),
        df["인쇄_청소년"].sum(),
        df["인쇄_성인"].sum()
    ]

    labels = [
        "어린이",
        "청소년",
        "성인"
    ]

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.bar(labels, values)

    ax.set_title("인쇄자료 이용 현황")

    st.pyplot(fig)


# 전자자료 그래프
def plot_electronic_chart(df):

    st.subheader("전자자료 이용 현황")

    values = [
        df["전자_어린이"].sum(),
        df["전자_청소년"].sum(),
        df["전자_성인"].sum()
    ]

    labels = [
        "어린이",
        "청소년",
        "성인"
    ]

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.bar(labels, values)

    ax.set_title("전자자료 이용 현황")

    st.pyplot(fig)


# 지역별 이용 그래프
def plot_region_age_chart(df):

    st.subheader("지역별 연령대 인쇄자료 이용 현황")

    region_df = df.groupby("지역")[[
        "인쇄_어린이",
        "인쇄_청소년",
        "인쇄_성인"
    ]].sum()

    fig, ax = plt.subplots(figsize=(12, 6))

    region_df.plot(
        kind="bar",
        ax=ax
    )

    ax.set_title("지역별 연령대 인쇄자료 이용 현황")
    ax.set_xlabel("지역")
    ax.set_ylabel("이용 건수")

    plt.xticks(rotation=45)

    st.pyplot(fig)


# 데이터 특징
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


# 메인
def main():

    st.title("지역별 공공도서관 이용현황 분석 프로그램")

    st.subheader("지역별 CSV 업로드")

    seoul = st.file_uploader("서울", type=["csv"])
    busan = st.file_uploader("부산", type=["csv"])
    gyeonggi = st.file_uploader("경기", type=["csv"])
    sejong = st.file_uploader("세종", type=["csv"])
    gangwon = st.file_uploader("강원", type=["csv"])
    jeonnam = st.file_uploader("전남", type=["csv"])

    files = [
        ("서울", seoul),
        ("부산", busan),
        ("경기", gyeonggi),
        ("세종", sejong),
        ("강원", gangwon),
        ("전남", jeonnam)
    ]

    dfs = []

    for region, file in files:

        if file is not None:

            raw_text, df = load_csv(file)

            if df is not None:

                show_raw_text(raw_text, region)

                df = preprocess_data(df)

                dfs.append(df)

    if len(dfs) > 0:

        merged_df = pd.concat(
            dfs,
            ignore_index=True
        )

        st.subheader("통합 데이터")

        st.dataframe(merged_df)

        st.write(f"총 데이터 건수: {len(merged_df)}")

        st.write("컬럼 목록")
        st.write(list(merged_df.columns))

        plot_print_chart(merged_df)

        plot_electronic_chart(merged_df)

        plot_region_age_chart(merged_df)

        analyze_data(merged_df)


if __name__ == "__main__":
    main()
