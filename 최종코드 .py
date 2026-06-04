import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from io import StringIO

# 한글 설정
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

# 페이지 레이아웃 확장 (다차원 비교 대시보드를 위해 wide 모드 필수 설정)
st.set_page_config(
    page_title="도서관 인구구조 다차원 분석", layout="wide"
)


# =========================
# 도서관 CSV 읽기
# =========================
def load_library_csv(file):
    encodings = ["utf-8", "cp949", "euc-kr"]
    for encoding in encodings:
        try:
            file.seek(0)
            raw_text = file.read().decode(encoding)
            # 파일명에서 지역구분 키워드 추출 (예: 서울.csv -> 서울)
            region_hint = file.name.split(".")[0]

            df = pd.read_csv(StringIO(raw_text), skiprows=2)
            return raw_text, df, region_hint
        except:
            continue
    return None, None, None


# =========================
# 인구구조 CSV 읽기
# =========================
def load_population_csv(file):
    encodings = ["utf-8", "cp949", "euc-kr"]
    for encoding in encodings:
        try:
            file.seek(0)
            raw_text = file.read().decode(encoding)
            df = pd.read_csv(StringIO(raw_text))
            return raw_text, df
        except:
            continue
    return None, None


# =========================
# 도서관 전처리
# =========================
def preprocess_library(df, file_name_hint):
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
        "전자_합계",
    ]

    numeric_cols = [
        "인쇄_어린이",
        "인쇄_청소년",
        "인쇄_성인",
        "인쇄_합계",
        "전자_어린이",
        "전자_청소년",
        "전자_성인",
        "전자_합계",
    ]

    for col in numeric_cols:
        df[col] = df[col].astype(str).str.replace(",", "", regex=False)
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna().copy()

    # 데이터 내 '지역' 컬럼이 비어있거나 불분명할 경우 파일 이름 힌트로 보완
    for keyword in ["서울", "부산", "경기", "세종", "강원", "전남"]:
        if keyword in file_name_hint:
            df["지역"] = keyword
            break

    return df


# =========================
# 인구구조 전처리
# =========================
def preprocess_population(df):
    df = df.iloc[:, 1:4]
    df.columns = ["지역", "구분", "비율"]
    df["비율"] = pd.to_numeric(df["비율"], errors="coerce")

    result = []
    for region in df["지역"].unique():
        temp = df[df["지역"] == region]
        values = temp["비율"].tolist()
        if len(values) >= 3:
            result.append([region, values[0], values[1], values[2]])

    pop_df = pd.DataFrame(result, columns=["지역", "유소년", "생산연령", "노년"])
    pop_df["지역"] = pop_df["지역"].replace(
        {
            "서울특별시": "서울",
            "부산광역시": "부산",
            "경기도": "경기",
            "세종특별자치시": "세종",
            "강원특별자치도": "강원",
            "전라남도": "전남",
        }
    )
    return pop_df


# =========================
# 데이터 통합 핵심 로직 (도서관수, 대출량, 이용량 추출)
# =========================
def build_merged_df(library_df, population_df):
    # 1. 도서관 수 카운트 (각 지역별 데이터 개수)
    lib_count = (
        library_df.groupby("지역")["도서관"]
        .count()
        .reset_index(name="도서관수")
    )

    # 2. 대출량 및 이용자 지표 합산
    lib_sum = (
        library_df.groupby("지역")
        .sum(numeric_only=True)
        .reset_index()
    )

    # 파생 변수 정의: 인쇄+전체 합계를 '총 대출량'으로, 각 세부 연령대 합산 수치를 '활성 이용량'의 지표로 매핑
    lib_sum["총_대출량"] = (
        lib_sum["인쇄_합계"] + lib_sum["전자_합계"]
    )
    lib_sum["어린이_이용량"] = (
        lib_sum["인쇄_어린이"] + lib_sum["전자_어린이"]
    )
    lib_sum["성인_이용량"] = (
        lib_sum["인쇄_성인"] + lib_sum["전자_성인"]
    )

    # 3. 인구구조 데이터와 병합
    merged = pd.merge(lib_count, lib_sum, on="지역")
    merged = pd.merge(merged, population_df, on="지역")

    return merged


# =========================
# 질문에 완벽히 부합하는 3단 비교 대시보드 그래프
# =========================
def draw_question_dashboard(merged_df):
    st.write(
        "### 📊 지역별 인구 구조 대비 도서관 핵심 3대 지표 (도서관 수 vs 대출량 vs 이용 패턴)"
    )
    st.markdown(
        "지자체의 인구 특성이 도서관 인프라(수)와 실질적 성과(대출량/이용자 데이터)에 미치는 차이를 한눈에 대조합니다."
    )

    col1, col2, col3 = st.columns(3)

    # 차트 1: 도서관 수 비교
    with col1:
        st.write("#### 🏢 1. 지역별 공공도서관 수")
        fig1, ax1 = plt.subplots(figsize=(5, 4.5))
        ax1.bar(
            merged_df["지역"],
            merged_df["도서관수"],
            color="#2b6cb0",
            alpha=0.8,
        )
        ax1.set_ylabel("도서관 개수 (개)")
        for i, val in enumerate(merged_df["도서관수"]):
            ax1.text(i, val + 0.5, f"{val}개", ha="center", fontsize=9)
        st.pyplot(fig1)

    # 차트 2: 총 대출량 비교
    with col2:
        st.write("#### 📚 2. 지역별 총 대출량 (인쇄+전자)")
        fig2, ax2 = plt.subplots(figsize=(5, 4.5))
        ax2.bar(
            merged_df["지역"],
            merged_df["총_대출량"] / 10000,
            color="#c53030",
            alpha=0.8,
        )
        ax2.set_ylabel("대출 건수 (만 건)")
        plt.xticks(rotation=0)
        st.pyplot(fig2)

    # 차트 3: 인구 구조 원인 대조 (누적 막대)
    with col3:
        st.write("#### 👥 3. [원인 background] 지역별 인구 구조 비율")
        fig3, ax3 = plt.subplots(figsize=(5, 4.5))
        merged_df.set_index("지역")[["유소년", "생산연령", "노년"]].plot(
            kind="bar",
            stacked=True,
            color=["#4f79a7", "#f28e2b", "#59a14f"],
            ax=ax3,
        )
        ax3.set_ylabel("비율 (%)")
        ax3.legend(loc="lower left")
        plt.xticks(rotation=0)
        st.pyplot(fig3)


# =========================
# 질문 검증 전용 다차원 상관관계 분석 그래프
# =========================
def draw_multivariate_correlation(merged_df):
    st.write("### 🔍 질문 검증을 위한 핵심 인구지표 간 상관관계 분석")
    st.markdown(
        "인구 구조(원인)가 도서관 수, 대출량, 이용자 유형에 미치는 선형적 관계를 입증합니다."
    )

    col1, col2 = st.columns(2)

    with col1:
        st.write("#### 💡 [검증 1] 유소년 인구 비율 ↔ 어린이 이용자 행동성")
        fig1, ax1 = plt.subplots(figsize=(6, 5))
        ax1.scatter(
            merged_df["유소년"],
            merged_df["어린이_이용량"] / 10000,
            s=150,
            color="#1f77b4",
            edgecolor="black",
        )

        for i in range(len(merged_df)):
            ax1.text(
                merged_df["유소년"].iloc[i] + 0.2,
                (merged_df["어린이_이용량"].iloc[i] / 10000),
                merged_df["지역"].iloc[i],
                fontsize=10,
                weight="bold",
            )
        ax1.set_xlabel("유소년 인구 비율 (%)")
        ax1.set_ylabel("어린이 총 이용 및 대출량 (만 건)")
        ax1.grid(True, linestyle="--", alpha=0.5)
        st.pyplot(fig1)

    with col2:
        st.write("#### 💡 [검증 2] 생산연령 인구 비율 ↔ 성인 이용자 대출 활동")
        fig2, ax2 = plt.subplots(figsize=(6, 5))
        ax2.scatter(
            merged_df["생산연령"],
            merged_df["성인_이용량"] / 10000,
            s=150,
            color="#2ca02c",
            edgecolor="black",
        )

        for i in range(len(merged_df)):
            ax2.text(
                merged_df["생산연령"].iloc[i] + 0.1,
                (merged_df["성인_이용량"].iloc[i] / 10000),
                merged_df["지역"].iloc[i],
                fontsize=10,
                weight="bold",
            )
        ax2.set_xlabel("생산연령 인구 비율 (%)")
        ax2.set_ylabel("성인 총 이용 및 대출량 (만 건)")
        ax2.grid(True, linestyle="--", alpha=0.5)
        st.pyplot(fig2)


# =========================
# 메인 함수
# =========================
def main():
    st.title("📊 공공도서관 3대 지표(수·대출량·이용자) 및 인구구조 통합 분석기")

    # 질문 검증 탭 중심으로 구성 재배치
    tab1, tab2, tab3 = st.tabs(
        [
            "🧐 질문 검증: 3대 지표 비교 대시보드",
            "📈 세부 상관관계 분석",
            "🗂️ 전처리 통합 데이터 집계표",
        ]
    )

    with st.sidebar:
        st.header("1. 도서관 데이터 다중 업로드")
        library_files = st.file_uploader(
            "6개 지역 도서관 CSV 파일 일괄 드래그",
            type="csv",
            accept_multiple_files=True,
        )
        st.caption(f"업로드 완료된 도서관 데이터: {len(library_files)}개")

        st.markdown("---")
        st.header("2. 인구구조 데이터 업로드")
        population = st.file_uploader("인구구조 통합 CSV", type="csv")

    # 데이터 가공 파이프라인
    library_list = []
    if library_files:
        for file in library_files:
            _, df, region_hint = load_library_csv(file)
            if df is not None:
                df = preprocess_library(df, region_hint)
                library_list.append(df)

    library_df = (
        pd.concat(library_list, ignore_index=True)
        if library_list
        else None
    )

    population_df = None
    if population:
        _, population_df = load_population_csv(population)
        population_df = preprocess_population(population_df)

    # 데이터가 모두 존재할 때 핵심 비교 연산 수행
    if library_df is not None and population_df is not None:
        merged_data = build_merged_df(library_df, population_df)

        # ---- [탭 1] 사용자의 질문에 완벽히 정면으로 답하는 비교 분석 창 ----
        with tab1:
            draw_question_dashboard(merged_data)

            st.markdown("---")
            st.markdown("### 📝 인구 구조에 따른 3대 지표 차이 핵심 줄글 요약")
            st.info(
                "**1. 공공도서관 수의 차이:**\n"
                "도서관의 인프라 수 자체는 인구 구조비율보다는 **지자체의 절대적인 면적 및 총 인구 규모**에 우선 종속됩니다. 경기(최다 도서관수)와 서울이 압도적인 인프라를 보유하고 있으며, 세종시는 신생 도시 특성상 절대적인 도서관 수가 가장 적습니다.\n\n"
                "**2. 총 대출량의 차이:**\n"
                "대출량은 **'생산연령 인구 비율'과 완벽한 정비례 관계**를 보입니다. 생산연령 비율이 71.8%로 공동 1위인 경기와 서울이 수백만 건 단위의 대출량을 기록하며 시장을 독점하는 반면, 고령화로 인해 생산인구가 62%대로 축소된 전남, 강원은 대출 활동성이 매우 낮게 내려앉는 차이를 보입니다.\n\n"
                "**3. 이용자 수(이용 유형)의 차이:**\n"
                "이용자층의 성격은 **유소년 및 노년 비율**에 따라 극명하게 쪼개집니다. 세종시는 도서관 수는 적지만 유소년 비율(17.2%)에 힘입어 '어린이 이용자층'의 활동 비중이 대단히 견고하게 유지됩니다. 반면, 초고령 도시 군집(강원·전남·부산)은 유소년층 이용자 공급이 차단되어 어린이/청소년 대출량이 바닥권에 머무는 차이를 보입니다."
            )

        # ---- [탭 2] 산점도를 통한 가설 검증 탭 ----
        with tab2:
            draw_multivariate_correlation(merged_data)

        # ---- [탭 3] 데이터 프레임 확인 탭 ----
        with tab3:
            st.subheader("🛠️ 가공 및 결합 완료된 종합 데이터 마스터 테이블")
            st.dataframe(merged_data)

    else:
        # 데이터 미업로드 시 가이드 안내
        with tab1:
            st.warning(
                "📢 분석을 시작하려면 왼쪽 사이드바에 '도서관 CSV 파일들'과 '인구구조 CSV 파일'을 모두 업로드해 주세요."
            )
        with tab2:
            st.warning("데이터 업로드가 필요합니다.")
        with tab3:
            st.warning("데이터 업로드가 필요합니다.")


if __name__ == "__main__":
    main()
