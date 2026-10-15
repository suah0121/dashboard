import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정 및 데이터 로딩 (캐싱 적용)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="동네별 인구 피라미드",
    page_icon="👨‍👩‍👧‍👦",
    layout="wide"
)

@st.cache_data
def load_data():
    # 데이터 출처 URL (ZIP 압축 파일이지만 pandas가 직접 로드)
    url = "https://raw.githubusercontent.com/suah0121/dashboard/main/1.zip"
    df = pd.read_csv(url, encoding="utf-8")
    
    # 데이터에 존재하는 연도 중 가장 최신 연도 선택
    latest_year = df["연도"].max()
    df_latest = df[df["연도"] == latest_year].copy()
    
    return df_latest, latest_year

# 데이터 불러오기
try:
    df, latest_year = load_data()
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# -----------------------------------------------------------------------------
# 2. 헤더 및 데이터 필터링 (시도 -> 시군구 -> 동)
# -----------------------------------------------------------------------------
st.title("👨‍👩‍👧‍👦 우리 동네 인구 피라미드")
st.caption(f"가장 최신 데이터({latest_year}년 기준)를 바탕으로 지역별 나이·성별 인구 구조를 확인합니다.")

# 드롭다운 컬럼 배치
col1, col2, col3 = st.columns(3)

with col1:
    sido_list = sorted(df["시도"].dropna().unique())
    selected_sido = st.selectbox("1. 시·도 선택", sido_list)

# 선택한 시·도에 해당하는 시·군·구 추출
df_sido = df[df["시도"] == selected_sido]

with col2:
    sigungu_list = sorted(df_sido["시군구"].dropna().unique())
    selected_sigungu = st.selectbox("2. 시·군·구 선택", sigungu_list)

# 선택한 시·군·구에 해당하는 동 추출
df_sigungu = df_sido[df_sido["시군구"] == selected_sigungu]

with col3:
    dong_list = sorted(df_sigungu["동"].dropna().unique())
    selected_dong = st.selectbox("3. 읍·면·동 선택", dong_list)

# -----------------------------------------------------------------------------
# 3. 선택한 동네의 인구 데이터 추출 및 지표 계산
# -----------------------------------------------------------------------------
# 최종 선택된 1개 행 추출
target_row = df_sigungu[df_sigungu["동"] == selected_dong].iloc[0]

# 0세부터 100세 이상까지 연령 목록 만들기
age_labels = [f"{i}세" for i in range(100)] + ["100세 이상"]

male_pop = []
female_pop = []

# 각 연령별 남/여 인구수 수집
for age in age_labels:
    male_pop.append(target_row[f"남_{age}"])
    female_pop.append(target_row[f"여_{age}"])

# 연령별 총 인구수 배열 (남+여)
total_pop_by_age = [m + f for m, f in zip(male_pop, female_pop)]

# 1) 총인구 계산
total_pop = sum(total_pop_by_age)

# 2) 평균연령 계산 (100세 이상은 100세로 가중치 적용)
if total_pop > 0:
    weighted_age_sum = sum(i * total_pop_by_age[i] for i in range(100)) + (100 * total_pop_by_age[100])
    avg_age = weighted_age_sum / total_pop
else:
    avg_age = 0.0

# 3) 고령화율(65세 이상 비율) 및 유소년 비율(14세 이하 비율) 계산
elderly_pop = sum(total_pop_by_age[65:])
elderly_ratio = (elderly_pop / total_pop * 100) if total_pop > 0 else 0.0

child_pop = sum(total_pop_by_age[:15])
child_ratio = (child_pop / total_pop * 100) if total_pop > 0 else 0.0

# -----------------------------------------------------------------------------
# 4. 상단 지표 카드 3개 표시 (그래프 위)
# -----------------------------------------------------------------------------
st.write("---")

m1, m2, m3 = st.columns(3)

# 1번째 카드: 총인구
m1.metric(label="👥 총인구", value=f"{total_pop:,} 명")

# 2번째 카드: 평균연령
m2.metric(label="🎂 평균연령", value=f"{avg_age:.1f} 세")

# 3번째 카드: 고령화율 (20% 이상 시 경고 문구 추가)
if elderly_ratio >= 20.0:
    m3.metric(
        label="👵 고령화율 (65세 이상)",
        value=f"{elderly_ratio:.1f} %",
        delta="⚠️ 초고령사회 (20% 이상)",
        delta_color="inverse"
    )
else:
    m3.metric(
        label="👵 고령화율 (65세 이상)",
        value=f"{elderly_ratio:.1f} %"
    )

st.write("---")

# -----------------------------------------------------------------------------
# 5. Plotly를 활용한 인구 피라미드 시각화
# -----------------------------------------------------------------------------
fig = go.Figure()

# 남자 막대 그래프 (음수 값으로 처리하여 왼쪽에 위치)
fig.add_trace(go.Bar(
    y=age_labels,
    x=[-val for val in male_pop],
    name="남자",
    orientation="h",
    marker=dict(color="#6baed6"),  # 부드러운 블루 톤
    hovertemplate="%{y} 남자 인구: %{customdata:,}명<extra></extra>",
    customdata=male_pop  # 원래 양수 값을 마우스 호버에 표시
))

# 여자 막대 그래프 (양수 값으로 처리하여 오른쪽에 위치)
fig.add_trace(go.Bar(
    y=age_labels,
    x=female_pop,
    name="여자",
    orientation="h",
    marker=dict(color="#f768a1"),  # 부드러운 핑크 톤
    hovertemplate="%{y} 여자 인구: %{x:,}명<extra></extra>"
))

# 그래프 레이아웃 설정
fig.update_layout(
    title=dict(
        text=f"📍 {selected_sido} {selected_sigungu} {selected_dong} 연령별 인구 피라미드",
        font=dict(size=18)
    ),
    barmode="overlay",
    bargap=0.1,
    height=800,
    margin=dict(l=50, r=50, t=80, b=50),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="center",
        x=0.5
    ),
    # 세로축 설정 (0세가 아래, 100세 이상이 위로 순서 고정)
    yaxis=dict(
        type="category",
        categoryorder="array",
        categoryarray=age_labels,  # 0세부터 100세 이상까지 순서대로 명시적 배정
        dtick=5,  # 눈금을 5세 단위로 표시하여 가독성 확보
        title="연령"
    ),
    # 가로축 설정 (음수로 표시된 남자 눈금을 양수로 변경)
    xaxis=dict(
        title="인구수 (명)",
        tickformat=",d"
    )
)

# 실제 데이터 최고 인구수에 맞춰 가로축 범위 자동 계산 (대칭)
max_val = max(max(male_pop), max(female_pop)) * 1.15 if total_pop > 0 else 100
fig.update_xaxes(range=[-max_val, max_val])

# 그래프 화면 출력
st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------------------------
# 6. 피라미드 하단 자동 한 줄 설명
# -----------------------------------------------------------------------------
# 아이(0~14세) 비율과 어르신(65세 이상) 비율 비교하여 한 줄 설명 생성
if child_ratio > elderly_ratio:
    desc = f"💡 **{selected_dong}**은(는) 아이(0~14세, {child_ratio:.1f}%)가 어르신(65세 이상, {elderly_ratio:.1f}%)보다 많은 상대적으로 **젊고 활기찬 동네**입니다."
elif elderly_ratio >= 20.0:
    desc = f"💡 **{selected_dong}**은(는) 어르신(65세 이상, {elderly_ratio:.1f}%) 비율이 높은 **초고령 동네**로, 아이(0~14세, {child_ratio:.1f}%)에 비해 어르신이 훨씬 많은 편입니다."
else:
    desc = f"💡 **{selected_dong}**은(는) 어르신(65세 이상, {elderly_ratio:.1f}%) 비율이 아이(0~14세, {child_ratio:.1f}%)보다 높아 **어르신이 조금 더 많은 편**인 동네입니다."

st.info(desc)
