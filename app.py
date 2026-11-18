"""
Bengaluru Smart Traffic Optimizer - Operations Research Dashboard
Root Application & Executive Portal.
"""

import streamlit as st
import pandas as pd
from components.ui_helpers import (
    load_custom_css,
    render_header,
    render_metric,
    render_workflow_navigation,
    load_all_datasets,
    load_road_networks
)

st.set_page_config(
    page_title="Bengaluru Smart Traffic Optimizer | Operations Research",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply unified modern dark theme
load_custom_css()

# Render Executive Header and Custom Navigation Drawer
render_header(
    title="Bengaluru Smart Traffic Optimizer",
    subtitle="Multi-Intersection Network Flow Optimization & Queue-Minimizing Signal Control",
    badge_text="Operations Research Suite",
    current_page="app.py"
)

# Load underlying dataset and road networks
try:
    data = load_all_datasets()
    builder, G_macro, G_micro = load_road_networks()
    n_nodes = G_macro.number_of_nodes()
    n_edges = G_macro.number_of_edges()
    n_intersections = len(data["intersections"])
    n_timings = len(data["timings"])
except Exception as e:
    st.error(f"Error loading system graph and dataset: {e}")
    n_nodes, n_edges, n_intersections, n_timings = 0, 0, 0, 0

# Executive KPI Metrics Row
c1, c2, c3, c4 = st.columns(4)
render_metric(c1, "Intersections Geocoded", f"{n_intersections:,}", "Level 1 Network Nodes", "normal")
render_metric(c2, "Arterial Road Links", f"{n_edges:,}", "Directed Strongly Connected Edges", "normal")
render_metric(c3, "Extracted Timing Plans", f"{n_timings:,}", "BEL CAD & Police Schedules", "green")
render_metric(c4, "OR Network Models", "4 Coupled", "Feedback Capacity Loop", "normal")

st.markdown("---")

# Main Academic Problem Statement & Core Architecture
col_left, col_right = st.columns([1.2, 0.8])

with col_left:
    st.markdown("""
    ### Academic Research Scope & Problem Formulation
    
    In high-density metropolitan road networks such as Bengaluru, isolated, uncoordinated signal timings 
    generate severe downstream queue spillback, intersection starvation, and system-wide traffic breakdown. 
    
    This computational framework implements **Four Interconnected Operations Research Network Models** to optimize vehicular flow 
    across 226 geocoded intersections derived from 118 official Bharat Electronics Limited (BEL) & Bengaluru 
    Traffic Police (BTP) signal engineering plans:
    
    1. **Model 1: Maximum Flow (Ford-Fulkerson / Dinic)**  
       Calculates the theoretical upper bound of hourly vehicular throughput ($F^*$) across arterial cuts, identifying saturated bottleneck links via the Max-Flow Min-Cut Theorem.
    
    2. **Model 2: Minimum Cost Flow (Network Simplex)**  
       Solves the optimal multicommodity mass-balance traffic allocation $\\min \\sum c_{ij} x_{ij}$, minimizing total system travel delay while strictly satisfying link capacities $x_{ij} \\le u_{ij}$.
    
    3. **Model 3: Shortest Path Routing (Dijkstra)**  
       Computes minimum-impedance routing trajectories between major activity centres and quantifies travel-time savings after signal timing reconfiguration.
    
    4. **Model 4: Signal Timing Linear Programming (SciPy HiGHS)**  
       Optimizes phase green splits $g_{jp}$ to minimize residual queues subject to cycle time conservation $\\sum g_{jp} + L_j = C_j$, minimum clearance intervals, and saturation flow rates.
    
    **The Feedback Capacity Loop:** Model 4's optimized green splits update effective link capacities $u_{ij} = s_{ij} \\times (g_{jp} / C_j)$ and Webster delay impedances $c_{ij}$, which directly re-parameterize Models 1, 2, and 3 for iterative equilibrium.
    """)

with col_right:
    st.markdown("""
    ### Key Metropolitan Study Corridors
    The mathematical models are calibrated against five key Bengaluru arterial corridors:
    
    - **Corridor 1 (South-Central Arterial):** Adugodi $\\to$ Koramangala $\\to$ Wilson Garden $\\to$ Dairy Circle  
    - **Corridor 2 (East Corridor):** Indiranagar $\\to$ CMH Road $\\to$ Old Madras Road $\\to$ Frazer Town  
    - **Corridor 3 (West Corridor):** Mysore Road $\\to$ Byatarayanapura $\\to$ Vijayanagar  
    - **Corridor 4 (North Corridor):** Sadashivanagar $\\to$ Bhashyam Circle $\\to$ Mekhri Circle $\\to$ Hebbal  
    - **Corridor 5 (South-West Corridor):** Kanakapura Road $\\to$ Banashankari $\\to$ Konanakunte  
    - **Outer Ring Road & Hosur Highway:** Central Silk Board $\\to$ Bellandur $\\to$ Mahadevapura $\\to$ Electronic City  
    
    ---
    #### Linear Workflow Navigation
    Use the **sidebar navigation** or the workflow switcher below to step through each module sequentially from data parsing to mathematical optimality proofs.
    """)

st.markdown("---")

# Module Overview Grid with Direct Interactive Links
st.markdown("### Operations Research Module Directory")
m1, m2, m3 = st.columns(3)

with m1:
    st.markdown("""
    <div class="or-card">
        <h4 style="color:#06B6D4; margin-top:0; font-size:1.05rem;">Phase I: Data & Topology</h4>
        <p style="font-size:0.86rem; color:#94A3B8; line-height:1.5;">
            Inspect 118 PDF/CAD signal plans, approach geometry, time-of-day phase schedules, and explore the dual-level macro/micro directed graph.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/1_Overview.py", label="Explore Corpus Overview", icon="📊", use_container_width=True)
    st.page_link("pages/3_Network_Visualization.py", label="View Network Topology", icon="🗺️", use_container_width=True)

with m2:
    st.markdown("""
    <div class="or-card">
        <h4 style="color:#10B981; margin-top:0; font-size:1.05rem;">Phase II: Flow & Routing</h4>
        <p style="font-size:0.86rem; color:#94A3B8; line-height:1.5;">
            Solve maximum network capacity ($F^*$), identify saturated min-cut bottlenecks, and allocate equilibrium traffic via Network Simplex.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/4_Maximum_Flow.py", label="Run Model 1: Maximum Flow", icon="⚡", use_container_width=True)
    st.page_link("pages/5_Minimum_Cost_Flow.py", label="Run Model 2: Min Cost Flow", icon="⚖️", use_container_width=True)

with m3:
    st.markdown("""
    <div class="or-card">
        <h4 style="color:#F59E0B; margin-top:0; font-size:1.05rem;">Phase III: Optimization & Proofs</h4>
        <p style="font-size:0.86rem; color:#94A3B8; line-height:1.5;">
            Optimize green splits using SciPy HiGHS LP, compare Dijkstra route travel times, and execute meso-queue dynamic simulations.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/7_Signal_Optimization.py", label="Run Model 4: Signal Timing LP", icon="🚦", use_container_width=True)
    st.page_link("pages/9_Analytics.py", label="Stress Testing & Benchmarks", icon="📈", use_container_width=True)

# Sequential Workflow Switcher
render_workflow_navigation(
    next_page="pages/1_Overview.py",
    next_label="01. Corpus Architecture"
)
