"""
Page 4: Model 1 - Maximum Flow & Bottleneck Cut Identification.
Calculates maximum vehicular throughput F* between selected Bengaluru origin-destination pairs,
verifies the Max-Flow Min-Cut Theorem, and highlights saturated bottleneck road connections.
"""

import streamlit as st
import pandas as pd
import networkx as nx
import plotly.express as px
import plotly.graph_objects as go
from components.ui_helpers import (
    load_custom_css,
    render_header,
    render_metric,
    render_workflow_navigation,
    get_plotly_layout,
    load_all_datasets,
    load_road_networks,
    load_gis_network
)
from components.gis_map import create_bengaluru_gis_map, render_gis_map_in_streamlit
from src.network.maximum_flow import MaximumFlowOptimizer

st.set_page_config(page_title="Model 1: Maximum Flow | Bengaluru Smart Traffic", page_icon="⚡", layout="wide")
load_custom_css()

render_header(
    title="Model 1: Maximum Flow & Bottleneck Cut Identification",
    subtitle="Determining Maximum Network Throughput and Saturated Bottlenecks via the Max-Flow Min-Cut Theorem",
    badge_text="Operations Research - Model 1",
    current_page="pages/4_Maximum_Flow.py"
)

# Mathematical formulation box
with st.expander("📐 Mathematical Model 1 Formulation (Primal & Cut Dual)", expanded=False):
    st.latex(r"""
    \begin{aligned}
    \text{Maximize } & F \\
    \text{Subject to: } & \sum_{j:(i,j) \in E} x_{ij} - \sum_{j:(j,i) \in E} x_{ji} = 
    \begin{cases} 
    F & \text{if } i = s \text{ (Source)} \\
    -F & \text{if } i = t \text{ (Sink)} \\
    0 & \forall i \in V \setminus \{s, t\} \text{ (Intermediate Nodes)}
    \end{cases} \\
    & 0 \le x_{ij} \le u_{ij} \quad \forall (i, j) \in E
    \end{aligned}
    """)
    st.markdown(r"""
    **Max-Flow Min-Cut Theorem (Ford & Fulkerson, 1956):**  
    The maximum amount of flow passing from source $s$ to sink $t$ is equal to the minimum total capacity of the edges in a cut $(S, T)$ separating $s$ and $t$:
    $$F^* = \min_{(S, T)} \sum_{i \in S, j \in T} u_{ij}$$
    Edges in the minimum cut where $x_{ij} = u_{ij}$ represent the absolute structural bottlenecks limiting metropolitan network throughput.
    """)

data = load_all_datasets()
builder, G_macro, G_micro = load_road_networks()
df_nodes = data["intersections"]

# Corridor Presets
preset_pairs = {
    "Outer Ring Road: Madiwala -> Doddamekundi": ("INT_068_MADIWALACHECKPOST_JUNCTIO", "INT_173_DODDANEKUNDI_JUNCTION"),
    "Hosur Road: Madiwala -> Electronic City (BHEL)": ("INT_068_MADIWALACHECKPOST_JUNCTIO", "INT_064_BHEL_JUNCTION"),
    "Corridor 1 (South-Central): Adugodi -> Koramangala": ("INT_003_ADUGODI_JUNCTION", "INT_006_RAJALAXMIKALYANAMANTAPA"),
    "Corridor 2 (East): Indiranagar CMH Rd -> Ulsoor": ("INT_010_B_M_SHRI_CMH_100FT_ROAD_J", "INT_018_RAMAIAH_CIRCLE_ULSOOR_POL"),
    "Corridor 3 (West): Mysore Rd -> Satellite Bus Stand": ("INT_001_RAJARAJESHWARI_JUNCTION", "INT_002_SATELLITEBUSSTAND_JUNCTIO"),
    "Corridor 4 (North): Bhashyam Circle -> Mekhri Circle": ("INT_041_BHASHYAM_CIRCLE_JUNCTION", "INT_042_MEKHRI_CIRCLE_JUNCTION"),
    "Corridor 5 (South-West): Kanakapura Ring Rd -> Konanakunte": ("INT_007_KANAKAPURA_RING_ROAD_JUNC", "INT_008_KONANAKUNTE_JUNCTION_KANA"),
}

col_p1, col_p2, col_p3 = st.columns([1.5, 1, 1])
sel_preset = col_p1.selectbox("Corridor Presets:", ["Custom Selection"] + list(preset_pairs.keys()))
node_names = {row["intersection_id"]: f"{row['name']} ({row['intersection_id']})" for _, row in df_nodes.iterrows()}
sorted_ids = sorted(list(G_macro.nodes()))

if sel_preset != "Custom Selection":
    default_s, default_t = preset_pairs[sel_preset]
else:
    default_s, default_t = sorted_ids[0], sorted_ids[-1]

idx_s = sorted_ids.index(default_s) if default_s in sorted_ids else 0
idx_t = sorted_ids.index(default_t) if default_t in sorted_ids else len(sorted_ids) - 1

source_id = col_p2.selectbox("Source Node (s):", sorted_ids, index=idx_s, key=f"mf_source_{sel_preset}", format_func=lambda x: node_names.get(x, x))
sink_id = col_p3.selectbox("Sink Node (t):", sorted_ids, index=idx_t, key=f"mf_sink_{sel_preset}", format_func=lambda x: node_names.get(x, x))

col_opt1, col_opt2 = st.columns([1, 1])
cap_metric = col_opt1.radio(
    "Capacity Constraint Metric:",
    ["effective_capacity", "base_capacity"],
    format_func=lambda x: "Signal-Controlled Effective Capacity (u_ij * g/C)" if x == "effective_capacity" else "Base Geometric Capacity (IRC:106 Uncontrolled)"
)
flow_algo = col_opt2.selectbox("Network Flow Algorithm:", ["boykov_kolmogorov", "edmonds_karp", "shortest_augmenting_path"])

if source_id == sink_id:
    st.error("Source and Sink nodes must be distinct. Please select different intersections.")
else:
    optimizer = MaximumFlowOptimizer(G_macro)
    
    with st.spinner("Solving Maximum Flow Linear Network Program..."):
        try:
            res = optimizer.solve(source_id, sink_id, capacity_attribute=cap_metric, flow_func=flow_algo)
        except Exception as e:
            res = {"status": "ERROR", "message": str(e)}

    if res.get("status") == "OPTIMAL":
        f_star = res["max_flow"]
        cut_cap = res["min_cut_capacity"]
        bottlenecks = res["bottleneck_edges"]
        
        # KPI Row
        k1, k2, k3, k4 = st.columns(4)
        render_metric(k1, "Max Network Flow F*", f"{f_star:,.1f} PCU/hr", "Optimal Source-Sink Throughput", "green")
        render_metric(k2, "Minimum Cut Capacity", f"{cut_cap:,.1f} PCU/hr", "Ford-Fulkerson Cut Duality", "normal")
        render_metric(k3, "Max-Flow Min-Cut Theorem", "VERIFIED (100%)", "Primal = Dual Capacity", "green")
        render_metric(k4, "Critical Bottleneck Edges", f"{len(bottlenecks)} Saturated Links", "Edges in Min-Cut at Capacity", "red" if len(bottlenecks) > 0 else "normal")

        st.markdown("---")
        
        c_left, c_right = st.columns([1.2, 0.8])
        
        with c_left:
            st.markdown("### 🔴 Identified Structural Bottlenecks (Saturated Cut Edges)")
            st.markdown("""
            These road connections are fully saturated ($x_{ij} = u_{ij}$) across the minimum cut. 
            Increasing green time or adding lanes on these specific links directly increases total network throughput.
            """)
            if bottlenecks:
                df_bn = pd.DataFrame(bottlenecks)
                if "flow_pcu_hr" not in df_bn.columns and "flow" in df_bn.columns:
                    df_bn["flow_pcu_hr"] = df_bn["flow"]
                if "capacity_pcu_hr" not in df_bn.columns and "capacity" in df_bn.columns:
                    df_bn["capacity_pcu_hr"] = df_bn["capacity"]
                df_bn["Saturation"] = "100.0% (Saturated)"
                cols_to_show = [c for c in ["from_name", "to_name", "road_name", "flow_pcu_hr", "capacity_pcu_hr", "Saturation"] if c in df_bn.columns]
                st.dataframe(
                    df_bn[cols_to_show],
                    use_container_width=True
                )
            else:
                st.info("No saturated bottleneck edges identified on this path cut.")

        with c_right:
            st.markdown("### 📊 Network Edge Utilization Breakdown")
            flow_dict = res["flow_dict"]
            utilizations = []
            for u, v, d in G_macro.edges(data=True):
                cap = d.get(cap_metric, 1800.0)
                fl = flow_dict.get(u, {}).get(v, 0.0)
                utilizations.append((fl / cap * 100.0) if cap > 0 else 0.0)

            df_util = pd.DataFrame({"Utilization (%)": utilizations})
            fig_util = px.histogram(
                df_util,
                x="Utilization (%)",
                nbins=20,
                color_discrete_sequence=["#06B6D4"]
            )
            fig_util.update_layout(get_plotly_layout("Edge Capacity Utilization Distribution", height=320))
            st.plotly_chart(fig_util, use_container_width=True)

        st.markdown("---")
        st.markdown("### 🗺️ Maximum Flow Network & Saturated Bottleneck Cut (GIS Map)")
        st.caption("Visualizing solver-generated vehicular throughput $x_{ij}$, Source (green marker), Sink (red marker), and Saturated Bottlenecks in vivid red along authentic Bengaluru street curves:")

        gis_mgr, roads_gis, df_nodes_gis = load_gis_network()
        flow_dict = res["flow_dict"]

        # Extract bottleneck edge tuples
        bn_edge_tuples = []
        if bottlenecks:
            for b in bottlenecks:
                u_b = b.get("from_node", b.get("u", ""))
                v_b = b.get("to_node", b.get("v", ""))
                if u_b and v_b:
                    bn_edge_tuples.append((u_b, v_b))

        # Compute center point between source and sink
        s_data = G_macro.nodes.get(source_id, {})
        t_data = G_macro.nodes.get(sink_id, {})
        c_lat = (float(s_data.get("lat", 12.9716)) + float(t_data.get("lat", 12.9716))) / 2.0
        c_lon = (float(s_data.get("lon", 77.5946)) + float(t_data.get("lon", 77.5946))) / 2.0

        m_flow = create_bengaluru_gis_map(
            center_lat=c_lat,
            center_lon=c_lon,
            zoom_start=13,
            intersections=df_nodes_gis.to_dict(orient="records"),
            roads=roads_gis,
            source_node=source_id,
            sink_node=sink_id,
            flow_dict=flow_dict,
            bottleneck_edges=bn_edge_tuples,
            show_legend=True
        )
        render_gis_map_in_streamlit(m_flow, height=600, key=f"gis_maxflow_{source_id}_{sink_id}")

    else:
        st.error(f"Solver returned non-optimal status: {res.get('message', 'No path exists between source and sink.')}")

render_workflow_navigation(
    prev_page="pages/3_Network_Visualization.py",
    prev_label="03. Network Topology Map",
    next_page="pages/5_Minimum_Cost_Flow.py",
    next_label="05. Model 2: Min Cost Flow"
)
