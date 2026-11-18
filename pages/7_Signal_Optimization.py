"""
Page 7: Model 4 - Traffic Signal Timing Linear Programming.
Formulates and solves the queue-minimizing signal timing optimization problem using SciPy HiGHS,
evaluating baseline BEL signal timings against optimized green splits and Webster delay.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from components.ui_helpers import (
    load_custom_css,
    render_header,
    render_metric,
    render_workflow_navigation,
    get_plotly_layout,
    load_all_datasets
)
from src.optimization.signal_optimizer import SignalOptimizer

st.set_page_config(page_title="Model 4: Signal Optimization | Bengaluru Smart Traffic", page_icon="🚦", layout="wide")
load_custom_css()

render_header(
    title="Model 4: Traffic Signal Timing Linear Programming",
    subtitle="Queue-Minimizing Green Split Allocation via SciPy HiGHS Simplex Subject to Cycle Conservation",
    badge_text="Operations Research - Model 4",
    current_page="pages/7_Signal_Optimization.py"
)

with st.expander("📐 Mathematical Model 4 Formulation (Queue LP & Webster Delay)", expanded=False):
    st.latex(r"""
    \begin{aligned}
    \text{Minimize } & Z = \sum_{p=1}^P w_p \cdot Q_{p}^{\text{next}} - \epsilon \sum_{p=1}^P \left(\frac{q_p}{\sum q}\right) g_p \\
    \text{Subject to: } & \sum_{p=1}^{P_{\text{veh}}} g_p + L_{\text{total}} + g_{\text{ped}} = C \quad \text{(Cycle Time Conservation)} \\
    & Q_p^{\text{next}} + D_p = Q_p^{\text{curr}} + A_p \quad \forall p \in \{1,\dots,P_{\text{veh}}\} \quad \text{(Queue Conservation)} \\
    & D_p \le \left(\frac{s_p}{3600}\right) g_p \quad \forall p \in \{1,\dots,P_{\text{veh}}\} \quad \text{(Saturation Flow Departure Bound)} \\
    & g_{\min} \le g_p \le g_{\max} \quad \forall p \in \{1,\dots,P_{\text{veh}}\} \\
    & Q_p^{\text{next}} \ge 0, \quad D_p \ge 0
    \end{aligned}
    """)
    st.markdown(r"""
    Where:
    - $g_p$: Green light duration allocated to phase $p$ (seconds).
    - $C$: Fixed cycle duration from BEL engineering plans (seconds).
    - $A_p = \frac{q_p \cdot C}{3600}$: Vehicle arrivals per cycle.
    - $s_p = \text{lanes} \times 1800$: Saturation flow rate (PCU/hr).
    - $w_p$: Objective priority weight for phase $p$.
    """)

data = load_all_datasets()
df_nodes = data["intersections"]
df_timings = data["timings"]
df_phases = data["phases"]

col_sel1, col_sel2 = st.columns([1.5, 1])
sel_int_name = col_sel1.selectbox(
    "Select Intersection to Optimize:",
    sorted(list(df_nodes["name"].unique())),
    index=0
)

int_row = df_nodes[df_nodes["name"] == sel_int_name].iloc[0]
int_id = int_row["intersection_id"]
default_cycle = int(int_row.get("cycle_time_sec", 120))

# Get timing records for this junction
int_timings = df_timings[df_timings["intersection_id"] == int_id]
plan_names = sorted(list(int_timings["plan_name"].dropna().unique())) if len(int_timings) > 0 else []

sel_plan = col_sel2.selectbox(
    "Select Time-of-Day Plan:",
    plan_names if plan_names else ["Plan 1 (General Peak)"]
)

# Extract baseline green splits from timings
baseline_greens = {}
if len(int_timings) > 0 and sel_plan in plan_names:
    plan_subset = int_timings[int_timings["plan_name"] == sel_plan]
    for _, r in plan_subset.iterrows():
        p_no = int(r["phase_number"])
        baseline_greens[p_no] = float(r["green_duration_sec"])

if not baseline_greens:
    baseline_greens = {1: 45.0, 2: 35.0, 3: 20.0}

num_veh_phases = max(len(baseline_greens), 3)

st.markdown("---")
st.markdown("#### ⚙️ Operational Parameters & Approach Demands")

col_p1, col_p2, col_p3 = st.columns(3)
cycle_time = col_p1.number_input("Signal Cycle Time C (seconds):", min_value=60, max_value=240, value=default_cycle, step=5)
lost_time_phase = col_p2.number_input("Lost Time per Phase (Y + All-Red):", min_value=2.0, max_value=8.0, value=4.0, step=0.5)
min_green = col_p3.number_input("Minimum Green Bound (seconds):", min_value=5.0, max_value=25.0, value=10.0, step=1.0)

# Phase Demand Inputs
st.markdown("##### Directional Phase Demands & Geometry:")
phase_cols = st.columns(num_veh_phases)
phases_config = []
demands_dict = {}
weights_dict = {}

default_demands = [850.0, 620.0, 410.0, 300.0]

for i in range(num_veh_phases):
    p_no = i + 1
    with phase_cols[i]:
        st.markdown(f"**Phase {p_no}**")
        base_g = baseline_greens.get(p_no, 30.0)
        st.caption(f"Baseline Green: **{base_g:.0f}s**")
        d_val = st.number_input(
            f"Demand (PCU/hr):",
            min_value=50.0, max_value=3000.0,
            value=default_demands[i % len(default_demands)],
            step=50.0,
            key=f"dem_{int_id}_{p_no}"
        )
        lanes = st.selectbox(f"Lanes:", [1, 2, 3, 4], index=1, key=f"lanes_{int_id}_{p_no}")
        wt = st.slider(f"Priority Weight:", 1.0, 5.0, 1.0, step=0.5, key=f"wt_{int_id}_{p_no}")
        
        phases_config.append({
            "phase_number": p_no,
            "lanes": lanes,
            "is_pedestrian_phase": False
        })
        demands_dict[p_no] = float(d_val)
        weights_dict[p_no] = float(wt)

# Add pedestrian phase
phases_config.append({
    "phase_number": num_veh_phases + 1,
    "lanes": 1,
    "is_pedestrian_phase": True
})

st.markdown("---")

optimizer = SignalOptimizer()
with st.spinner("Solving SciPy HiGHS Queue-Minimizing Linear Program..."):
    res = optimizer.optimize_intersection_timings(
        intersection_name=sel_int_name,
        cycle_time=cycle_time,
        phases=phases_config,
        demands_pcu_hr=demands_dict,
        lost_time_per_phase=lost_time_phase,
        min_veh_green=min_green,
        ped_min_green=10.0,
        weights=weights_dict
    )

if res.get("is_optimal"):
    opt_greens = res.get("optimized_phase_greens", {})
    queues = res.get("residual_queues", {})
    departures = res.get("cycle_departures", res.get("departures", {}))
    caps = res.get("effective_capacities_pcu_hr", res.get("capacities_pcu_hr", {}))
    
    # Calculate Webster Delay for Baseline vs Optimized
    def compute_webster_delay(c_sec, g_sec, q_hr, s_hr):
        lambd = g_sec / c_sec if c_sec > 0 else 0.1
        cap = s_hr * lambd
        x = min(0.98, q_hr / cap) if cap > 0 else 0.98
        term1 = (c_sec * ((1.0 - lambd) ** 2)) / (2.0 * (1.0 - lambd * x))
        term2 = (x ** 2) / (2.0 * (q_hr / 3600.0) * (1.0 - x) + 1e-4)
        return max(5.0, term1 + term2)

    tot_base_delay = 0.0
    tot_opt_delay = 0.0
    tot_dem = sum(demands_dict.values())

    comparison_rows = []
    veh_phase_keys = sorted([int(k) for k in opt_greens.keys() if str(k).isdigit()])
    for p_no in veh_phase_keys:
        g_base = baseline_greens.get(p_no, 30.0)
        g_opt = opt_greens[p_no]
        q_p = demands_dict[p_no]
        lanes = next(p["lanes"] for p in phases_config if p["phase_number"] == p_no)
        s_p = lanes * 1800.0

        d_base = compute_webster_delay(cycle_time, g_base, q_p, s_p)
        d_opt = compute_webster_delay(cycle_time, g_opt, q_p, s_p)

        tot_base_delay += d_base * q_p
        tot_opt_delay += d_opt * q_p

        comparison_rows.append({
            "Phase": f"Phase {p_no}",
            "Demand (PCU/hr)": q_p,
            "Baseline Green (s)": round(g_base, 1),
            "Optimized Green (s)": round(g_opt, 1),
            "Green Delta (s)": round(g_opt - g_base, 1),
            "Residual Queue (veh)": round(queues.get(p_no, 0.0), 1),
            "Baseline Delay (s/veh)": round(d_base, 1),
            "Optimized Delay (s/veh)": round(d_opt, 1),
            "Delay Reduction (%)": round(((d_base - d_opt) / d_base * 100.0) if d_base > 0 else 0.0, 1)
        })

    avg_base_delay = tot_base_delay / tot_dem if tot_dem > 0 else 0.0
    avg_opt_delay = tot_opt_delay / tot_dem if tot_dem > 0 else 0.0
    avg_delay_savings = avg_base_delay - avg_opt_delay
    pct_delay_savings = (avg_delay_savings / avg_base_delay * 100.0) if avg_base_delay > 0 else 0.0

    # KPI Row
    k1, k2, k3, k4 = st.columns(4)
    render_metric(k1, "Baseline Webster Delay", f"{avg_base_delay:.1f} s/veh", "Original BEL Timing Plan", "normal")
    render_metric(k2, "Optimized Webster Delay", f"{avg_opt_delay:.1f} s/veh", "HiGHS LP Solution", "green")
    render_metric(k3, "Intersection Delay Savings", f"{avg_delay_savings:+.1f} s/veh", f"{pct_delay_savings:.1f}% Reduction", "green")
    render_metric(k4, "Total Cycle Allocation", f"{cycle_time}s", "100% Conserved", "normal")

    st.markdown("---")

    c_left, c_right = st.columns([1.2, 0.8])

    with c_left:
        st.markdown("### 📊 Green Split Allocation Comparison")
        st.caption("Phase green durations before and after Linear Programming optimization:")
        df_comp = pd.DataFrame(comparison_rows)

        fig_greens = go.Figure(data=[
            go.Bar(name="Baseline Green (s)", x=df_comp["Phase"], y=df_comp["Baseline Green (s)"], marker_color="#38BDF8"),
            go.Bar(name="Optimized Green (s)", x=df_comp["Phase"], y=df_comp["Optimized Green (s)"], marker_color="#22C55E")
        ])
        fig_greens.update_layout(barmode="group", **get_plotly_layout("Phase Green Splits (Baseline vs Optimized)", height=320))
        st.plotly_chart(fig_greens, use_container_width=True)

    with c_right:
        st.markdown("### ⏱️ Phase Delay Reduction")
        fig_delays = px.bar(
            df_comp,
            x="Phase",
            y=["Baseline Delay (s/veh)", "Optimized Delay (s/veh)"],
            barmode="group",
            color_discrete_sequence=["#F59E0B", "#22C55E"]
        )
        fig_delays.update_layout(get_plotly_layout("Vehicle Delay by Phase (s/veh)", height=320))
        st.plotly_chart(fig_delays, use_container_width=True)

    st.markdown("### 📋 Detailed Phase Optimization Summary Table")
    st.dataframe(df_comp, use_container_width=True)

    st.info("""
    🔄 **Operations Research Feedback Coupling:**  
    The optimized green splits above directly modify the network model parameters:
    - **Effective Link Capacity:** $u_{ij} = s_i \\times (g_i / C)$ is updated in Model 1 (Max Flow) and Model 2 (Min Cost Flow).
    - **Link Transportation Cost:** $c_{ij} = t_{\\text{free}} + d_{\\text{Webster}}$ is updated in Model 2 and Model 3 (Shortest Path).
    """)

else:
    st.error(f"HiGHS solver reported non-optimal state: {res.get('status')}")

render_workflow_navigation(
    prev_page="pages/6_Shortest_Path.py",
    prev_label="06. Model 3: Shortest Path",
    next_page="pages/8_Simulation_Centre.py",
    next_label="08. Dynamic Simulation"
)
