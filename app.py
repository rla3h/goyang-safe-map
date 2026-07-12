import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import osmnx as ox
import networkx as nx

# 1. 페이지 설정
st.set_page_config(layout="centered", page_title="SafeWay 고양")
st.title("🛡️ SafeWay 고양")

@st.cache_data
def load_data():
    cctv = pd.read_csv('CCTV정보_경기고양시.csv', encoding='cp949')
    safe = pd.read_csv('안전비상벨위치현황(제공표준).csv', encoding='cp949')
    return cctv, safe

cctv_df, safe_df = load_data()

# 2. 사이드바 설정
st.sidebar.header("설정")
view_mode = st.sidebar.radio("지도 모드", ["일반", "히트맵"])
time_mode = st.sidebar.select_slider("시간대", options=["낮", "밤"])

# 3. 지도 객체 생성
tiles = "CartoDB dark_matter" if time_mode == "밤" else "OpenStreetMap"
m = folium.Map(location=[37.658, 126.832], zoom_start=13, tiles=tiles)

# 4. 모드별 데이터 표시 (제공해주신 컬럼명 적용)
if view_mode == "히트맵":
    # CCTV는 'WGS84위도', 'WGS84경도' 사용
    heat_data = cctv_df[['WGS84위도', 'WGS84경도']].values.tolist()
    HeatMap(heat_data).add_to(m)
else:
    # CCTV 마커
    for _, row in cctv_df.iterrows():
        folium.Marker([row['WGS84위도'], row['WGS84경도']], icon=folium.Icon(color='blue', icon='camera')).add_to(m)
    # 비상벨 마커
    for _, row in safe_df.iterrows():
        folium.Marker([row['위도'], row['경도']], icon=folium.Icon(color='red', icon='bell')).add_to(m)

# 5. 경로 탐색 및 로드뷰 기능
start_loc = st.text_input("출발지 입력")
end_loc = st.text_input("도착지 입력")

if st.button("경로 찾기"):
    try:
        G = ox.graph_from_place("Goyang, South Korea", network_type="walk")
        start_node = ox.distance.nearest_nodes(G, *ox.geocode(start_loc)[::-1])
        end_node = ox.distance.nearest_nodes(G, *ox.geocode(end_loc)[::-1])
        route = nx.shortest_path(G, start_node, end_node, weight='length')
        m = ox.plot_route_folium(G, route, route_map=m)
        
        # 카카오 로드뷰
        coords = ox.geocode(end_loc)
        kakao_url = f"https://map.kakao.com/link/roadview/{coords[0]},{coords[1]}"
        st.markdown(f"📍 [도착지 주변 로드뷰 보기]({kakao_url})", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"경로 탐색 실패: {e}")

st_folium(m, width=700, height=500)

# 6. 경찰 신고 버튼
if st.button("🚨 112 경찰 신고하기"):
    st.markdown("[전화걸기](tel:112)")
