"""
Page 3: Ambulance Route Optimizer.
Ambulance Route Optimization — Bengaluru.

Core Operations Research module implementing:
1. Minimum estimated travel-time Dijkstra shortest path optimization.
2. Signal-aware travel time optimization (Phase 4 Webster uniform delay).
3. Traffic congestion modeling (Phase 5 BPR volume-delay scenarios).
4. Shortest-distance benchmark comparison.
5. Alternative route generation via Yen's K-Shortest Loopless Paths Algorithm.
6. Seamless hospital driveway access delay modeling (+1.0 min gate clearance, 15 km/h driveway speed).
7. Interactive Folium GIS multi-layer cartography with turn-by-turn itinerary export.
"""

import os
import math
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional

from components.ui_helpers import (
    load_custom_css,
    render_header,
    render_metric,
    render_workflow_navigation,
    get_plotly_layout,
    load_all_datasets,
    load_gis_network,
    load_ambulance_router,
    load_hospital_data
)
try:
    from components.gis_map import (
        create_ambulance_route_map,
        render_gis_map_in_streamlit,
        calculate_bearing,
        bearing_to_cardinal,
        haversine_distance_m
    )
except ImportError:
    from components.gis_map import (
        create_ambulance_route_map,
        render_gis_map_in_streamlit,
        calculate_bearing,
        bearing_to_cardinal
    )
    from src.network.ambulance_graph import haversine_distance_m
from src.network.ambulance_router import (
    PROFILE_MINIMUM_TIME,
    PROFILE_SHORTEST_DISTANCE,
    PROFILE_TIME_PLUS_SIGNAL,
    PROFILE_MODERATE_CONGESTION,
    PROFILE_HEAVY_CONGESTION,
    PROFILE_COMBINED_TRAFFIC_SIGNAL,
    UnreachableDestinationError,
    HospitalNotFoundError
)

st.set_page_config(
    page_title="Ambulance Route Optimizer | Bengaluru GIS",
    page_icon="🚑",
    layout="wide"
)
load_custom_css()

render_header(
    title="Ambulance Route Optimizer",
    subtitle="Minimum Travel-Time Dijkstra Solver with Alternative Path Modeling (Yen's Algorithm) & Hospital Access Snapping",
    badge_text="Operations Research — Emergency Dispatch",
    current_page="pages/3_Ambulance_Route_Optimizer.py"
)

# 1. Load Cached System Data
data = load_all_datasets()
gis_mgr, roads_gis, df_nodes_gis = load_gis_network()
df_hospitals, df_connections = load_hospital_data()
router = load_ambulance_router()
# Defensive compatibility for active Streamlit cache sessions
if not hasattr(router, "find_hospital_route") and hasattr(router, "route_to_hospital"):
    router.find_hospital_route = router.route_to_hospital
G_di = router.graph_di

# Expandable Academic OR Mathematical Formulation
with st.expander("📐 Mathematical Formulation — Binary Shortest Path IP & Yen's K-Shortest Loopless Paths", expanded=False):
    st.latex(r"""
    \begin{aligned}
    \text{Minimize } & Z = \sum_{(i,j) \in E} t_{ij} \cdot y_{ij} \\
    \text{Subject to: } & \sum_{j:(i,j) \in E} y_{ij} - \sum_{j:(j,i) \in E} y_{ji} = 
    \begin{cases}
    1 & \text{if } i = s \text{ (Ambulance Origin)} \\
    -1 & \text{if } i = t \text{ (Hospital Snapped Junction)} \\
    0 & \forall i \in V \setminus \{s, t\} \text{ (Transshipment Junction)}
    \end{cases} \\
    & y_{ij} \in \{0, 1\} \quad \forall (i, j) \in E, \quad t_{ij} = \frac{d_{ij}}{v_{ij}} \times 3600 \text{ seconds}
    \end{aligned}
    """)
    st.markdown("""
    **Formulation Attributes:**
    - **Primary Objective:** Minimum travel time traversing the directed arterial graph $G=(V, E)$.
    - **Urban Speed Calibration:** Speed $v_{ij}$ strictly calibrated via Indian Road Congress (IRC:106-1990) standards ($50\\text{ km/h}$ Expressways, $40\\text{ km/h}$ Major Arterials, $35\\text{ km/h}$ Sub-Arterials, $30\\text{ km/h}$ Collectors).
    - **Hospital Driveway Model:** Total emergency transit time $T_{\\text{total}} = T_{\\text{road}} + t_{\\text{driveway}}$, where $t_{\\text{driveway}} = (d_{\\text{snap}} / 15\\text{ km/h}) + 1.0\\text{ min}$ campus gate clearance.
    - **Alternative Routes:** Generated via **Yen's K-Shortest Loopless Paths Algorithm**, preventing circular loops through spur-node deviation.
    """)

# Preset Strategic Dispatch Hubs
PRESET_ORIGINS = {
    "INT_001_RAJARAJESHWARI_JUNCTION": "Majestic / KSR Railway Central Dispatch",
    "INT_006_RAJALAXMIKALYANAMANTAPA": "Koramangala 80ft Road Police Outpost",
    "INT_068_MADIWALACHECKPOST_JUNCTIO": "Silk Board Arterial Hub (Hosur / ORR)",
    "INT_010_B_M_SHRI_CMH_100FT_ROAD_J": "Indiranagar CMH Metro Station Station",
    "INT_052_PRASANNA_JUNCTION": "Magadi Road Toll Gate Sector Hub",
    "INT_002_SATELLITEBUSSTAND_JUNCTIO": "Mysore Road Satellite Bus Terminal Hub"
}

st.markdown("### 🚑 Emergency Route Configuration & Dispatch Parameters")

# State management for handoffs
default_dest_type = st.session_state.get("destination_type", "HOSPITAL")
dest_type = st.radio(
    "Destination Mode:",
    ["Hospital Emergency Facility (Recommended)", "Direct Road Intersection Node"],
    index=0 if default_dest_type == "HOSPITAL" else 1,
    horizontal=True
)

col_cfg1, col_cfg2, col_cfg3 = st.columns([1.2, 1.4, 1.2])

sorted_nodes = sorted(list(G_di.nodes()))
node_name_map = {n: f"{n} — {G_di.nodes[n].get('name', 'Junction')}" for n in sorted_nodes}

with col_cfg1:
    st.markdown("#### 1. Ambulance Origin Station")
    preset_opt = st.selectbox(
        "Quick Origin Presets:",
        ["Custom Junction Selector"] + list(PRESET_ORIGINS.values())
    )
    
    if preset_opt != "Custom Junction Selector":
        matched_orig = [k for k, v in PRESET_ORIGINS.items() if v == preset_opt][0]
        selected_origin_node = matched_orig
        st.caption(f"📍 Station: `[{selected_origin_node}]` {G_di.nodes[selected_origin_node].get('name', '')}")
    else:
        saved_orig = st.session_state.get("origin_node_id", sorted_nodes[0])
        default_orig_idx = sorted_nodes.index(saved_orig) if saved_orig in sorted_nodes else 0
        selected_origin_node = st.selectbox(
            "Select Origin Intersection:",
            sorted_nodes,
            index=default_orig_idx,
            format_func=lambda x: node_name_map.get(x, x)
        )

with col_cfg2:
    st.markdown("#### 2. Destination Facility / Node")
    selected_dest_hospital_id = None
    selected_dest_node = None
    hospital_rec = None

    if "Hospital" in dest_type:
        hosp_ids = df_hospitals["hospital_id"].tolist()
        def _format_hosp_label(row: pd.Series) -> str:
            addr = row.get("address")
            addr_clean = f" — {str(addr)[:28]}" if pd.notna(addr) and str(addr).strip() and str(addr).lower() != "nan" else ""
            return f"{row['hospital_name']} ({row['verification_status']}){addr_clean}"

        hosp_name_dict = {
            r["hospital_id"]: _format_hosp_label(r)
            for _, r in df_hospitals.iterrows()
        }
        
        saved_hid = st.session_state.get("target_hospital_id", "BLR_HOSP_0052")
        default_idx = hosp_ids.index(saved_hid) if saved_hid in hosp_ids else 0
        
        selected_dest_hospital_id = st.selectbox(
            "Select Receiving Emergency Hospital:",
            hosp_ids,
            index=default_idx,
            format_func=lambda x: hosp_name_dict.get(x, x)
        )

        h_matches = df_hospitals[df_hospitals["hospital_id"] == selected_dest_hospital_id]
        if not h_matches.empty:
            hospital_rec = h_matches.iloc[0].to_dict()
            c_matches = df_connections[df_connections["hospital_id"] == selected_dest_hospital_id]
            if not c_matches.empty:
                c_row = c_matches.iloc[0].to_dict()
                hospital_rec.update(c_row)
                selected_dest_node = c_row.get("nearest_intersection_id")

            v_badge = hospital_rec.get("verification_status", "HOSPITAL_EMERGENCY_UNVERIFIED")
            s_dist = hospital_rec.get("snapping_distance_m", 0.0)
            d_time = hospital_rec.get("estimated_access_time_min", 1.0)
            st.caption(f"🏥 **{hospital_rec.get('hospital_name')}** ({v_badge}) | Snapped: **{hospital_rec.get('nearest_road_name', 'Link')}** ({s_dist:,.0f} m, +{d_time} min)")
    else:
        default_d = sorted_nodes[-1]
        selected_dest_node = st.selectbox(
            "Select Destination Intersection:",
            sorted_nodes,
            index=sorted_nodes.index(default_d),
            format_func=lambda x: node_name_map.get(x, x)
        )

with col_cfg3:
    st.markdown("#### 3. Solver Objective & Alternatives")
    opt_profile = st.selectbox(
        "Routing Objective:",
        [
            PROFILE_COMBINED_TRAFFIC_SIGNAL,
            PROFILE_HEAVY_CONGESTION,
            PROFILE_MODERATE_CONGESTION,
            PROFILE_TIME_PLUS_SIGNAL,
            PROFILE_MINIMUM_TIME,
            PROFILE_SHORTEST_DISTANCE
        ],
        format_func=lambda x: (
            "🚨 Combined Congestion + Signal Delay (Phase 5)" if x == PROFILE_COMBINED_TRAFFIC_SIGNAL
            else ("🚗 Heavy Congestion Peak Hour (TomTom Benchmark)" if x == PROFILE_HEAVY_CONGESTION
            else ("🟡 Moderate Congestion Inter-Peak" if x == PROFILE_MODERATE_CONGESTION
            else ("🚦 Signal-Aware Road Time (Phase 4 Webster Delay)" if x == PROFILE_TIME_PLUS_SIGNAL
            else ("⚡ Baseline Free-Flow Road Time (IRC:106)" if x == PROFILE_MINIMUM_TIME
            else "📏 Shortest Distance (km)"))))
        )
    )
    k_alternatives = st.slider("Alternative Routes (Yen's K):", min_value=1, max_value=5, value=3, step=1)
    overlay_baseline = st.checkbox("Overlay Baseline Route Comparison", value=True) if opt_profile in (PROFILE_TIME_PLUS_SIGNAL, PROFILE_COMBINED_TRAFFIC_SIGNAL, PROFILE_HEAVY_CONGESTION) else False
    
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    solve_btn = st.button("🚀 Calculate Optimal Ambulance Route", type="primary", width="stretch")

st.markdown("---")

# 3. Solver Execution & Display
if selected_origin_node == selected_dest_node:
    st.error("⚠️ Origin and Destination cannot be the same intersection. Please choose distinct locations.")
    st.stop()

if not selected_dest_node:
    st.error(f"⚠️ Selected hospital does not have a valid snapped road connection within the 226-junction arterial model.")
    st.stop()

with st.spinner("Executing Dijkstra Shortest Path & Yen's K-Shortest Loopless Paths Algorithm..."):
    try:
        if "Hospital" in dest_type and selected_dest_hospital_id:
            if hasattr(router, "find_hospital_route"):
                route_res = router.find_hospital_route(selected_origin_node, selected_dest_hospital_id, profile=opt_profile)
            else:
                route_res = router.route_to_hospital(selected_origin_node, selected_dest_hospital_id, profile=opt_profile)
        else:
            route_res = router.find_shortest_path(selected_origin_node, selected_dest_node, profile=opt_profile)

        # Baseline comparison route if requested
        baseline_res = None
        if overlay_baseline:
            if "Hospital" in dest_type and selected_dest_hospital_id:
                if hasattr(router, "find_hospital_route"):
                    baseline_res = router.find_hospital_route(selected_origin_node, selected_dest_hospital_id, profile=PROFILE_MINIMUM_TIME)
                else:
                    baseline_res = router.route_to_hospital(selected_origin_node, selected_dest_hospital_id, profile=PROFILE_MINIMUM_TIME)
            else:
                baseline_res = router.find_shortest_path(selected_origin_node, selected_dest_node, profile=PROFILE_MINIMUM_TIME)

        # Compute alternative routes if K > 1
        alt_routes = []
        if k_alternatives > 1:
            alt_routes = router.find_k_alternative_routes(
                selected_origin_node,
                selected_dest_node,
                K=k_alternatives,
                profile=opt_profile
            )

    except UnreachableDestinationError:
        st.error(f"❌ No feasible directed path exists in the network from `{selected_origin_node}` to `{selected_dest_node}`.")
        st.stop()
    except Exception as e:
        st.error(f"Solver Error: {str(e)}")
        st.stop()

if route_res.get("status") != "OPTIMAL":
    st.warning(f"Could not find optimal path: {route_res.get('message', 'Unknown issue')}")
    st.stop()

# 4. KPI Performance Metric Display
m1, m2, m3, m4, m5 = st.columns(5)

tot_time_m = route_res.get("total_time_min", 0.0)
tot_dist_km = route_res.get("total_distance_km", 0.0)
avg_speed = route_res.get("average_speed_kmh", 0.0)
n_segs = route_res.get("num_segments", 0)

render_metric(m1, "Estimated Travel Time", f"{tot_time_m:.2f} min", f"{tot_time_m*60:,.0f} Total Seconds", "green" if tot_time_m < 15 else "normal")
render_metric(m2, "Physical Distance", f"{tot_dist_km:.2f} km", f"{route_res.get('total_distance_m', 0):,.0f} Meters", "normal")
render_metric(m3, "Effective Velocity", f"{avg_speed:.1f} km/h", "IRC:106 / BPR Calibrated", "normal")
render_metric(m4, "Route Segments", f"{n_segs} Links", f"{len(route_res.get('path_nodes', []))} Junctions Traversed", "normal")

if "Hospital" in dest_type:
    d_time = route_res.get("driveway_access_time_min", 1.0)
    d_dist = route_res.get("driveway_access_distance_m", 300.0)
    render_metric(m5, "Hospital Driveway Access", f"+{d_time:.1f} min", f"{d_dist:,.0f}m Bay Maneuvering", "amber")
else:
    render_metric(m5, "Solver Status", "OPTIMAL", "Dijkstra Minimum Time", "green")

# Delay Breakdown alert banner
t_sig_m = route_res.get("total_signal_delay_min", 0.0)
t_sig_s = route_res.get("total_signal_delay_sec", 0.0)
n_signals = route_res.get("num_signals_encountered", 0)
t_traff_m = route_res.get("total_traffic_delay_min", 0.0)
t_ff_m = route_res.get("free_flow_time_min", tot_time_m)

if t_sig_s > 0 or t_traff_m > 0:
    st.markdown(f"""
    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-left: 4px solid #0284C7; padding: 10px 14px; border-radius: 6px; margin: 12px 0; font-size: 13px; color: #0F172A; box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);">
        <span style="font-weight: 700; color: #0284C7;">⏱️ JOURNEY TIME DECOMPOSITION:</span>
        Base Road Cruising Time: <b>{t_ff_m:.2f} min</b> |
        Mid-Link Traffic Congestion Delay: <b style="color: #D97706;">+{t_traff_m:.2f} min</b> |
        Terminal Signal Red Delay: <b style="color: #7C3AED;">+{t_sig_m:.2f} min ({t_sig_s:.0f}s across {n_signals} verified signals)</b> |
        Total Journey: <b>{tot_time_m:.2f} min</b>
    </div>
    """, unsafe_allow_html=True)

# 5. Interactive GIS Route Map
st.markdown("### 🗺️ Interactive GIS Route Map")
st.caption("Inspect street-following route polylines, alternative loopless paths, waypoint turns, and emergency trauma facility bays.")

origin_pt = {
    "latitude": G_di.nodes[selected_origin_node]["lat"],
    "longitude": G_di.nodes[selected_origin_node]["lon"],
    "name": G_di.nodes[selected_origin_node].get("name", selected_origin_node)
}

dest_pt = None
hosp_pt = None
if "Hospital" in dest_type and hospital_rec:
    hosp_pt = {
        "latitude": hospital_rec["latitude"],
        "longitude": hospital_rec["longitude"],
        "hospital_name": hospital_rec["hospital_name"],
        "hospital_id": hospital_rec["hospital_id"],
        "verification_status": hospital_rec.get("verification_status", "VERIFIED"),
        "snapping_distance_m": hospital_rec.get("snapping_distance_m", 0.0)
    }
else:
    dest_pt = {
        "latitude": G_di.nodes[selected_dest_node]["lat"],
        "longitude": G_di.nodes[selected_dest_node]["lon"],
        "name": G_di.nodes[selected_dest_node].get("name", selected_dest_node)
    }

# Gather verified signals along route
route_signals = []
for pe in route_res.get("path_edges", []):
    if pe.get("signal_available") and pe.get("signal_delay_sec", 0) > 0:
        to_nid = pe.get("to_node")
        if to_nid and to_nid in G_di:
            nd = G_di.nodes[to_nid]
            route_signals.append({
                "intersection_id": to_nid,
                "name": nd.get("name", to_nid),
                "latitude": nd.get("lat"),
                "longitude": nd.get("lon"),
                "signal_delay_sec": pe.get("signal_delay_sec", 30.0),
                "cycle_time_sec": nd.get("cycle_time_sec", 120.0),
                "green_sec": max(15.0, 120.0 - math.sqrt(max(1.0, 2.0 * 120.0 * pe.get("signal_delay_sec", 30.0)))),
                "red_sec": math.sqrt(max(1.0, 2.0 * 120.0 * pe.get("signal_delay_sec", 30.0))),
                "verification_status": pe.get("signal_verification_status", "VERIFIED"),
                "pdf_source": pe.get("signal_reason", "Verified Traffic Signal Plan")
            })

m_route = create_ambulance_route_map(
    primary_route=route_res,
    alternative_routes=alt_routes,
    comparison_route=baseline_res,
    signal_nodes=route_signals,
    roads=roads_gis,
    origin_info=origin_pt,
    destination_info=dest_pt,
    hospital_info=hosp_pt,
    show_background_roads=True,
    show_legend=True
)
render_gis_map_in_streamlit(m_route, height=600, key=f"amb_route_{selected_origin_node}_{selected_dest_node}_{opt_profile}_{k_alternatives}")

# 6. Detailed Route Analysis Tabs
tab_alts, tab_signals, tab_itinerary = st.tabs([
    f"🔀 Alternative Routes ({len(alt_routes)})",
    f"🚦 Signal Delays En Route ({len(route_signals)})",
    "📋 Turn-by-Turn Itinerary"
])

# TAB 1: ALTERNATIVE ROUTES COMPARISON
with tab_alts:
    st.markdown("#### Yen's K-Shortest Loopless Paths Comparison")
    if alt_routes:
        alt_records = []
        for r_item in alt_routes:
            rank = r_item.get("rank", 1)
            t_m = r_item.get("total_time_min", 0.0)
            d_k = r_item.get("total_distance_km", 0.0)
            delta_t = r_item.get("delta_time_min", 0.0)
            detour_pct = r_item.get("detour_factor_pct", 0.0)
            
            label = "Primary Route (Optimal)" if rank == 1 else f"Option {rank} (Alternative {rank-1})"
            alt_records.append({
                "Option": label,
                "Travel Time": f"{t_m:.2f} min",
                "Distance": f"{d_k:.2f} km",
                "Time Penalty": f"+{delta_t:.2f} min (+{detour_pct:.1f}%)" if rank > 1 else "Baseline (0.00)",
                "Segments": r_item.get("num_segments", 0),
                "Avg Speed": f"{r_item.get('average_speed_kmh', 0):.1f} km/h",
                "Divergence Junction": r_item.get("divergence_node_name", "Origin")
            })
        
        df_alt_table = pd.DataFrame(alt_records)
        st.dataframe(df_alt_table, width="stretch", hide_index=True)
        st.caption("Alternative paths provide dispatchers with certified loopless bypass routes if an primary corridor is blocked.")
    else:
        st.info("Set slider K >= 2 to compute loopless alternative routes using Yen's algorithm.")

# TAB 2: VERIFIED SIGNAL TIMINGS & RED DELAYS
with tab_signals:
    st.markdown("#### Signalized Intersections Traversed En Route")
    if route_signals:
        sig_display_rows = []
        for s in route_signals:
            sig_display_rows.append({
                "Junction ID": s["intersection_id"],
                "Junction Name": s["name"],
                "Signal Delay": f"+{s['signal_delay_sec']:.1f} sec",
                "Cycle Time": f"{s['cycle_time_sec']:.0f} sec",
                "Estimated Green": f"{s['green_sec']:.0f} sec",
                "Estimated Red": f"{s['red_sec']:.0f} sec",
                "Verification Status": s["verification_status"],
                "Source PDF": s["pdf_source"]
            })
        st.dataframe(pd.DataFrame(sig_display_rows), width="stretch", hide_index=True)
        st.caption(f"Total signal-induced waiting delay: **+{t_sig_m:.2f} min** across {len(route_signals)} verified signalized intersections.")
    else:
        st.info("No signalized intersections with active signal timing plans encountered along this route.")

# TAB 3: TURN-BY-TURN ITINERARY
with tab_itinerary:
    st.markdown("#### Turn-by-Turn Emergency Dispatch Itinerary")
    path_edges = route_res.get("path_edges", [])
    if path_edges:
        itinerary_records = []
        cum_dist_m = 0.0
        cum_time_sec = 0.0

        for edge in path_edges:
            dist_m = float(edge.get("length_m", 0.0))
            time_s = float(edge.get("travel_time_sec", 0.0))
            cum_dist_m += dist_m
            cum_time_sec += time_s

            geom = edge.get("geometry", [])
            heading = "Straight"
            if geom and len(geom) >= 2:
                b = calculate_bearing(geom[0][0], geom[0][1], geom[-1][0], geom[-1][1])
                heading = f"{bearing_to_cardinal(b)} ({b:.0f}°)"

            itinerary_records.append({
                "Step": edge.get("step"),
                "From Junction": edge.get("from_name", edge.get("from_node")),
                "To Junction": edge.get("to_name", edge.get("to_node")),
                "Road Name": edge.get("road_name", "Arterial Link"),
                "Heading (Approx)": heading,
                "Distance (m)": f"{dist_m:,.0f} m",
                "Speed Limit": f"{edge.get('speed_kmh', 30)} km/h",
                "Road Travel Time": f"{time_s:.0f}s ({time_s/60:.1f}m)",
                "Signal Delay (Webster)": f"+{edge.get('signal_delay_sec', 0):.0f}s ({edge.get('signal_delay_min', 0):.2f}m)" if edge.get("signal_available") else "0s (Unsignalized/Unverified)",
                "Cumulative Distance": f"{cum_dist_m/1000:.2f} km",
                "Cumulative Time": f"{cum_time_sec/60:.1f} min"
            })

        df_itin = pd.DataFrame(itinerary_records)
        st.dataframe(df_itin, width="stretch", hide_index=True)

        st.caption("⚠️ **Notice:** *Cardinal directions are approximate headings calculated from geocoded coordinates. Road names reflect official BTP and OpenStreetMap records.*")

        csv_itin = df_itin.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Turn-by-Turn Itinerary (CSV)",
            data=csv_itin,
            file_name=f"ambulance_itinerary_{selected_origin_node}_{selected_dest_node}.csv",
            mime="text/csv"
        )
    else:
        st.info("No itinerary available.")

# Sequential Page Navigation
render_workflow_navigation(
    prev_page="pages/2_Hospital_Finder.py",
    prev_label="02. Hospital Finder",
    next_page="pages/4_Alternative_Route_Comparison.py",
    next_label="04. Alternative Route Comparison"
)
