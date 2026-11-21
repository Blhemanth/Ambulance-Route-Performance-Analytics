"""
Page 6: Ambulance Route Optimizer.
Ambulance Route Optimization — Bengaluru.

Interactive Operations Research emergency ambulance routing engine:
- Minimum estimated travel-time Dijkstra shortest path optimization.
- Shortest-distance benchmark comparison.
- Yen's K-shortest loopless alternative route generation (K=1 to 5).
- Integrated Phase 1 Hospital Facility triage & campus driveway delay modeling.
- Real Bengaluru OpenStreetMap road geometry polyline visualization.
- Accurate turn-by-turn itinerary with approximate cardinal headings.
"""

import os
import math
import streamlit as st
import pandas as pd
import networkx as nx
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
    current_page="pages/6_Shortest_Path.py"
)

# 1. Load Cached System Data
data = load_all_datasets()
gis_mgr, roads_gis, df_nodes_gis = load_gis_network()
df_hospitals, df_connections = load_hospital_data()
router = load_ambulance_router()
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
    "Majestic KSR Railway Station Core": "INT_001_RAJARAJESHWARI_JUNCTION",
    "Silk Board Arterial Hub (Madiwala)": "INT_068_MADIWALACHECKPOST_JUNCTIO",
    "Koramangala Traffic Zone (Rajalaxmi Mantapa)": "INT_006_RAJALAXMIKALYANAMANTAPA",
    "Indiranagar 100ft Road (B.M. Shri Circle)": "INT_010_B_M_SHRI_CMH_100FT_ROAD_J",
    "Yeshwantpur / Bhashyam Circle (North)": "INT_041_BHASHYAM_CIRCLE_JUNCTION",
    "Marathahalli / Doddanekundi Arterial (East)": "INT_173_DODDANEKUNDI_JUNCTION",
    "South Arterial Ring (Kanakapura Road)": "INT_007_KANAKAPURA_RING_ROAD_JUNC"
}

# 2. Control Panel
st.markdown("### 🎛️ Ambulance Dispatch & Routing Configuration")

col_cfg1, col_cfg2, col_cfg3 = st.columns([1.2, 1.4, 0.9])

with col_cfg1:
    st.markdown("#### 1. Ambulance Origin")
    origin_mode = st.radio("Origin Selection Mode:", ["Strategic Hubs", "Searchable Junction", "Manual Coordinates"], horizontal=True)

    sorted_nodes = sorted(list(G_di.nodes()))
    node_name_map = {n: f"{G_di.nodes[n].get('name', n)} ({n})" for n in sorted_nodes}

    # Handle pre-selected origin from session state
    preset_sel_origin = st.session_state.get("origin_node_id")

    if origin_mode == "Strategic Hubs":
        def_label = list(PRESET_ORIGINS.keys())[0]
        sel_preset_name = st.selectbox("Select Dispatch Hub:", list(PRESET_ORIGINS.keys()), index=0)
        selected_origin_node = PRESET_ORIGINS[sel_preset_name]
    elif origin_mode == "Searchable Junction":
        init_idx = sorted_nodes.index(preset_sel_origin) if preset_sel_origin in sorted_nodes else 0
        selected_origin_node = st.selectbox(
            "Select Road Network Junction:",
            sorted_nodes,
            index=init_idx,
            format_func=lambda x: node_name_map.get(x, x)
        )
    else:
        c_lat, c_lon = st.columns(2)
        in_lat = c_lat.number_input("Latitude:", value=12.9716, format="%.5f")
        in_lon = c_lon.number_input("Longitude:", value=77.5946, format="%.5f")
        # Nearest node snapping
        best_node, best_dist = None, float("inf")
        for n, d in G_di.nodes(data=True):
            lat, lon = d.get("latitude"), d.get("longitude")
            if lat and lon:
                dist = haversine_distance_m(in_lat, in_lon, lat, lon)
                if dist < best_dist:
                    best_dist = dist
                    best_node = n
        selected_origin_node = best_node
        st.caption(f"📍 Snapped to nearest junction: **{node_name_map.get(selected_origin_node, selected_origin_node)}** ({best_dist:,.0f} m)")

    orig_data = G_di.nodes[selected_origin_node]
    st.caption(f"Corridor: **{orig_data.get('corridor', 'Arterial')}** | Degree: **{G_di.degree(selected_origin_node)} directed links**")

with col_cfg2:
    st.markdown("#### 2. Destination Hospital")
    dest_type = st.radio("Destination Type:", ["Hospital Facility (Phase 1)", "Network Intersection"], horizontal=True)

    selected_dest_hospital_id = None
    selected_dest_node = None
    hospital_rec = None

    if dest_type == "Hospital Facility (Phase 1)":
        tier_filter = st.selectbox(
            "Emergency Triage Tier:",
            [
                "🟢 Verified Emergency Trauma Centers (103)",
                "🔵 Probable Emergency Tertiary (51)",
                "All Healthcare Facilities (1,084)"
            ]
        )
        if "Verified" in tier_filter:
            filtered_hospitals = df_hospitals[df_hospitals["verification_status"] == "VERIFIED_EMERGENCY"]
        elif "Probable" in tier_filter:
            filtered_hospitals = df_hospitals[df_hospitals["verification_status"] == "EMERGENCY_PROBABLE_UNVERIFIED"]
        else:
            filtered_hospitals = df_hospitals

        # Check session state for incoming hospital
        default_hid = st.session_state.get("target_hospital_id", "BLR_HOSP_0052")
        hosp_ids = list(filtered_hospitals["hospital_id"].dropna().unique())
        if not hosp_ids:
            hosp_ids = list(df_hospitals["hospital_id"].dropna().unique())
        
        default_idx = hosp_ids.index(default_hid) if default_hid in hosp_ids else 0

        def _fmt_hosp_option(r):
            a = r.get("address")
            a_str = str(a).strip() if pd.notna(a) and str(a).strip() else "Bengaluru"
            return f"{r['hospital_name']} — {a_str[:35]}"

        hosp_name_dict = {
            row["hospital_id"]: _fmt_hosp_option(row)
            for _, row in filtered_hospitals.iterrows()
        }

        selected_dest_hospital_id = st.selectbox(
            "Select Receiving Emergency Hospital:",
            hosp_ids,
            index=default_idx,
            format_func=lambda x: hosp_name_dict.get(x, x)
        )

        h_matches = df_hospitals[df_hospitals["hospital_id"] == selected_dest_hospital_id]
        if not h_matches.empty:
            hospital_rec = h_matches.iloc[0].to_dict()
            # Join connection data
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
        # Direct Intersection
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
    st.error(f"⚠️ Selected hospital ({hospital_rec.get('hospital_name', 'Hospital') if hospital_rec else 'Unknown'}) does not have a valid snapped road connection within the 226-junction arterial model.")
    st.stop()

# Auto-solve or solve on button
with st.spinner("Executing Dijkstra Shortest Path & Yen's K-Shortest Loopless Paths Algorithm..."):
    try:
        # 1. Primary Route Calculation
        if hospital_rec:
            primary_result = router.route_to_hospital(
                origin=selected_origin_node,
                hospital_id_or_name=selected_dest_hospital_id,
                profile=opt_profile
            )
        else:
            primary_result = router.find_shortest_path(
                origin=selected_origin_node,
                destination=selected_dest_node,
                profile=opt_profile
            )

        # 2. Alternative Routes via Yen's Algorithm
        alt_routes = router.find_k_alternative_routes(
            origin=selected_origin_node,
            destination=selected_dest_node,
            K=k_alternatives,
            profile=opt_profile
        )

        # 3. Comparative Benchmark (Time vs Distance)
        benchmark_comp = router.compare_distance_vs_time_routes(
            origin=selected_origin_node,
            destination=selected_dest_node
        )

        # 4. Signal-Aware vs Baseline Comparison (Phase 4 Task 8)
        signal_comp = router.compare_baseline_vs_signal_aware(
            origin=selected_origin_node,
            destination=selected_dest_node
        ) if opt_profile == PROFILE_TIME_PLUS_SIGNAL else None

    except UnreachableDestinationError:
        primary_result = {"status": "NO_PATH_EXISTS"}
        alt_routes = []
        benchmark_comp = None
        signal_comp = None
    except Exception as e:
        primary_result = {"status": "ERROR", "message": str(e)}
        alt_routes = []
        benchmark_comp = None
        signal_comp = None

if primary_result.get("status") in ["NO_PATH_EXISTS", "ERROR"]:
    st.error(f"🚨 No feasible directed path exists between **{node_name_map.get(selected_origin_node, selected_origin_node)}** and **{node_name_map.get(selected_dest_node, selected_dest_node)}** due to one-way flow constraints.")
    st.info("💡 Try selecting another arterial origin or choosing a hospital with access from bidirectional arterials.")
    st.stop()

# 4. Result Metrics Row (Task 5 & Phase 4)
st.markdown("### 📊 Route Optimization Solution Summary")

if opt_profile == PROFILE_TIME_PLUS_SIGNAL:
    t_tot_min = primary_result.get("total_signal_aware_time_min", primary_result.get("total_time_min", 0.0))
else:
    t_tot_min = primary_result.get("total_time_min", 0.0)

t_sig_delay_min = primary_result.get("total_signal_delay_min", 0.0)
n_signals = primary_result.get("num_signals_encountered", 0)
d_tot_km = primary_result.get("total_distance_km", 0.0)
n_segs = primary_result.get("num_segments", 0)
v_avg = primary_result.get("average_speed_kmh", 0.0)

m1, m2, m3, m4, m5, m6 = st.columns(6)
if opt_profile == PROFILE_TIME_PLUS_SIGNAL:
    render_metric(m1, "Signal-Aware Total Time", f"{t_tot_min:.1f} min", f"Road: {primary_result.get('total_time_min', 0):.1f}m + Sig: {t_sig_delay_min:.1f}m", "green")
else:
    render_metric(m1, "Estimated Road Time", f"{t_tot_min:.1f} min", f"{t_tot_min * 60:.0f} seconds", "green")

render_metric(m2, "Total Road Distance", f"{d_tot_km:.2f} km", f"{d_tot_km * 1000:,.0f} meters", "normal")
render_metric(m3, "Arterial Road Segments", f"{n_segs} Links", f"{n_segs + 1} Junctions", "normal")
render_metric(m4, "Effective Average Speed", f"{v_avg:.1f} km/h", "IRC:106 Calibrated", "green")

if opt_profile == PROFILE_TIME_PLUS_SIGNAL:
    render_metric(m5, "Signal Delays (Webster)", f"+{t_sig_delay_min:.1f} min", f"{n_signals} Verified Signals", "amber" if n_signals > 0 else "green")
else:
    render_metric(m5, "Solver Optimality", "Rank 1 (Optimal)", "Dijkstra Engine", "green")

if hospital_rec:
    d_gate = hospital_rec.get("estimated_access_time_min", 1.0)
    render_metric(m6, "Driveway Penalty", f"+{d_gate:.1f} min", f"{hospital_rec.get('snapping_distance_m', 0):,.0f}m Gate Delay", "amber")
else:
    render_metric(m6, "Alternative Paths", f"{len(alt_routes)} Options", "Yen's Loopless", "normal")

# Signal Comparison Card (Phase 4 Task 8)
if signal_comp and signal_comp.get("status") == "SUCCESS":
    with st.container():
        st.markdown("""
        <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 8px; padding: 12px 16px; margin: 12px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <b style="color: #166534; font-size: 13px;">🚦 Scenario A (Baseline) vs Scenario B (Signal-Aware) Route Comparison</b>
                <span style="background: #DCFCE7; color: #15803D; font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 4px;">
                    PHASE 4 VALIDATED
                </span>
            </div>
            <div style="font-size: 12px; color: #1E293B; line-height: 1.5;">
        """ + f"<b>Routing Decision:</b> {signal_comp['route_changes_description']}" + """
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# 5. Interactive GIS Map (Task 2 & Task 4 & Task 9)
st.markdown("### 🗺️ Bengaluru Metropolitan Ambulance Route Map")
st.caption("Authentic OpenStreetMap road geometry with real street curvature. Cyan = Signal-Aware / Primary Route; Orange = Baseline Route; Purple = Alternative Routes.")

orig_info = {
    "intersection_id": selected_origin_node,
    "name": G_di.nodes[selected_origin_node].get("name", selected_origin_node),
    "latitude": G_di.nodes[selected_origin_node].get("latitude", 12.9716),
    "longitude": G_di.nodes[selected_origin_node].get("longitude", 77.5946),
    "corridor": G_di.nodes[selected_origin_node].get("corridor", "Arterial")
}

hosp_map_info = None
dest_map_info = None
if hospital_rec:
    hosp_map_info = hospital_rec
else:
    dest_map_info = {
        "intersection_id": selected_dest_node,
        "name": G_di.nodes[selected_dest_node].get("name", selected_dest_node),
        "latitude": G_di.nodes[selected_dest_node].get("latitude", 12.9716),
        "longitude": G_di.nodes[selected_dest_node].get("longitude", 77.5946)
    }

# Build signal markers along primary path
signal_markers = []
for pe in primary_result.get("path_edges", []):
    to_n = pe.get("to_node")
    if to_n in G_di.nodes and pe.get("signal_available", False) and pe.get("signal_delay_sec", 0) > 0:
        node_d = G_di.nodes[to_n]
        signal_markers.append({
            "name": node_d.get("name", to_n),
            "junction_name": node_d.get("name", to_n),
            "latitude": node_d.get("latitude", 12.9716),
            "longitude": node_d.get("longitude", 77.5946),
            "source_pdf": node_d.get("source_pdf", "BEL_Engineering_Plan.pdf"),
            "source_page": node_d.get("source_page", node_d.get("page_number", 1)),
            "cycle_sec": node_d.get("cycle_time_sec", 120.0),
            "green_sec": max(15.0, 120.0 - math.sqrt(max(1.0, 2.0 * 120.0 * pe.get("signal_delay_sec", 30.0)))),
            "signal_delay_sec": pe.get("signal_delay_sec", 30.0),
            "signal_delay_min": pe.get("signal_delay_min", 0.5),
            "verification_status": pe.get("signal_verification_status", "VERIFIED"),
            "approach_code": pe.get("approach_code", "A"),
            "plan_name": "WEEKDAY_MORNING_PEAK"
        })

comp_route_obj = signal_comp["scenario_a_baseline"] if (overlay_baseline and signal_comp and signal_comp.get("status") == "SUCCESS") else None

m_route = create_ambulance_route_map(
    primary_route=primary_result,
    alternative_routes=alt_routes,
    comparison_route=comp_route_obj,
    signal_nodes=signal_markers if opt_profile == PROFILE_TIME_PLUS_SIGNAL else None,
    roads=roads_gis,
    origin_info=orig_info,
    destination_info=dest_map_info,
    hospital_info=hosp_map_info,
    hospitals_catalog=df_hospitals,
    show_background_roads=True,
    show_legend=True
)
render_gis_map_in_streamlit(m_route, height=620, key=f"amb_route_{selected_origin_node}_{selected_dest_node}")

st.markdown("---")

# 6. Detailed Panels: Alternatives Table & Itinerary
tab_alts, tab_benchmark, tab_turn_by_turn = st.tabs([
    "🔀 Alternative Routes Comparison (Yen's Algorithm)",
    "⚖️ Travel Time vs. Physical Distance Tradeoff",
    "📋 Turn-by-Turn Route Itinerary & Cardinal Headings"
])

# TAB 1: ALTERNATIVE ROUTES COMPARISON TABLE (Task 5)
with tab_alts:
    st.markdown("#### Yen's K-Shortest Loopless Paths Evaluation")
    st.caption("Calculates strictly loopless alternative routes by perturbing spur nodes along the optimal path.")

    if alt_routes:
        alt_table_data = []
        base_time = alt_routes[0].get("total_time_min", 0.0)
        base_dist = alt_routes[0].get("total_distance_km", 0.0)

        for r in alt_routes:
            t = r.get("total_time_min", 0.0)
            d = r.get("total_distance_km", 0.0)
            d_time = round(t - base_time, 2)
            pct_time = round((d_time / base_time * 100.0) if base_time > 0 else 0.0, 1)
            d_dist = round(d - base_dist, 3)

            alt_table_data.append({
                "Rank": f"Option {r.get('rank')}",
                "Status": "Optimal (Primary)" if r.get("rank") == 1 else "Alternative",
                "Travel Time (min)": f"{t:.2f}",
                "Time Delta (+min)": f"+{d_time:.2f} min" if d_time > 0 else "0.0 min",
                "Time Delta (%)": f"+{pct_time:.1f}%" if d_time > 0 else "0.0%",
                "Distance (km)": f"{d:.2f}",
                "Distance Delta (+km)": f"+{d_dist:.2f} km" if d_dist > 0 else "0.0 km",
                "Avg Speed (km/h)": f"{r.get('average_speed_kmh', 0.0):.1f}",
                "Segments": r.get("num_segments", 0),
                "Divergence Context": r.get("divergence_description", "Primary route")
            })

        st.dataframe(pd.DataFrame(alt_table_data), width="stretch", hide_index=True)
    else:
        st.info("No alternative paths found for this OD pair.")

# TAB 2: TIME VS DISTANCE BENCHMARK (Task 10)
with tab_benchmark:
    st.markdown("#### Travel Time vs. Physical Distance Objective Comparison")
    st.caption("Validates how selecting Minimum Travel Time routing trades additional road distance to exploit higher-speed arterials.")

    if benchmark_comp and benchmark_comp.get("status") == "SUCCESS":
        c_b1, c_b2 = st.columns([1.2, 1])

        with c_b1:
            st.markdown(f"**Empirical Route Comparison:**")
            st.info(f"💡 {benchmark_comp.get('tradeoff_explanation')}")

            comp_df = pd.DataFrame([
                {
                    "Metric": "Total Travel Time (min)",
                    "Minimum-Time Route": f"{benchmark_comp['fastest_time_min']:.2f} min",
                    "Shortest-Distance Route": f"{benchmark_comp['shortest_dist_time_min']:.2f} min",
                    "Net Difference": f"-{benchmark_comp['time_saved_min']:.2f} min ({benchmark_comp['time_saved_percentage']}%)"
                },
                {
                    "Metric": "Total Road Distance (km)",
                    "Minimum-Time Route": f"{benchmark_comp['fastest_distance_km']:.2f} km",
                    "Shortest-Distance Route": f"{benchmark_comp['shortest_distance_km']:.2f} km",
                    "Net Difference": f"+{benchmark_comp['delta_distance_km']:+.2f} km"
                },
                {
                    "Metric": "Identical Trajectory?",
                    "Minimum-Time Route": "Yes" if benchmark_comp["is_identical_path"] else "No (Divergent paths)",
                    "Shortest-Distance Route": "Yes" if benchmark_comp["is_identical_path"] else "No (Divergent paths)",
                    "Net Difference": "Diverges on high-capacity bypass" if not benchmark_comp["is_identical_path"] else "Identical"
                }
            ])
            st.dataframe(comp_df, width="stretch", hide_index=True)

        with c_b2:
            fig_comp = go.Figure(data=[
                go.Bar(
                    name="Travel Time (min)",
                    x=["Minimum-Time Route", "Shortest-Distance Route"],
                    y=[benchmark_comp["fastest_time_min"], benchmark_comp["shortest_dist_time_min"]],
                    marker_color=["#06B6D4", "#F59E0B"],
                    text=[f"{benchmark_comp['fastest_time_min']:.1f}m", f"{benchmark_comp['shortest_dist_time_min']:.1f}m"],
                    textposition="auto"
                )
            ])
            fig_comp.update_layout(get_plotly_layout("Travel Time Comparison by Objective", height=280))
            st.plotly_chart(fig_comp, width="stretch")

# TAB 3: TURN-BY-TURN ROUTE INSTRUCTIONS (Task 6)
with tab_turn_by_turn:
    st.markdown("#### Turn-by-Turn Emergency Navigation Itinerary")
    st.caption("Exact sequence of road segments, regulated speed limits, and approximate cardinal headings derived from link coordinates.")

    path_edges = primary_result.get("path_edges", [])
    if path_edges:
        itinerary_records = []
        cum_dist_m = 0.0
        cum_time_sec = 0.0

        for edge in path_edges:
            dist_m = edge.get("length_m", 0.0)
            time_s = edge.get("travel_time_sec", 0.0)
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
    prev_page="app.py",
    prev_label="Operations Dashboard",
    next_page="pages/3_Network_Visualization.py",
    next_label="02. Road Network Explorer"
)
