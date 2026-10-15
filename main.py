import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정 및 디자인 (따뜻한 톤 스타일링)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="동네별 인구 피라미드", page_icon="👨‍👩‍👧‍👦", layout="centered"
)

# 따뜻한 느낌을 주는 커스텀 CSS 적용
st.markdown(
    """
    <style>
    /* 배경색과 기본 글꼴 톤 설정 */
    .main {
        background-color: #FAF8F5;
    }
    /* 제목 스타일 */
    h1 {
        color: #5A3E2B;
        font-family: 'Pretendard', sans-serif;
    }
    /* 안내 문구 스타일 */
    .stMarkdown p {
        color: #6C5C53;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🏡 우리 동네 인구 피라미드")
st.write(
    "지역을 선택하면 선택한 동네의 **나이별 남녀 인구 구조**를 따뜻한 피라미드 그래프로 보여드립니다."
)


# -----------------------------------------------------------------------------
# 2. 데이터 로드 및 전처리 (캐싱을 적용하여 속도 향상)
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    # GitHub Raw 주소 (판다스로 바로 읽을 수 있는 URL)
    url = "https://raw.githubusercontent.com/suah0121/sootory/main/202609_202609_%EC%97%B0%EB%A0%B9%EB%B3%84%EC%9D%B8%EA%B5%AC%ED%98%84%ED%99%A9_%EC%9B%94%EA%B0%84%20(1).csv"

    # CSV 데이터 불러오기 (자동으로 압축 해제되어 읽힘)
    df = pd.read_csv(url)

    # 데이터에 존재하는 가장 최신 연도 필터링
    latest_year = df["연도"].max()
    df = df[df["연도"] == latest_year].copy()

    return df, latest_year


# 데이터 불러오기
try:
    df, latest_year = load_data()
    st.caption(f" 기준 연도: **{latest_year}년 데이터**")
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()


# -----------------------------------------------------------------------------
# 3. 드롭다운 메뉴 (시도 → 시군구 → 동 3단계 계층 구조)
# -----------------------------------------------------------------------------
st.subheader("📍 지역 선택")
col1, col2, col3 = st.columns(3)

with col1:
    sido_list = sorted(df["시도"].dropna().unique())
    selected_sido = st.selectbox("시·도", sido_list)

# 선택된 시·도에 해당하는 시·군·구 목록 추출
sigungu_df = df[df["시도"] == selected_sido]
sigungu_list = sorted(sigungu_df["시군구"].dropna().unique())

with col2:
    selected_sigungu = st.selectbox("시·군·구", sigungu_list)

# 선택된 시·군·구에 해당하는 동 목록 추출
dong_df = sigungu_df[sigungu_df["시군구"] == selected_sigungu]
dong_list = sorted(dong_df["동"].dropna().unique())

with col3:
    selected_dong = st.selectbox("읍·면·동", dong_list)


# -----------------------------------------------------------------------------
# 4. 선택된 지역 데이터 추출 및 가공
# -----------------------------------------------------------------------------
# 사용자가 최종 선택한 행 1개 가져오기
target_data = dong_df[dong_df["동"] == selected_dong].iloc[0]

# 연령대 라벨 정의 (0세, 1세, ..., 99세, 100세 이상)
# 0세부터 100세 이상까지 순서대로 정렬된 리스트입니다.
age_labels = [f"{i}세" for i in range(100)] + ["100세 이상"]

male_pop = []
female_pop = []

# 컬럼명 패턴('남_0세', '여_0세' 등)에 맞춰 인구수 값 읽기
for age in age_labels:
    male_col = f"남_{age}"
    female_col = f"여_{age}"

    # 데이터의 숫자에 쉼표(,)가 포함되어 있을 경우를 대비하여 처리
    m_val = target_data.get(male_col, 0)
    f_val = target_data.get(female_col, 0)

    if isinstance(m_val, str):
        m_val = int(m_val.replace(",", ""))
    if isinstance(f_val, str):
        f_val = int(f_val.replace(",", ""))

    male_pop.append(m_val)
    female_pop.append(f_val)

# 남성 인구수는 왼쪽 배치를 위해 음수로 변환
male_pop_neg = [-x for x in male_pop]


# -----------------------------------------------------------------------------
# 5. Plotly 가로 막대그래프(인구 피라미드) 생성
# -----------------------------------------------------------------------------
fig = go.Figure()

# [남성] 왼쪽 막대그래프 (따뜻한 인디고/블루 톤)
fig.add_trace(
    go.Bar(
        y=age_labels,
        x=male_pop_neg,
        name="남성",
        orientation="h",
        marker=dict(color="#5C7AEA"),
        # 마우스 호버 시 음수 기호를 떼고 실제 인구수로 표시
        hovertemplate="나이: %{y}<br>남성 인구: %{customdata:,}명<extra></extra>",
        customdata=male_pop,
    )
)

# [여성] 오른쪽 막대그래프 (따뜻한 코랄/살구 톤)
fig.add_trace(
    go.Bar(
        y=age_labels,
        x=female_pop,
        name="여성",
        orientation="h",
        marker=dict(color="#FF8E8F"),
        hovertemplate="나이: %{y}<br>여성 인구: %{x:,}명<extra></extra>",
    )
)

# -----------------------------------------------------------------------------
# 6. 세로축(y축) 및 전체 레이아웃 설정
# -----------------------------------------------------------------------------
# 최대 인구수를 계산하여 x축 대칭 범위를 설정
max_pop = max(max(male_pop), max(female_pop))
# 데이터가 전혀 없는 경우 대비
if max_pop == 0:
    max_pop = 100

fig.update_layout(
    title=dict(
        text=f"📊 {selected_sido} {selected_sigungu} {selected_dong} 인구 피라미드",
        font=dict(size=18, color="#4A3E3D"),
    ),
    barmode="overlay",  # 두 막대를 중심 기준으로 겹쳐서 배치
    bargap=0.1,  # 막대 간격
    paper_bgcolor="rgba(0,0,0,0)",  # 배경 투명 (스트림릿 테마와 조화)
    plot_bgcolor="rgba(0,0,0,0)",
    # X축 (가로축): 왼쪽(남)과 오른쪽(여)의 축 눈금을 모두 양수로 보이게 처리
    xaxis=dict(
        title="인구수 (명)",
        range=[-max_pop * 1.1, max_pop * 1.1],
        tickvals=[
            -int(max_pop * 0.8),
            -int(max_pop * 0.4),
            0,
            int(max_pop * 0.4),
            int(max_pop * 0.8),
        ],
        ticktext=[
            f"{int(max_pop * 0.8):,}",
            f"{int(max_pop * 0.4):,}",
            "0",
            f"{int(max_pop * 0.4):,}",
            f"{int(max_pop * 0.8):,}",
        ],
        showgrid=True,
        gridcolor="#EAE3D2",
    ),
    # Y축 (세로축): 나이 라벨을 '0세'부터 '100세 이상'까지 입력 순서 그대로 고정
    yaxis=dict(
        title="연령",
        type="category",  # 범주형으로 지정하여 정렬 왜곡 방지
        categoryorder="array",  # 라벨 배열 순서 지정
        categoryarray=age_labels,  # 맨 아래가 0세, 맨 위가 100세 이상
        showgrid=False,
        dtick=10,  # 10세 단위로 눈금 표시하여 깔끔하게 정렬
    ),
    legend=dict(x=0.85, y=1.0, backgroundcolor="rgba(255,255,255,0.6)"),
    height=700,
)

# 스트림릿 화면에 그래프 표시
st.plotly_chart(fig, use_container_width=True)
