"""
Page 1: Bengaluru Road Network Explorer.
Ambulance Route Optimization — Bengaluru.

Interactive GIS road network explorer for Bengaluru:
- Level 1: Macro Arterial Directed Graph G = (V, E) with real OSM polylines.
- Road classifications (IRC:106 Expressways, Arterials, Sub-Arterials, Collectors).
- One-way restrictions and directional flow visualization.
- Hospital proximity radius filtering (inspecting road networks around emergency facilities).
- Topological Centrality & Critical Arterial Hubs.
"""

import streamlit as st
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional

from components.ui_helpers import (
    load_custom_css,
    render_header,
    render_workflow_navigation,
    render_metric,
    get_plotly_layout,
    load_all_datasets,
    load_road_networks,
    load_gis_network,
    load_hospital_data,
    load_ambulance_router
)
try:
    from components.gis_map import (
        create_bengaluru_gis_map,
        render_gis_map_in_streamlit,
        haversine_distance_m
    )
except ImportError:
    from components.gis_map import (
        create_bengaluru_gis_map,
        render_gis_map_in_streamlit
    )
    from src.network.ambulance_graph import haversine_distance_m
from src.network.network_analyzer import NetworkAnalyzer

st.set_page_config(
    page_title="Road Network Explorer | Bengaluru GIS",
    page_icon="🗺️",
    layout="wide"
)
load_custom_css()

render_header(
    title="Bengaluru Road Network Explorer",
    subtitle="Directed Arterial Graph Geometry, IRC:106 Speed Limits, One-Way Constraints & Hospital Proximity",
    badge_text="GIS Topology & Graph Theory",
    current_page="pages/1_Road_Network_Explorer.py"
)

data = load_all_datasets()
builder, G_macro, G_micro = load_road_networks()
gis_mgr, roads_gis, df_nodes_gis = load_gis_network()
df_hospitals, df_connections = load_hospital_data()
router = load_ambulance_router()
G_di = router.graph_di

if "corridor" not in df_nodes_gis.columns:
    from src.network.graph_builder import map_police_station_to_corridor
    df_nodes_gis["corridor"] = df_nodes_gis.apply(
        lambda r: map_police_station_to_corridor(r.get("police_station", ""), r.get("name", "")),
        axis=1
    )
df_nodes = data["intersections"]

tab_map, tab_catalog, tab_metrics = st.tabs([
    "🌐 Interactive Road Network Map",
    "📑 Road Segment Catalog & Classifications",
    "📈 Topological Centrality & Arterial Hubs"
])

# TAB 1: INTERACTIVE ROAD NETWORK MAP
with tab_map:
    st.markdown("#### Metropolitan Directed Road Graph (OpenStreetMap Geometry)")
    st.caption("Inspect authentic street geometry polylines, signalized crossroads, directional rights, and emergency hospital access zones.")

    col_f1, col_f2, col_f3 = st.columns([1.2, 1.2, 1.2])
    
    # 1. Filter by Corridor
    corridor_list = ["All Corridors"] + sorted(list(df_nodes_gis["corridor"].dropna().unique()))
    sel_corr = col_f1.selectbox("Filter by Arterial Corridor:", corridor_list)

    # 2. Filter by Road Classification
    road_classes = ["All Road Classes", "Expressways & Flyovers (50 km/h)", "Major Arterials (40 km/h)", "Sub-Arterials (35 km/h)", "Collectors & Local (30 km/h)"]
    sel_class = col_f2.selectbox("Filter by Road Classification:", road_classes)

    # 3. Hospital Proximity Filter
    hosp_filter_mode = col_f3.selectbox(
        "Hospital Proximity Focus:",
        ["All Bengaluru", "Focus Near Victoria Hospital (Central)", "Focus Near Bowring Hospital (East)", "Focus Near St. John's Hospital (South-East)", "Focus Near Aster CMI (North)"]
    )

    # Filter logic
    filtered_roads = list(roads_gis)
    filtered_nodes_df = df_nodes_gis.copy()

    # Corridor filter
    if sel_corr != "All Corridors":
        filtered_nodes_df = filtered_nodes_df[filtered_nodes_df["corridor"] == sel_corr]
        sub_node_ids = set(filtered_nodes_df["intersection_id"])
        filtered_roads = [r for r in filtered_roads if r["from_node"] in sub_node_ids or r["to_node"] in sub_node_ids]

    # Classification filter
    if sel_class != "All Road Classes":
        if "50 km/h" in sel_class:
            filtered_roads = [r for r in filtered_roads if r.get("speed_kmh", 30) >= 50]
        elif "40 km/h" in sel_class:
            filtered_roads = [r for r in filtered_roads if r.get("speed_kmh", 30) == 40]
        elif "35 km/h" in sel_class:
            filtered_roads = [r for r in filtered_roads if r.get("speed_kmh", 30) == 35]
        else:
            filtered_roads = [r for r in filtered_roads if r.get("speed_kmh", 30) <= 30]

    # Hospital focus filter
    c_lat, c_lon, zoom_lvl = 12.9716, 77.5946, 12
    if hosp_filter_mode != "All Bengaluru":
        h_targets = {
            "Victoria": (12.9628, 77.5750),
            "Bowring": (12.9835, 77.6030),
            "St. John's": (12.9345, 77.6200),
            "Aster CMI": (13.0550, 77.5920)
        }
        for k, (tlat, tlon) in h_targets.items():
            if k in hosp_filter_mode:
                c_lat, c_lon, zoom_lvl = tlat, tlon, 14
                # Filter road links within 3.5km of target
                nearby_roads = []
                for r in filtered_roads:
                    u_lat, u_lon = r.get("u_lat"), r.get("u_lon")
                    if u_lat and u_lon:
                        if haversine_distance_m(tlat, tlon, u_lat, u_lon) <= 3500:
                            nearby_roads.append(r)
                if nearby_roads:
                    filtered_roads = nearby_roads
                break
    elif not filtered_nodes_df.empty and sel_corr != "All Corridors":
        c_lat = float(filtered_nodes_df["latitude"].mean())
        c_lon = float(filtered_nodes_df["longitude"].mean())
        zoom_lvl = 13

    # KPI Metrics Row
    k1, k2, k3, k4 = st.columns(4)
    tot_km = sum(r.get("length_m", 500.0) for r in filtered_roads) / 1000.0
    verified_r = sum(1 for r in filtered_roads if r.get("verification_status") == "VERIFIED")
    render_metric(k1, "Displayed Intersections", f"{len(filtered_nodes_df)} Nodes", "BTP Signalized Crossroads", "normal")
    render_metric(k2, "Directed Road Links", f"{len(filtered_roads)} Edges", "IRC:106 Arterial Segments", "normal")
    render_metric(k3, "Total Roadway Span", f"{tot_km:.1f} km", "Centerline Polyline Span", "green")
    render_metric(k4, "Verified Curved Centerlines", f"{verified_r} Links", "Authentic OSM Geometries", "green" if verified_r > 0 else "normal")

    st.markdown("---")

    # Render Reusable Folium GIS Map
    m_macro = create_bengaluru_gis_map(
        center_lat=c_lat,
        center_lon=c_lon,
        zoom_start=zoom_lvl,
        intersections=filtered_nodes_df.to_dict(orient="records"),
        roads=filtered_roads,
        show_legend=True
    )
    render_gis_map_in_streamlit(m_macro, height=620, key=f"road_explorer_{sel_corr}_{sel_class}_{hosp_filter_mode}")

# TAB 2: ROAD SEGMENT CATALOG & CLASSIFICATIONS
with tab_catalog:
    st.markdown("#### Searchable Arterial Road Links Catalog")
    st.caption("Complete tabular inventory of the 804 directed road segments, IRC:106 speeds, physical lengths, and capacities.")

    search_txt = st.text_input("🔍 Search Road Name or Node ID:", "")
    
    catalog_records = []
    for r in roads_gis:
        rname = r.get("road_name", "Arterial Link")
        u_name = r.get("from_name", r.get("from_node"))
        v_name = r.get("to_name", r.get("to_node"))
        speed = r.get("speed_kmh", 30)

        # Classification label
        if speed >= 50:
            cls_lbl = "Expressway / Flyover"
        elif speed >= 40:
            cls_lbl = "Major Arterial"
        elif speed >= 35:
            cls_lbl = "Sub-Arterial"
        else:
            cls_lbl = "Collector Link"

        if search_txt:
            st_low = search_txt.lower()
            if not (st_low in str(rname).lower() or st_low in str(u_name).lower() or st_low in str(v_name).lower()):
                continue

        catalog_records.append({
            "Edge ID": r.get("edge_id"),
            "Road Name": rname,
            "Classification": cls_lbl,
            "From Junction": u_name,
            "To Junction": v_name,
            "Length (m)": f"{r.get('length_m', 500):,.0f} m",
            "Speed Limit": f"{speed} km/h",
            "Lanes": r.get("lanes", 2),
            "Capacity (PCU/h)": f"{r.get('capacity', 2400):,}",
            "Geometry Source": r.get("geometry_source", "OSM_WAY_CENTERLINE")
        })

    df_cat = pd.DataFrame(catalog_records)
    st.write(f"Showing **{len(df_cat)}** of {len(roads_gis)} directed road links:")
    st.dataframe(df_cat, width="stretch", height=450, hide_index=True)

    csv_roads = df_cat.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download Road Network Catalog (CSV)",
        data=csv_roads,
        file_name="bengaluru_road_network_catalog.csv",
        mime="text/csv"
    )

# TAB 3: TOPOLOGICAL CENTRALITY & HUBS
with tab_metrics:
    st.markdown("#### Network Topology & Arterial Hub Analysis")
    analyzer = NetworkAnalyzer(G_macro)
    metrics = analyzer.compute_all_metrics()

    m_c1, m_c2, m_c3, m_c4 = st.columns(4)
    m_c1.metric("Network Density", f"{metrics.get('density', 0.0):.4f}")
    m_c2.metric("Average Clustering", f"{metrics.get('average_clustering', 0.0):.4f}")
    m_c3.metric("Strongly Connected Components", metrics.get("num_strongly_connected_components", 1))
    m_c4.metric("Weakly Connected Components", metrics.get("num_weakly_connected_components", 1))

    st.markdown("---")
    st.markdown("##### Top 10 Critical Arterial Hubs by Betweenness Centrality")
    st.caption("Intersections with highest betweenness centrality carry maximum routing influence and are vulnerable to network-wide bottleneck propagation.")

    betweenness = nx.betweenness_centrality(G_macro)
    top_hubs = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:10]

    hub_records = []
    for node, score in top_hubs:
        d = G_macro.nodes[node]
        hub_records.append({
            "Intersection ID": node,
            "Intersection Name": d.get("name", node),
            "Corridor": d.get("corridor", "N/A"),
            "Betweenness Centrality": round(score, 5),
            "Degree": G_macro.degree(node),
            "Cycle Length (s)": d.get("cycle_time_sec", 120)
        })
    st.dataframe(pd.DataFrame(hub_records), width="stretch", hide_index=True)

render_workflow_navigation(
    prev_page="app.py",
    prev_label="Dashboard",
    next_page="pages/2_Hospital_Finder.py",
    next_label="02. Hospital Finder"
)
