"""
Page 4: Alternative Route Comparison & Resilient Dispatch.
Ambulance Route Optimization — Bengaluru.

Implements Operations Research Alternative Route Modeling:
- Yen's K-Shortest Loopless Paths Algorithm ($K=1..5$).
- Divergence Junction & Root Path Tracking.
- Detour Factor & Link Overlap (Jaccard Similarity).
- Corridor Blockage & Network Resilience Simulation.
- Multi-layer Interactive GIS Map with distinctive route styling.
"""

import os
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
    load_all_datasets,
    load_gis_network,
    load_ambulance_router,
    load_hospital_data
)
from components.gis_map import (
    create_ambulance_route_map,
    render_gis_map_in_streamlit
)
from src.network.ambulance_router import (
    PROFILE_MINIMUM_TIME,
    PROFILE_TIME_PLUS_SIGNAL,
    PROFILE_COMBINED_TRAFFIC_SIGNAL,
    PROFILE_SHORTEST_DISTANCE
)

st.set_page_config(
    page_title="Alternative Route Comparison | Bengaluru GIS",
    page_icon="🔀",
    layout="wide"
)
load_custom_css()

render_header(
    title="Alternative Route Comparison & Network Resilience",
    subtitle="Yen's K-Shortest Loopless Paths: Divergence Analysis, Link Overlap, Detour Bounds & Incident Bypass",
    badge_text="Operations Research — K-Shortest Paths",
    current_page="pages/4_Alternative_Route_Comparison.py"
)

# Load cached data & routing engine
router = load_ambulance_router()
G_di = router.graph_di
gis_mgr, roads_gis, df_nodes_gis = load_gis_network()
df_hospitals, df_connections = load_hospital_data()

st.markdown(r"""
<div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-left: 4px solid #0284C7; padding: 0.85rem 1.1rem; border-radius: 6px; margin-bottom: 1.2rem; font-size: 0.85rem; line-height: 1.5; color: #0F172A; box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);">
    <b style="color: #0284C7;">📐 YEN'S K-SHORTEST LOOPLESS PATHS ALGORITHM (Yen, 1971):</b><br/>
    In emergency vehicle operations, dispatchers cannot rely solely on a single optimal route. Road blockages,
    flash flooding, or mass-casualty traffic jams require pre-calculated, loopless alternative bypasses.
    Yen's algorithm identifies the $K$-best paths by systematically branching at <i>spur nodes</i> and pruning root-path sub-edges,
    strictly preventing cyclical loops ($\mathcal{O}(K \cdot |V| \cdot (|E| + |V| \log |V|))$).
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Dispatch Controls
# ---------------------------------------------------------
c_c1, c_c2, c_c3 = st.columns([1.2, 1.4, 1.2])

sorted_nodes = sorted(list(G_di.nodes()))
node_names = {n: f"{n} — {G_di.nodes[n].get('name', n)}" for n in sorted_nodes}

with c_c1:
    st.markdown("#### 1. Dispatch Origin")
    preset_origins = [
        "INT_001_RAJARAJESHWARI_JUNCTION",
        "INT_006_RAJALAXMIKALYANAMANTAPA",
        "INT_068_MADIWALACHECKPOST_JUNCTIO",
        "INT_010_B_M_SHRI_CMH_100FT_ROAD_J",
        "INT_052_PRASANNA_JUNCTION"
    ]
    u_sel = st.selectbox(
        "Ambulance Origin Station:",
        sorted_nodes,
        index=sorted_nodes.index(preset_origins[0]),
        format_func=lambda x: node_names.get(x, x)
    )

with c_c2:
    st.markdown("#### 2. Destination Facility / Junction")
    dest_mode = st.radio("Destination Mode:", ["Hospital Facility", "Network Intersection"], horizontal=True)
    if dest_mode == "Hospital Facility":
        hosp_ids = df_hospitals["hospital_id"].tolist()
        hosp_dict = {
            r["hospital_id"]: f"{r['hospital_name']} ({r['verification_status']})"
            for _, r in df_hospitals.iterrows()
        }
        h_sel = st.selectbox("Destination Hospital:", hosp_ids, index=0, format_func=lambda hid: hosp_dict.get(hid, hid))
        c_match = df_connections[df_connections["hospital_id"] == h_sel]
        v_sel = c_match.iloc[0]["nearest_intersection_id"] if not c_match.empty else sorted_nodes[-1]
    else:
        v_sel = st.selectbox("Destination Junction:", sorted_nodes, index=len(sorted_nodes) - 1, format_func=lambda x: node_names.get(x, x))

with c_c3:
    st.markdown("#### 3. Alternatives & Objective")
    k_val = st.slider("Number of Paths (K):", min_value=2, max_value=5, value=3)
    cost_prof = st.selectbox(
        "Cost Profile:",
        [PROFILE_COMBINED_TRAFFIC_SIGNAL, PROFILE_TIME_PLUS_SIGNAL, PROFILE_MINIMUM_TIME, PROFILE_SHORTEST_DISTANCE],
        format_func=lambda x: (
            "🚨 Combined Traffic + Signals" if x == PROFILE_COMBINED_TRAFFIC_SIGNAL
            else ("🚦 Signal-Aware Min Time" if x == PROFILE_TIME_PLUS_SIGNAL
            else ("⚡ Baseline Road Time" if x == PROFILE_MINIMUM_TIME else "📏 Shortest Distance"))
        )
    )

if u_sel == v_sel:
    st.error("Origin and Destination cannot be identical. Please choose distinct locations.")
    st.stop()

# ---------------------------------------------------------
# Compute K-Shortest Loopless Paths
# ---------------------------------------------------------
with st.spinner(f"Computing {k_val} loopless alternative paths via Yen's Algorithm..."):
    alt_paths = router.find_k_alternative_routes(u_sel, v_sel, K=k_val, profile=cost_prof)

if not alt_paths:
    st.error("No feasible paths found between the selected origin and destination.")
    st.stop()

primary_path = alt_paths[0]
p1_nodes = set(primary_path["path_nodes"])
p1_edges = {(primary_path["path_nodes"][i], primary_path["path_nodes"][i+1]) for i in range(len(primary_path["path_nodes"])-1)}

# Metric Cards
m_c1, m_c2, m_c3, m_c4 = st.columns(4)
with m_c1:
    p_time = primary_path.get("total_time_min", 0.0)
    p_dist = primary_path.get("total_distance_km", 0.0)
    p_spd = primary_path.get("average_speed_kmh", 0.0)
    render_metric(m_c1, "Primary Route Time", f"{p_time:.2f} min", f"{p_dist:.2f} km @ {p_spd:.1f} km/h", "green")
with m_c2:
    alt1 = alt_paths[1] if len(alt_paths) > 1 else primary_path
    alt1_time = alt1.get("total_time_min", p_time)
    detour1 = alt1.get("detour_factor_pct", 0.0)
    render_metric(m_c2, "Alternative 1 Time", f"{alt1_time:.2f} min", f"+{detour1:.1f}% Detour Penalty", "normal")
with m_c3:
    alt_max = alt_paths[-1]
    detour_max = alt_max.get("detour_factor_pct", 0.0)
    alt_max_time = alt_max.get("total_time_min", p_time)
    render_metric(m_c3, f"Alternative {len(alt_paths)-1} Time", f"{alt_max_time:.2f} min", f"+{detour_max:.1f}% Detour Penalty", "warning")
with m_c4:
    render_metric(m_c4, "Algorithm Used", "Yen's K-Shortest", "Strict Loopless Formulation", "normal")

# ---------------------------------------------------------
# Multi-Alternative GIS Map
# ---------------------------------------------------------
st.markdown("### 🗺️ Multi-Alternative GIS Route Overlay")
st.caption("Each loopless alternative path is rendered in a distinct color. Toggle layers in top-right control to inspect individual paths.")

origin_dict = {"latitude": G_di.nodes[u_sel]["lat"], "longitude": G_di.nodes[u_sel]["lon"]}
dest_dict = {"latitude": G_di.nodes[v_sel]["lat"], "longitude": G_di.nodes[v_sel]["lon"]}

m_alt = create_ambulance_route_map(
    primary_route=primary_path,
    alternative_routes=alt_paths,
    roads=roads_gis,
    origin_info=origin_dict,
    destination_info=dest_dict,
    show_background_roads=True,
    show_legend=True
)
render_gis_map_in_streamlit(m_alt, height=560, key=f"alt_map_{u_sel}_{v_sel}_{k_val}_{cost_prof}")

# ---------------------------------------------------------
# Tabular Comparison & Overlap Metrics
# ---------------------------------------------------------
st.markdown("### 📋 Comparative Alternative Route Breakdown")

comp_data = []
for alt in alt_paths:
    rank = alt.get("rank", 1)
    nodes = alt.get("path_nodes", [])
    edges = {(nodes[i], nodes[i+1]) for i in range(len(nodes)-1)}
    
    # Jaccard link similarity with primary path
    if p1_edges and edges:
        jaccard_overlap = len(p1_edges.intersection(edges)) / len(p1_edges.union(edges)) * 100.0
    else:
        jaccard_overlap = 100.0

    alt_t = alt.get("total_time_min", 0.0)
    alt_delta = alt.get("delta_time_min", alt.get("time_delta_from_primary_min", 0.0))
    alt_detour = alt.get("detour_factor_pct", 0.0)
    alt_dist = alt.get("total_distance_km", 0.0)
    p_dist_val = primary_path.get("total_distance_km", 0.0)

    comp_data.append({
        "Option": f"Primary Route (k={rank})" if rank == 1 else f"Alternative {rank-1} (k={rank})",
        "Travel Time (min)": f"{alt_t:.2f}",
        "Time Delta (min)": f"+{alt_delta:.2f}" if rank > 1 else "Baseline",
        "Detour Factor": f"+{alt_detour:.1f}%" if rank > 1 else "1.00x",
        "Distance (km)": f"{alt_dist:.2f}",
        "Distance Delta (km)": f"+{alt_dist - p_dist_val:.2f}" if rank > 1 else "Baseline",
        "Segments": alt.get("num_segments", len(nodes)-1),
        "Avg Speed (km/h)": f"{alt.get('average_speed_kmh', 0.0):.1f}",
        "Link Overlap with Primary": f"{jaccard_overlap:.1f}%",
        "Divergence Junction": alt.get("divergence_node_name", alt.get("divergence_description", "Origin"))
    })

st.dataframe(pd.DataFrame(comp_data), width="stretch", hide_index=True)

# ---------------------------------------------------------
# Incident & Corridor Blockage Simulation
# ---------------------------------------------------------
st.markdown("---")
st.markdown("### 🚨 Road Blockage & Incident Bypass Simulation")
st.caption("Simulate an unexpected arterial closure (e.g. fallen tree, severe crash, VIP convoy). The engine dynamically bypasses the blocked link:")

p_edges_list = primary_path.get("path_edges", [])
if p_edges_list:
    edge_options = [f"Step {e['step']}: {e.get('from_name', e['from_node'])} → {e.get('to_name', e['to_node'])} ({e.get('road_name')})" for e in p_edges_list]
    sel_edge_idx = st.selectbox("Select Road Segment on Primary Route to Block:", range(len(edge_options)), format_func=lambda i: edge_options[i])
    
    blocked_edge = p_edges_list[sel_edge_idx]
    b_u, b_v = blocked_edge["from_node"], blocked_edge["to_node"]
    
    if st.button("🚧 Simulate Incident Blockage & Re-Route", type="primary"):
        # Create temp graph copy without this edge
        G_blocked = G_di.copy()
        if G_blocked.has_edge(b_u, b_v):
            G_blocked.remove_edge(b_u, b_v)
        
        from src.network.ambulance_router import AmbulanceRouter
        temp_router = AmbulanceRouter(graph_di=G_blocked)
        reroute_res = temp_router.find_shortest_path(u_sel, v_sel, profile=cost_prof)
        
        if reroute_res["status"] == "OPTIMAL":
            t_orig = primary_path["total_time_min"]
            t_new = reroute_res["total_time_min"]
            diff_t = round(t_new - t_orig, 2)
            
            st.success(f"""
            ✅ **Resilient Bypass Identified!**  
            Primary route segment `{blocked_edge['road_name']}` blocked.  
            - **New Route Travel Time:** **{t_new:.2f} min** (+{diff_t:.2f} min delay, +{(diff_t/t_orig*100):.1f}%)  
            - **New Distance:** **{reroute_res['total_distance_km']:.2f} km** (was {primary_path['total_distance_km']:.2f} km)  
            - **Bypass Route Segments:** **{reroute_res['num_segments']} links**
            """)
        else:
            st.error("No alternative bypass path exists when this critical arterial bridge is severed.")

render_workflow_navigation(
    prev_page="pages/3_Ambulance_Route_Optimizer.py",
    prev_label="03. Route Optimizer",
    next_page="pages/5_Signal_Delay_Analysis.py",
    next_label="05. Signal Timing & Delays"
)
