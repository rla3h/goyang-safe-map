import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import folium_static
import osmnx as ox
import networkx as nx
import math

# 1. 페이지 설정
st.set_page_config(page_title="SafeWay 고양", page_icon="🛡️", layout="wide")

# 2. 데이터 로드
@st.cache_data
def load_data():
    # 파일 이름을 정확히 매칭했습니다.
    cctv_df = pd.read_csv('data/CCTV정보_경기고양시.csv', encoding='cp949')
    bell_df = pd.read_csv('data/안전비상벨위치현황(제공표준).csv', encoding='cp949')
    return cctv_df, bell_df

cctv_data, bell_data = load_data()

# 3. 사이드바 구성
st.sidebar.title("🛡️ SafeWay 설정")
start_name = st.sidebar.text_input("출발지 입력", "고양시청")
end_name = st.sidebar.text_input("목적지 입력", "원당역")
time_mode = st.sidebar.radio("시간대 선택", ["낮", "밤"])
show_heatmap = st.sidebar.checkbox("🔥 CCTV 히트맵 표시", value=True)

st.sidebar.markdown(
    """<a href="tel:112" style="display: block; text-align: center; background-color: #ff4b4b; color: white; padding: 15px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 20px;">🚨 112 긴급 신고</a>""", 
    unsafe_allow_html=True
)

# 4. 경로 탐색 알고리즘
def find_safe_path(start_name, end_name, is_night):
    alpha = 3.0 if is_night else 1.0
    G = ox.graph_from_place("Goyang-si, South Korea", network_type="walk")
    
    start_lat, start_lon = ox.geocode(start_name)
    end_lat, end_lon = ox.geocode(end_name)
    
    start_node = ox.nearest_nodes(G, start_lon, start_lat)
    end_node = ox.nearest_nodes(G, end_lon, end_lat)

    # CCTV와 비상벨 데이터를 합쳐서 안전 포인트 구성
    safe_points = list(zip(cctv_data['WGS84위도'], cctv_data['WGS84경도'])) + list(zip(bell_data['위도'], bell_data['경도']))

    for u, v, k, data in G.edges(keys=True, data=True):
        length = data.get('length', 50)
        mid_lat = (G.nodes[u]['y'] + G.nodes[v]['y']) / 2
        mid_lon = (G.nodes[u]['x'] + G.nodes[v]['x']) / 2
        
        safe_count = sum(1 for lat, lon in safe_points if math.hypot(lat - mid_lat, lon - mid_lon) < 0.001)
        data['safe_cost'] = length + (alpha / (1.0 + safe_count))

    path = nx.astar_path(G, start_node, end_node, weight='safe_cost')
    return [[G.nodes[node]['y'], G.nodes[node]['x']] for node in path]

# 5. 경로 검색
if st.sidebar.button("경로 검색"):
    with st.spinner('안전 경로 계산 중...'):
        try:
            path = find_safe_path(start_name, end_name, time_mode == "밤")
            st.session_state.path_points = path
            st.success("경로 계산 완료!")
        except Exception as e:
            st.error(f"경로 계산 실패: {e}")

# 6. 지도 렌더링
st.title("🛡️ SafeWay 고양")

def render_map():
    center = st.session_state.path_points[0] if 'path_points' in st.session_state else [37.6584, 126.8320]
    m = folium.Map(location=center, zoom_start=15, tiles="CartoDB dark_matter" if time_mode == "밤" else "CartoDB positron")
    
    if show_heatmap:
        heat_data = [[row['WGS84위도'], row['WGS84경도']] for _, row in cctv_data.iterrows()]
        HeatMap(heat_data, radius=15).add_to(m)
    
    # 비상벨 마커 추가
    for _, row in bell_data.iterrows():
        folium.CircleMarker([row['위도'], row['경도']], radius=3, color="red", popup="비상벨").add_to(m)
    
    if 'path_points' in st.session_state:
        folium.PolyLine(st.session_state.path_points, color="#00ffcc" if time_mode == "밤" else "blue", weight=6).add_to(m)
        folium.Marker(st.session_state.path_points[0], icon=folium.Icon(color="green", icon="play")).add_to(m)
        folium.Marker(st.session_state.path_points[-1], icon=folium.Icon(color="red", icon="flag")).add_to(m)
        
    folium_static(m, width=1000, height=700)

render_map()