"""
Ambulance Route Optimization — Traffic Congestion & Scenario Analysis.
Page 13: Interactive GIS Multi-Scenario Routing & Congestion Analysis.
Phase 5 — Bengaluru Traffic Data Integration and Scenario Analysis.
"""

import os
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

from components.ui_helpers import (
    load_custom_css,
    render_header,
    render_metric,
    render_workflow_navigation,
    get_plotly_layout,
    load_ambulance_router,
    load_congestion_scenario_data,
    load_hospital_data
)
from components.gis_map import (
    create_ambulance_route_map,
    render_gis_map_in_streamlit
)
from src.network.ambulance_router import (
    PROFILE_MINIMUM_TIME,
    PROFILE_SHORTEST_DISTANCE,
    PROFILE_MODERATE_CONGESTION,
    PROFILE_HEAVY_CONGESTION,
    PROFILE_COMBINED_TRAFFIC_SIGNAL
)

st.set_page_config(
    page_title="Traffic Scenario Analysis — Bengaluru Ambulance Routing",
    page_icon="📊",
    layout="wide"
)

load_custom_css()
render_header(
    title="Traffic Congestion & Scenario Analysis",
    subtitle="Macroscopic BPR Congestion Modeling, Time-of-Day Peak Scenarios & Non-Double-Counting Travel Time Optimization",
    badge_text="Operations Research — Shortest Path",
    current_page="pages/13_Traffic_Scenario_Analysis.py"
)

# Load core datasets
router = load_ambulance_router()
df_inventory, df_scenarios = load_congestion_scenario_data()
df_hospitals, df_connections = load_hospital_data()

# ---------------------------------------------------------
# Academic Context Banner
# ---------------------------------------------------------
st.markdown("""
<div style="background: rgba(30, 41, 59, 0.7); border-left: 4px solid #8B5CF6; padding: 0.9rem 1.2rem; border-radius: 6px; margin-bottom: 1.2rem; font-size: 0.85rem; line-height: 1.5;">
    <b style="color: #DDD6FE;">🔬 ACADEMIC TRAFFIC CONGESTION & NON-DOUBLE-COUNTING METHODOLOGY:</b><br/>
    This module evaluates the resilience of emergency ambulance dispatch across Greater Bengaluru under dynamic congestion.
    Link slowdowns are modeled using the macroscopic <b>Bureau of Public Roads (BPR) volume-delay formulation</b>
    calibrated to empirical <b>TomTom Traffic Index</b> peak-hour velocity benchmarks (13.9 km/h rush-hour vs 29.0 km/h free-flow).<br/>
    <span style="color: #34D399; font-weight: 600;">Strict Non-Double-Counting Invariant:</span>
    $$t_{\\text{edge}} = t_0 \\text{ (free-flow road time)} + \\Delta t_{\\text{traffic}} \\text{ (mid-link slowdown)} + d_{\\text{signal}} \\text{ (terminal junction red delay)}$$
    All link weights are strictly positive ($w_e > 0$), fully satisfying Dijkstra's shortest path optimality requirements.
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# High-Level Metric Cards
# ---------------------------------------------------------
k1, k2, k3, k4 = st.columns(4)

with k1:
    render_metric(
        k1,
        title="Baseline Free-Flow Speed",
        value="35.0 km/h",
        subtitle="IRC:106 Calibrated Speed Limit",
        status="normal"
    )
with k2:
    render_metric(
        k2,
        title="Moderate Congestion Speed",
        value="27.1 km/h",
        subtitle="Inter-Peak (v/c ≈ 0.65, +7.7% Time)",
        status="normal"
    )
with k3:
    render_metric(
        k3,
        title="Heavy Congestion Speed",
        value="21.2 km/h",
        subtitle="TomTom Peak Benchmark (v/c ≈ 1.05)",
        status="warning"
    )
with k4:
    render_metric(
        k4,
        title="Active Scenarios Evaluated",
        value="5 Models",
        subtitle="4,656 Road Link Records Generated",
        status="success"
    )

st.markdown("<br/>", unsafe_allow_html=True)

# ---------------------------------------------------------
# Interactive Corridor / Hospital Scenario Selector
# ---------------------------------------------------------
st.markdown("### 🔀 Multi-Scenario Route Experimentation")

tab_preset, tab_custom_od, tab_hospital = st.tabs([
    "🏁 10 Canonical Emergency Corridors",
    "📍 Custom OD Intersection Pair",
    "🏥 Emergency Hospital Dispatch Route"
])

selected_origin = None
selected_destination = None
is_hospital_mode = False
selected_hospital_id = None

# Tab 1: 10 Pre-computed Canonical Emergency Corridors
with tab_preset:
    preset_corridors = [
        ("INT_001_RAJARAJESHWARI_JUNCTION", "INT_003_ADUGODI_JUNCTION", "South-West Arterial to Adugodi Central Hub"),
        ("INT_001_RAJARAJESHWARI_JUNCTION", "INT_103_ANANDRAO_JUNCTION", "Mysore Road to Anandrao Circle CBD Hub"),
        ("INT_103_ANANDRAO_JUNCTION", "INT_073_OLDMADRAS_ROAD_INDIRANAGA", "City Core to Indiranagar Tech Corridor"),
        ("INT_052_PRASANNA_JUNCTION", "INT_003_ADUGODI_JUNCTION", "Magadi Road Corridor to Adugodi Hub"),
        ("INT_005_PUTTANNA_JUNCTION", "INT_160_KIMCO_JUNCTION_MYSORE_ROA", "Adugodi West to Kimco Industrial Sector"),
        ("INT_055_SONYWORLD_JUNCTION_INDIRA", "INT_103_ANANDRAO_JUNCTION", "Sony World Indiranagar to Central Anandrao"),
        ("INT_055_SONYWORLD_JUNCTION_INDIRA", "INT_073_OLDMADRAS_ROAD_INDIRANAGA", "Sony World to Old Madras Rd Arterial"),
        ("INT_159_HOYSALA_CIRCLEKENGERIUPAN", "INT_103_ANANDRAO_JUNCTION", "Kengeri Satellite Town to CBD Center"),
        ("INT_002_SATELLITEBUSSTAND_JUNCTIO", "INT_003_ADUGODI_JUNCTION", "Satellite Bus Stand to South-Central"),
        ("INT_160_KIMCO_JUNCTION_MYSORE_ROA", "INT_055_SONYWORLD_JUNCTION_INDIRA", "Mysore Rd Industrial to Sony World Tech"),
    ]
    corridor_labels = [f"{label} ({u[:12]} → {v[:12]})" for u, v, label in preset_corridors]
    sel_idx = st.selectbox("Select Canonical Corridor:", range(len(corridor_labels)), format_func=lambda i: corridor_labels[i])
    selected_origin = preset_corridors[sel_idx][0]
    selected_destination = preset_corridors[sel_idx][1]

# Tab 2: Custom Intersection Pair
with tab_custom_od:
    all_nodes = sorted(list(router.graph_di.nodes()))
    node_names = {nid: router.graph_di.nodes[nid].get("name", nid) for nid in all_nodes}

    c_o, c_d = st.columns(2)
    with c_o:
        u_sel = st.selectbox(
            "Origin Junction:",
            all_nodes,
            index=all_nodes.index(selected_origin) if selected_origin in all_nodes else 0,
            format_func=lambda nid: f"{nid}: {node_names.get(nid, nid)}"
        )
    with c_d:
        v_sel = st.selectbox(
            "Destination Junction:",
            all_nodes,
            index=all_nodes.index(selected_destination) if selected_destination in all_nodes else 1,
            format_func=lambda nid: f"{nid}: {node_names.get(nid, nid)}"
        )
    if st.button("Apply Custom OD Pair", key="btn_apply_custom_od"):
        selected_origin = u_sel
        selected_destination = v_sel

# Tab 3: Hospital Facility Route
with tab_hospital:
    if df_hospitals is not None and not df_hospitals.empty:
        hosp_options = df_hospitals["hospital_id"].tolist()
        hosp_labels = {
            r["hospital_id"]: f"{r['hospital_name']} ({r.get('emergency_service_type', 'Emergency')}) — {r.get('sub_district', 'Bengaluru')}"
            for _, r in df_hospitals.iterrows()
        }
        h_sel = st.selectbox("Select Destination Hospital Facility:", hosp_options, format_func=lambda hid: hosp_labels.get(hid, hid))
        
        # Origin junction for hospital dispatch
        o_hosp_sel = st.selectbox(
            "Ambulance Origin Station:",
            all_nodes,
            index=0,
            key="hosp_origin_sel",
            format_func=lambda nid: f"{nid}: {node_names.get(nid, nid)}"
        )
        if st.button("Evaluate Hospital Multi-Scenario Route", key="btn_apply_hospital"):
            selected_origin = o_hosp_sel
            selected_hospital_id = h_sel
            is_hospital_mode = True

# ---------------------------------------------------------
# Execute Optimization & Render Results
# ---------------------------------------------------------
st.markdown("---")

if is_hospital_mode and selected_hospital_id:
    exp_res = router.compare_hospital_scenarios(selected_origin, selected_hospital_id)
else:
    exp_res = router.compare_traffic_scenarios(selected_origin, selected_destination)

if exp_res["status"] != "SUCCESS":
    st.error(f"Routing failed: {exp_res.get('message', 'No feasible path')}")
else:
    scenarios = exp_res["scenarios"]
    base = scenarios["BASELINE_FREE_FLOW"]
    dist_sc = scenarios["SHORTEST_DISTANCE"]
    mod = scenarios["MODERATE_CONGESTION"]
    hvy = scenarios["HEAVY_CONGESTION"]
    comb = scenarios["COMBINED_TRAFFIC_SIGNAL"]

    st.markdown(f"#### 🚑 Corridor: **{exp_res['origin_name']}** → **{exp_res.get('destination_name', exp_res.get('hospital_name', 'Destination'))}**")
    st.info(exp_res["summary_narrative"])

    # 4 Scenario KPI summary cards
    sc_c1, sc_c2, sc_c3, sc_c4, sc_c5 = st.columns(5)
    with sc_c1:
        render_metric(
            sc_c1,
            title="Baseline Free-Flow",
            value=f"{base['total_time_min']:.2f} min",
            subtitle=f"{base['distance_km']:.2f} km @ {base['average_speed_kmh']:.1f} km/h",
            status="normal"
        )
    with sc_c2:
        render_metric(
            sc_c2,
            title="Shortest Distance",
            value=f"{dist_sc['total_time_min']:.2f} min",
            subtitle=f"{dist_sc['distance_km']:.2f} km @ {dist_sc['average_speed_kmh']:.1f} km/h",
            status="normal"
        )
    with sc_c3:
        render_metric(
            sc_c3,
            title="Moderate Congestion",
            value=f"{mod['total_time_min']:.2f} min",
            subtitle=f"+{mod['traffic_delay_min']:.2f} min delay @ {mod['average_speed_kmh']:.1f} km/h",
            status="normal"
        )
    with sc_c4:
        render_metric(
            sc_c4,
            title="Heavy Peak Congestion",
            value=f"{hvy['total_time_min']:.2f} min",
            subtitle=f"+{hvy['traffic_delay_min']:.2f} min delay @ {hvy['average_speed_kmh']:.1f} km/h",
            status="warning"
        )
    with sc_c5:
        render_metric(
            sc_c5,
            title="Combined Traffic + Signals",
            value=f"{comb['total_time_min']:.2f} min",
            subtitle=f"+{comb['signal_delay_min']:.2f} min signal delay @ {comb['average_speed_kmh']:.1f} km/h",
            status="danger"
        )

    # ---------------------------------------------------------
    # Interactive GIS Map Visualization
    # ---------------------------------------------------------
    st.markdown("### 🗺️ Multi-Scenario GIS Route Map Overlay")
    st.caption("Layer control allows toggling individual scenario paths on and off. Popups provide detailed segment and delay telemetry.")

    folium_map = create_ambulance_route_map(
        scenario_routes=scenarios,
        origin_info={"latitude": router.graph_di.nodes[selected_origin]["lat"], "longitude": router.graph_di.nodes[selected_origin]["lon"]},
        hospital_info={"latitude": exp_res.get("latitude"), "longitude": exp_res.get("longitude")} if is_hospital_mode else None
    )
    render_gis_map_in_streamlit(folium_map, height=560)

    # ---------------------------------------------------------
    # Analytical Visualizations
    # ---------------------------------------------------------
    st.markdown("### 📈 Delay Decomposition & Speed Degradation")
    c_chart1, c_chart2 = st.columns(2)

    with c_chart1:
        # Stacked Bar Chart of Travel Time Components
        sc_names = ["Baseline", "Shortest Dist", "Moderate", "Heavy Peak", "Combined"]
        ff_times = [scenarios[k]["free_flow_time_min"] for k in ["BASELINE_FREE_FLOW", "SHORTEST_DISTANCE", "MODERATE_CONGESTION", "HEAVY_CONGESTION", "COMBINED_TRAFFIC_SIGNAL"]]
        traff_delays = [scenarios[k]["traffic_delay_min"] for k in ["BASELINE_FREE_FLOW", "SHORTEST_DISTANCE", "MODERATE_CONGESTION", "HEAVY_CONGESTION", "COMBINED_TRAFFIC_SIGNAL"]]
        sig_delays = [scenarios[k]["signal_delay_min"] for k in ["BASELINE_FREE_FLOW", "SHORTEST_DISTANCE", "MODERATE_CONGESTION", "HEAVY_CONGESTION", "COMBINED_TRAFFIC_SIGNAL"]]

        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            name="Free-Flow Road Time",
            x=sc_names,
            y=ff_times,
            marker_color="#3B82F6"
        ))
        fig_bar.add_trace(go.Bar(
            name="Mid-Link Traffic Delay",
            x=sc_names,
            y=traff_delays,
            marker_color="#F59E0B"
        ))
        fig_bar.add_trace(go.Bar(
            name="Terminal Signal Delay",
            x=sc_names,
            y=sig_delays,
            marker_color="#8B5CF6"
        ))

        fig_bar.update_layout(
            barmode="stack",
            title="Travel Time Decomposition Across Scenarios (Minutes)",
            xaxis_title="Congestion Scenario",
            yaxis_title="Time (Minutes)",
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=380,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with c_chart2:
        # Effective Speed Degradation Curve
        speeds = [scenarios[k]["average_speed_kmh"] for k in ["BASELINE_FREE_FLOW", "SHORTEST_DISTANCE", "MODERATE_CONGESTION", "HEAVY_CONGESTION", "COMBINED_TRAFFIC_SIGNAL"]]
        
        fig_speed = go.Figure()
        fig_speed.add_trace(go.Scatter(
            x=sc_names,
            y=speeds,
            mode="lines+markers+text",
            text=[f"{s:.1f} km/h" for s in speeds],
            textposition="top center",
            line=dict(color="#10B981", width=3),
            marker=dict(size=10, color="#34D399")
        ))
        fig_speed.update_layout(
            title="Effective Journey Velocity Degradation (km/h)",
            xaxis_title="Congestion Scenario",
            yaxis_title="Effective Speed (km/h)",
            yaxis=dict(range=[0, max(speeds) * 1.25]),
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=380
        )
        st.plotly_chart(fig_speed, use_container_width=True)

    # ---------------------------------------------------------
    # Tabular Comparison Breakdown
    # ---------------------------------------------------------
    st.markdown("### 📋 Scenario Comparison Table")
    st.dataframe(
        exp_res["comparison_table"],
        use_container_width=True,
        hide_index=True
    )

# ---------------------------------------------------------
# Empirical Bengaluru Traffic Data Provenance Audit
# ---------------------------------------------------------
st.markdown("---")
st.markdown("### 📜 Bengaluru Traffic Data Inventory & Academic Provenance Audit")
st.markdown("""
To maintain absolute scientific and academic integrity, **no synthetic or imaginary sensor streams are represented as observed real-time telemetry**.
Below is the verified audit catalog of public data repositories in Bengaluru investigated during Phase 5.
""")

if df_inventory is not None and not df_inventory.empty:
    disp_cols = [c for c in [
        "dataset_id", "dataset_name", "source_organization", "format",
        "geographic_coverage", "spatial_resolution", "measurement_type", "suitability_assessment"
    ] if c in df_inventory.columns]
    st.dataframe(
        df_inventory[disp_cols],
        use_container_width=True,
        hide_index=True
    )

# Page Navigation
render_workflow_navigation(
    prev_page="pages/12_Signal_Delay_Analysis.py",
    prev_label="02. Signal Timing & Delays",
    next_page="pages/3_Network_Visualization.py",
    next_label="04. Road Network Explorer"
)
