import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import osmnx as ox
import networkx as nx
from pyproj import Transformer
import os

# 1. 페이지 설정
st.set_page_config(layout="centered", page_title="SafeWay 고양")
st.title("🛡️ SafeWay 고양")

# 좌표 변환 설정 (중부원점 EPSG:5186 -> WGS84 EPSG:4326)
transformer = Transformer.from_crs("EPSG:5186", "EPSG:4326", always_xy=True)

# 2. 데이터 로드 및 좌표 변환
@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cctv_path = os.path.join(base_dir, 'CCTV정보_경기고양시.csv')
    safe_path = os.path.join(base_dir, '안전비상벨위치현황(제공표준).csv')
    
    if os.path.exists(cctv_path) and os.path.exists(safe_path):
        cctv_df = pd.read_csv(cctv_path, encoding='cp949')
        safe_df = pd.read_csv(safe_path, encoding='cp949')
        
        # WGS84로 좌표 변환 및 덮어쓰기
        for df in [cctv_df, safe_df]:
            coords = [transformer.transform(x, y) for x, y in zip(df['경도'], df['위도'])]
            df['위도'] = [c[1] for c in coords]
            df['경도'] = [c[0] for c in coords]
        return cctv_df, safe_df
    return pd.DataFrame(), pd.DataFrame()

cctv_df, safe_df = load_data()

# 3. 사이드바 옵션
st.sidebar.header("설정")
view_mode = st.sidebar.radio("지도 모드", ["일반", "히트맵"])
time_mode = st.sidebar.select_slider("시간대 설정", options=["낮", "밤"])

# 4. 지도 생성 (시간대별 타일 설정)
tiles = "CartoDB dark_matter" if time_mode == "밤" else "OpenStreetMap"
m = folium.Map(location=[37.658, 126.832], zoom_start=13, tiles=tiles)

if not cctv_df.empty:
    if view_mode == "히트맵":
        heat_data = cctv_df[['위도', '경도']].values.tolist()
        HeatMap(heat_data).add_to(m)
    else:
        for _, row in cctv_df.iloc[:200].iterrows(): # 모바일 최적화를 위해 마커 수 제한
            folium.Marker([row['위도'], row['경도']], icon=folium.Icon(color='blue', icon='camera')).add_to(m)
        for _, row in safe_df.iloc[:200].iterrows():
            folium.Marker([row['위도'], row['경도']], icon=folium.Icon(color='red', icon='bell')).add_to(m)
else:
    st.warning("데이터 파일을 찾을 수 없습니다.")

# 5. 경로 탐색
start_loc = st.text_input("출발지 입력")
end_loc = st.text_input("도착지 입력")

if st.button("경로 찾기"):
    if start_loc and end_loc:
        try:
            G = ox.graph_from_place("Goyang, South Korea", network_type="walk")
            start_node = ox.distance.nearest_nodes(G, *ox.geocode(start_loc)[::-1])
            end_node = ox.distance.nearest_nodes(G, *ox.geocode(end_loc)[::-1])
            route = nx.shortest_path(G, start_node, end_node, weight='length')
            m = ox.plot_route_folium(G, route, route_map=m)
            
            # 카카오 로드뷰 기능
            end_coords = ox.geocode(end_loc)
            st.markdown(f"📍 [도착지 주변 로드뷰 보기](https://map.kakao.com/link/roadview/{end_coords[0]},{end_coords[1]})")
        except Exception as e:
            st.error(f"경로 탐색 실패: {e}")
    else:
        st.warning("출발지와 도착지를 입력해주세요.")

# 6. 지도 출력 및 경찰 신고 버튼
st_folium(m, width=700, height=500)

if st.button("🚨 112 경찰 신고하기"):
    st.markdown("[![전화걸기](https://img.shields.io/badge/112-경찰청_신고-red)](tel:112)")
