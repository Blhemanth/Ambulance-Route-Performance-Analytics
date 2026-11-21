"""
Page 5: Model 2 - Minimum Cost Flow Optimization.
Determines optimal vehicular traffic-flow allocation that minimizes total network transportation cost
subject to node supply/demand mass balance and link capacity constraints.
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
from src.network.minimum_cost_flow import MinimumCostFlowOptimizer
from src.network.maximum_flow import MaximumFlowOptimizer

st.set_page_config(page_title="Model 2: Minimum Cost Flow | Bengaluru Smart Traffic", page_icon="⚖️", layout="wide")
load_custom_css()

render_header(
    title="Model 2: Minimum Cost Flow Optimization",
    subtitle="Optimal Network Equilibrium Minimizing Total Vehicle Delay Subject to Mass Balance Constraints",
    badge_text="Operations Research - Model 2",
    current_page="pages/5_Minimum_Cost_Flow.py"
)

with st.expander("📐 Mathematical Model 2 Formulation (Network Simplex)", expanded=False):
    st.latex(r"""
    \begin{aligned}
    \text{Minimize } & Z = \sum_{(i,j) \in E} c_{ij} \cdot x_{ij} \\
    \text{Subject to: } & \sum_{j:(i,j) \in E} x_{ij} - \sum_{j:(j,i) \in E} x_{ji} = b_i \quad \forall i \in V \quad \text{(Mass Balance)} \\
    & 0 \le x_{ij} \le u_{ij} \quad \forall (i, j) \in E \quad \text{(Capacity Bounds)} \\
    & \sum_{i \in V} b_i = 0 \quad \text{(Feasibility Mass Conservation)}
    \end{aligned}
    """)
    st.markdown("""
    Where:
    - $c_{ij}$: Generalized transportation cost (travel time + signal delay in veh-min).
    - $x_{ij}$: Flow assigned to link $(i, j)$ in PCU/hr.
    - $b_i$: Net vehicular supply ($b_i > 0$), demand ($b_i < 0$), or transshipment node ($b_i = 0$).
    - $u_{ij}$: Effective link capacity under signal green splits.
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
    default_s, default_t = sorted_ids[0], sorted_ids[1]

idx_s = sorted_ids.index(default_s) if default_s in sorted_ids else 0
idx_t = sorted_ids.index(default_t) if default_t in sorted_ids else 1

origin_node = col_p2.selectbox("Origin Supply Node (b_s > 0):", sorted_ids, index=idx_s, key=f"mcf_orig_{sel_preset}", format_func=lambda x: node_names.get(x, x))
dest_node = col_p3.selectbox("Destination Demand Node (b_t < 0):", sorted_ids, index=idx_t, key=f"mcf_dest_{sel_preset}", format_func=lambda x: node_names.get(x, x))

col_opt1, col_opt2 = st.columns([1, 1])
trip_volume = col_opt1.number_input("Vehicular Demand Volume (PCU/hr):", min_value=100.0, max_value=15000.0, value=1200.0, step=100.0)
cost_metric = col_opt2.radio(
    "Transportation Cost Metric (c_ij):",
    ["cost", "free_flow_time_min"],
    format_func=lambda x: "Generalized Travel Time (Free Flow + Signal Delay)" if x == "cost" else "Free-Flow Time Only"
)

if origin_node == dest_node:
    st.error("Origin and Destination cannot be the same junction.")
else:
    # 1. First evaluate theoretical maximum flow bound (Model 1 integration)
    mf_optimizer = MaximumFlowOptimizer(G_macro)
    with st.spinner("Computing network bottleneck capacity bound (Model 1)..."):
        mf_res = mf_optimizer.solve(origin_node, dest_node, capacity_attribute="effective_capacity")
        f_max = mf_res.get("max_flow", 1000.0)

    # 2. Check feasibility according to Hoffman's Circulation Theorem / Gale's Demand Theorem
    if f_max <= 0:
        st.error(f"Zero capacity exists between {origin_node} and {dest_node}. Cannot route flow.")
        effective_volume = 0.0
    elif trip_volume > f_max:
        st.warning(
            f"⚠️ **Demand Exceeds Maximum Network Throughput ($d = {trip_volume:,.0f} > F^* = {f_max:,.0f}$ PCU/hr)**: "
            f"By the Max-Flow Min-Cut Theorem, traffic across the minimum cut cannot exceed {f_max:,.0f} PCU/hr without unbounded queue spillback. "
            f"Network Simplex is allocating the feasible upper bound ($0.95 \\times F^* = {f_max * 0.95:,.0f}$ PCU/hr)."
        )
        effective_volume = max(1.0, min(trip_volume, f_max * 0.95))
    else:
        st.info(f"✅ Demand Volume ({trip_volume:,.0f} PCU/hr) is within structural network capacity bound ($F^* = {f_max:,.0f}$ PCU/hr).")
        effective_volume = trip_volume

    # 3. Build mass balance dictionary on macro network
    demands = {n: 0.0 for n in G_macro.nodes()}
    demands[origin_node] = float(effective_volume)
    demands[dest_node] = -float(effective_volume)

    optimizer = MinimumCostFlowOptimizer(G_macro)
    with st.spinner("Solving Network Simplex Optimal Flow Distribution..."):
        try:
            res = optimizer.solve(demands, capacity_attribute="effective_capacity", cost_attribute=cost_metric)
        except Exception as e:
            res = {"status": "ERROR", "message": str(e)}

    if res.get("status") == "OPTIMAL":
        tot_cost = res["total_system_cost_veh_min"]
        tot_vol = res["total_flow_volume"]
        congested = res["congested_edges"]
        flow_records = res["flow_records"]
        
        # KPI Row
        k1, k2, k3, k4 = st.columns(4)
        render_metric(k1, "Total Transportation Cost", f"{tot_cost:,.1f} veh-min", "Objective Function Value Z*", "green")
        avg_d_str = f"{(tot_cost / effective_volume):,.2f} min" if effective_volume > 0 else "0.00 min"
        render_metric(k2, "Avg Trip Delay / Vehicle", avg_d_str, "Per-Vehicle Cost", "normal")
        render_metric(k3, "Allocated Flow Demand", f"{effective_volume:,.0f} PCU/hr", f"Max Bound: {f_max:,.0f} PCU/hr", "normal")
        render_metric(k4, "Congested Links (v/c > 0.85)", f"{len(congested)} Links", "High Delay Approaches", "amber" if len(congested) > 0 else "green")

        st.markdown("---")
        
        c_left, c_right = st.columns([1.2, 0.8])
        
        with c_left:
            st.markdown("### 📋 Optimal Link Traffic Flow Allocation")
            st.caption("Active links bearing traffic flow determined by the Network Simplex primal algorithm:")
            active_flows = [r for r in flow_records if r["flow_pcu_hr"] > 0]
            if active_flows:
                df_act = pd.DataFrame(active_flows)
                st.dataframe(
                    df_act[["from_name", "to_name", "road_name", "flow_pcu_hr", "capacity_pcu_hr", "unit_cost", "total_link_cost", "utilization_pct"]],
                    use_container_width=True,
                    height=380
                )
            else:
                st.info("No flow assigned.")

        with c_right:
            st.markdown("### ⚠️ Link Congestion Analysis (v/c Ratio)")
            st.caption("Approaches with Volume-to-Capacity ratio exceeding 0.85 undergo non-linear queuing delays:")
            if congested:
                df_cong = pd.DataFrame(congested)
                st.dataframe(
                    df_cong[["road_name", "from_name", "to_name", "flow_pcu_hr", "capacity_pcu_hr", "utilization_pct"]],
                    use_container_width=True
                )
            else:
                st.success("All active road approaches operate below 85% capacity threshold.")

            # Pie chart of congestion states
            num_cong = len(congested)
            num_free = len(active_flows) - num_cong
            cong_pie = pd.DataFrame({
                "State": ["Operating Normal (v/c <= 0.85)", "Congested (v/c > 0.85)"],
                "Count": [max(0, num_free), num_cong]
            })
            fig_pie = px.pie(
                cong_pie, names="State", values="Count", hole=0.5,
                color="State",
                color_discrete_map={"Operating Normal (v/c <= 0.85)": "#22C55E", "Congested (v/c > 0.85)": "#EF4444"}
            )
            fig_pie.update_layout(get_plotly_layout("Flow Congestion Breakdown", height=240))
            st.plotly_chart(fig_pie, use_container_width=True)

        st.markdown("---")
        st.markdown("### 🗺️ Network Simplex Traffic Flow & Congestion Distribution (GIS Map)")
        st.caption("Active flow-bearing road segments with line thickness proportional to allocated volume $x_{ij}$, colored by volume-to-capacity congestion ratio ($v/c$):")

        gis_mgr, roads_gis, df_nodes_gis = load_gis_network()
        flow_dict = res["flow_dict"]

        # Extract congested edge tuples
        cong_edge_tuples = []
        if congested:
            for c in congested:
                u_c = c.get("from_node", "")
                v_c = c.get("to_node", "")
                if u_c and v_c:
                    cong_edge_tuples.append((u_c, v_c))

        # Center between origin and destination
        o_data = G_macro.nodes.get(orig_id, {})
        d_data = G_macro.nodes.get(dest_id, {})
        c_lat = (float(o_data.get("lat", 12.9716)) + float(d_data.get("lat", 12.9716))) / 2.0
        c_lon = (float(o_data.get("lon", 77.5946)) + float(d_data.get("lon", 77.5946))) / 2.0

        m_mcf = create_bengaluru_gis_map(
            center_lat=c_lat,
            center_lon=c_lon,
            zoom_start=13,
            intersections=df_nodes_gis.to_dict(orient="records"),
            roads=roads_gis,
            source_node=orig_id,
            sink_node=dest_id,
            flow_dict=flow_dict,
            bottleneck_edges=cong_edge_tuples,
            show_legend=True
        )
        render_gis_map_in_streamlit(m_mcf, height=600, key=f"gis_mcf_{orig_id}_{dest_id}")

    else:
        st.error(f"Network Simplex was unable to satisfy flow: {res.get('message', 'Capacity exceeded or disconnected path.')}")

render_workflow_navigation(
    prev_page="pages/4_Maximum_Flow.py",
    prev_label="04. Model 1: Maximum Flow",
    next_page="pages/6_Shortest_Path.py",
    next_label="06. Model 3: Shortest Path"
)
