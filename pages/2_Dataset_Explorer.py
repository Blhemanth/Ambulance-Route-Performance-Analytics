"""
Page 2: Dataset Explorer.
Provides searchable, filterable tables for intersections, road approaches,
signal phases, timing plans, and extraction quality audit logs.
"""

import streamlit as st
import pandas as pd
from components.ui_helpers import (
    load_custom_css,
    render_header,
    render_workflow_navigation,
    load_all_datasets
)

st.set_page_config(page_title="Dataset Explorer | Bengaluru Smart Traffic", page_icon="🔍", layout="wide")
load_custom_css()

render_header(
    title="Bengaluru Signal Dataset Explorer",
    subtitle="Searchable Catalog of 226 Intersections, 652 Approaches, 879 Phases & 5,362 Timing Plans",
    badge_text="Ground Truth Data",
    current_page="pages/2_Dataset_Explorer.py"
)

data = load_all_datasets()
df_nodes = data["intersections"]
df_roads = data["roads"]
df_phases = data["phases"]
df_timings = data["timings"]
df_errors = data["errors"]

# Top filters
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📍 Intersections (226)",
    "🛣️ Road Approaches (652)",
    "🚦 Signal Phases (879)",
    "⏱️ Timing Plans (5,362)",
    "⚠️ Extraction Audit Logs",
    "✏️ Manual Correction"
])

# TAB 1: INTERSECTIONS
with tab1:
    st.markdown("#### Geocoded Intersections in Bengaluru Network")
    col_search, col_corr = st.columns([2, 1])
    search_q = col_search.text_input("Search intersection name or ID:", placeholder="e.g. Silk Board, Doddanekundi, CMH")
    
    corridors = ["All Corridors"] + sorted(list(df_nodes["corridor"].dropna().unique()))
    sel_corr = col_corr.selectbox("Filter Corridor:", corridors)
    
    filtered_nodes = df_nodes.copy()
    if search_q:
        filtered_nodes = filtered_nodes[
            filtered_nodes["name"].str.contains(search_q, case=False, na=False) |
            filtered_nodes["intersection_id"].str.contains(search_q, case=False, na=False)
        ]
    if sel_corr != "All Corridors":
        filtered_nodes = filtered_nodes[filtered_nodes["corridor"] == sel_corr]
        
    st.write(f"Showing **{len(filtered_nodes)}** of {len(df_nodes)} intersections:")
    st.dataframe(
        filtered_nodes[["intersection_id", "name", "corridor", "latitude", "longitude", "cycle_time_sec", "num_phases", "data_provenance"]],
        use_container_width=True,
        height=400
    )

# TAB 2: ROAD APPROACHES
with tab2:
    st.markdown("#### Road Links & Geometric Capacities (IRC:106 Standards)")
    col_r1, col_r2 = st.columns([1, 1])
    sel_int_road = col_r1.selectbox("Filter by Intersection:", ["All Intersections"] + sorted(list(df_nodes["name"].unique())))
    sel_lanes = col_r2.slider("Minimum Lanes:", 1, 6, 1)

    filtered_roads = df_roads.copy()
    if sel_int_road != "All Intersections":
        int_id = df_nodes[df_nodes["name"] == sel_int_road]["intersection_id"].values[0]
        filtered_roads = filtered_roads[
            (filtered_roads["from_intersection_id"] == int_id) | 
            (filtered_roads["to_intersection_id"] == int_id)
        ]
    filtered_roads = filtered_roads[filtered_roads["lanes"] >= sel_lanes]

    st.write(f"Showing **{len(filtered_roads)}** road approaches:")
    st.dataframe(
        filtered_roads[["road_id", "from_intersection_id", "to_intersection_id", "road_name", "lanes", "length_m", "base_capacity_pcu_hr", "effective_capacity_pcu_hr", "data_provenance"]],
        use_container_width=True,
        height=400
    )

# TAB 3: SIGNAL PHASES
with tab3:
    st.markdown("#### Signal Phases & Directional Turning Movements")
    st.caption("Extracted movement rights: Thru, Left, Right, U-Turn, and Pedestrian clearance phases.")
    
    sel_int_phase = st.selectbox("Select Intersection for Phase Breakdown:", sorted(list(df_nodes["name"].unique())), key="phase_int")
    int_id_p = df_nodes[df_nodes["name"] == sel_int_phase]["intersection_id"].values[0]
    
    int_phases = df_phases[df_phases["intersection_id"] == int_id_p]
    if len(int_phases) > 0:
        st.dataframe(
            int_phases[["phase_id", "phase_number", "approach_direction", "movement_type", "is_pedestrian_phase", "lanes_served"]],
            use_container_width=True
        )
    else:
        st.info("No explicit sub-phases defined; using intersection default 3-phase split.")

# TAB 4: TIMING PLANS
with tab4:
    st.markdown("#### Official Bharat Electronics Limited (BEL) Time-of-Day Timing Plans")
    col_t1, col_t2 = st.columns([1, 1])
    sel_int_timing = col_t1.selectbox("Select Intersection:", sorted(list(df_nodes["name"].unique())), key="timing_int")
    
    int_id_t = df_nodes[df_nodes["name"] == sel_int_timing]["intersection_id"].values[0]
    int_timings = df_timings[df_timings["intersection_id"] == int_id_t]
    
    plans_available = sorted(list(int_timings["plan_name"].dropna().unique())) if len(int_timings) > 0 else []
    sel_plan = col_t2.selectbox("Select Time-of-Day Plan:", ["All Plans"] + plans_available)
    
    filtered_timings = int_timings.copy()
    if sel_plan != "All Plans":
        filtered_timings = filtered_timings[filtered_timings["plan_name"] == sel_plan]
        
    st.write(f"Showing **{len(filtered_timings)}** timing records:")
    st.dataframe(
        filtered_timings[["plan_name", "start_time", "end_time", "cycle_length_sec", "phase_number", "green_duration_sec", "amber_sec", "red_sec", "validation_status"]],
        use_container_width=True,
        height=350
    )

# TAB 5: EXTRACTION AUDIT
with tab5:
    st.markdown("#### Dataset Extraction Quality & Error Audit")
    st.markdown("""
    All 118 PDF files underwent rigorous automated validation:
    - **Referential Integrity:** Every approach connects valid intersections.
    - **Cycle Conservation:** $\\sum g_{jp} + \\sum (Y + R_{\\text{all}}) = C_j \\pm 2\\text{s}$.
    - **CAD Character Condensation:** Deduplicated layered font streams from AutoCAD exports.
    """)
    if len(df_errors) > 0:
        st.dataframe(df_errors, use_container_width=True)
    else:
        st.success("Zero unhandled extraction errors. All 118 PDF documents parsed and validated successfully.")

# TAB 6: MANUAL CORRECTION
with tab6:
    st.markdown("#### Interactive Manual Plan Adjustment & Review")
    st.markdown("Test manual timing corrections and observe immediate cycle time validation:")
    
    mc_c1, mc_c2, mc_c3 = st.columns(3)
    c_int = mc_c1.selectbox("Select Junction to Adjust:", sorted(list(df_nodes["name"].unique())), key="mc_int")
    c_cycle = mc_c2.number_input("Target Cycle Length (s):", min_value=60, max_value=240, value=120, step=5)
    c_peds = mc_c3.number_input("Pedestrian Clearance (s):", min_value=5, max_value=30, value=10, step=1)
    
    p1, p2, p3 = st.columns(3)
    g1 = p1.slider("Phase 1 Green (s):", 5, 80, 40)
    g2 = p2.slider("Phase 2 Green (s):", 5, 80, 35)
    g3 = p3.slider("Phase 3 Green (s):", 5, 80, 23)
    
    yellow_all = 3 * 4.0 # 3 phases * 4s lost time
    sum_allocated = g1 + g2 + g3 + c_peds + yellow_all
    
    if abs(sum_allocated - c_cycle) <= 1.0:
        st.success(f"✅ Perfectly Balanced: Allocated = {sum_allocated}s, Stated Cycle = {c_cycle}s")
    else:
        diff = sum_allocated - c_cycle
        st.warning(f"⚠️ Imbalance: Allocated = {sum_allocated}s, Target Cycle = {c_cycle}s (Difference: {diff:+0.1f}s)")

render_workflow_navigation(
    prev_page="pages/1_Overview.py",
    prev_label="01. Corpus Architecture",
    next_page="pages/3_Network_Visualization.py",
    next_label="03. Network Topology Map"
)
