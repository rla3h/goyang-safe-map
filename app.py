import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import osmnx as ox
import networkx as nx

# 1. 페이지 설정 (모바일 최적화)
st.set_page_config(layout="centered", page_title="SafeWay 고양")

st.title("🛡️ SafeWay 고양")
st.subheader("안전한 경로 탐색 서비스")

# 2. 데이터 불러오기 (캐싱 적용)
@st.cache_data
def load_data():
    cctv_df = pd.read_csv('CCTV정보_경기고양시.csv', encoding='cp949')
    safe_df = pd.read_csv('안전비상벨위치현황(제공표준).csv', encoding='cp949')
    return cctv_df, safe_df

cctv_df, safe_df = load_data()

# 3. 지도 생성 및 마커 추가
m = folium.Map(location=[37.658, 126.832], zoom_start=13)

# CCTV 마커
for _, row in cctv_df.iterrows():
    folium.Marker([row['WGS84위도'], row['WGS84경도']], icon=folium.Icon(color='blue', icon='camera')).add_to(m)

# 안전벨 마커
for _, row in safe_df.iterrows():
    folium.Marker([row['위도'], row['경도']], icon=folium.Icon(color='red', icon='bell')).add_to(m)

# 4. 경로 탐색 함수
def get_route(start_loc, end_loc):
    try:
        # 고양시 지역 그래프 생성
        G = ox.graph_from_place("Goyang, South Korea", network_type="walk")
        
        # 주소 또는 좌표를 기반으로 가장 가까운 노드 찾기
        start_node = ox.distance.nearest_nodes(G, start_loc[1], start_loc[0])
        end_node = ox.distance.nearest_nodes(G, end_loc[1], end_loc[0])
        
        # 최단 경로 계산
        route = nx.shortest_path(G, start_node, end_node, weight='length')
        return route, G
    except Exception as e:
        return None, None

# 5. 사용자 입력
start_input = st.text_input("출발지 좌표 (위도, 경도) 예: 37.67, 126.77")
end_input = st.text_input("도착지 좌표 (위도, 경도) 예: 37.67, 126.75")

if st.button("경로 찾기"):
    try:
        start_coords = [float(x) for x in start_input.split(',')]
        end_coords = [float(x) for x in end_input.split(',')]
        
        route, G = get_route(start_coords, end_coords)
        
        if route:
            route_map = ox.plot_route_folium(G, route, route_map=m)
            st_folium(route_map, width=700, height=500)
        else:
            st.error("경로 계산 실패: 노드를 찾을 수 없습니다.")
    except Exception as e:
        st.error(f"입력 오류: {e}")
else:
    # 경로 찾기 전 초기 지도 표시
    st_folium(m, width=700, height=500)
