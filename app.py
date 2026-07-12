import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import osmnx as ox
import networkx as nx
from pyproj import Transformer

# 1. 모바일 최적화 페이지 설정
st.set_page_config(layout="wide", page_title="SafeWay 고양")
st.title("🛡️ SafeWay 고양")

# 좌표 변환기 (중부원점 -> WGS84)
transformer = Transformer.from_crs("EPSG:5186", "EPSG:4326", always_xy=True)

@st.cache_data
def load_data():
    # 인코딩 설정 및 WGS84 변환 (필수)
    cctv = pd.read_csv('CCTV정보_경기고양시.csv', encoding='cp949')
    safe = pd.read_csv('안전비상벨위치현황(제공표준).csv', encoding='cp949')
    
    for df in [cctv, safe]:
        # 데이터를 한꺼번에 처리하여 메모리 효율화
        coords = [transformer.transform(x, y) for x, y in zip(df['경도'], df['위도'])]
        df['위도'] = [c[1] for c in coords]
        df['경도'] = [c[0] for c in coords]
    return cctv, safe

# 데이터 로드
try:
    cctv_df, safe_df = load_data()
except Exception as e:
    st.error("데이터 로드 실패. 파일명과 형식을 확인하세요.")
    st.stop()

# 2. 사이드바 옵션 (모바일에서 접근 용이)
view_mode = st.sidebar.radio("지도 모드", ["일반", "히트맵"])
time_mode = st.sidebar.select_slider("시간대", options=["낮", "밤"])

# 3. 지도 객체
tiles = "CartoDB dark_matter" if time_mode == "밤" else "OpenStreetMap"
m = folium.Map(location=[37.658, 126.832], zoom_start=13, tiles=tiles)

if view_mode == "히트맵":
    HeatMap(cctv_df[['위도', '경도']].values.tolist()).add_to(m)
else:
    # 성능 최적화를 위해 마커를 너무 많이 찍지 않도록 제어 가능 (샘플링 등)
    for _, row in cctv_df.iloc[:200].iterrows(): # 모바일 렉 방지를 위해 샘플링
        folium.CircleMarker([row['위도'], row['경도']], radius=3, color='blue').add_to(m)
    for _, row in safe_df.iloc[:200].iterrows():
        folium.CircleMarker([row['위도'], row['경도']], radius=3, color='red').add_to(m)

# 4. 경로 및 기능
start = st.text_input("출발지")
end = st.text_input("도착지")

if st.button("경로 찾기"):
    if start and end:
        with st.spinner('경로 계산 중...'):
            try:
                G = ox.graph_from_place("Goyang, South Korea", network_type="walk")
                s_node = ox.distance.nearest_nodes(G, *ox.geocode(start)[::-1])
                e_node = ox.distance.nearest_nodes(G, *ox.geocode(end)[::-1])
                route = nx.shortest_path(G, s_node, e_node, weight='length')
                m = ox.plot_route_folium(G, route, route_map=m)
                
                # 로드뷰
                coords = ox.geocode(end)
                st.markdown(f"[도착지 로드뷰](https://map.kakao.com/link/roadview/{coords[0]},{coords[1]})")
            except Exception as e:
                st.error("경로 탐색 오류 (지명 확인 필요)")
    else:
        st.warning("입력값이 없습니다.")

st_folium(m, width=350, height=400) # 모바일 폭에 맞춤

# 5. 신고
if st.button("🚨 경찰 신고(112)"):
    st.link_button("전화 걸기", "tel:112")
