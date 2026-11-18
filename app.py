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
    load_all_datasets,
    load_road_networks
)

st.set_page_config(
    page_title="Bengaluru Smart Traffic Optimizer | Operations Research",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply unified dark theme
load_custom_css()

# Sidebar Navigation and Metadata
with st.sidebar:
    st.markdown("### 🚦 Optimization Engine")
    st.markdown("**Version:** 1.0.0-OR-Release")
    st.markdown("**Academic Discipline:** Operations Research")
    st.markdown("**Framework:** Network Models & Linear Programming")
    st.markdown("---")
    
    st.markdown("#### 🔬 Solvers Active")
    st.markdown("• **Max Flow:** NetworkX Boykov-Kolmogorov / Dinic")
    st.markdown("• **Min Cost Flow:** Network Simplex")
    st.markdown("• **Shortest Path:** Dijkstra's Algorithm")
    st.markdown("• **Signal LP:** SciPy HiGHS Simplex/Interior Point")
    st.markdown("---")
    
    st.markdown("#### 🛡️ Data Provenance Policy")
    st.caption("Every traffic demand and saturation parameter is classified into `ACTUAL`, `EXTERNAL`, `MEASURED`, `ESTIMATED`, or `SYNTHETIC`. Synthetic volumes are never represented as empirical police counts.")

# Render Executive Header
render_header(
    title="Bengaluru Smart Traffic Optimizer",
    subtitle="Traffic Signal Optimization Using Combined Network Models — Operations Research",
    badge_text="Operations Research Framework"
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
render_metric(c2, "Arterial Road Links", f"{n_edges:,}", "Directed Network Edges", "normal")
render_metric(c3, "Extracted Timing Plans", f"{n_timings:,}", "BEL CAD & Police Schedules", "green")
render_metric(c4, "OR Network Models", "4 Coupled", "Feedback Capacity Loop", "normal")

st.markdown("---")

# Main Academic Problem Statement & Core Architecture
col_left, col_right = st.columns([1.2, 0.8])

with col_left:
    st.markdown("""
    ### 🎯 Academic Objective & Research Scope
    
    In high-density metropolitan road networks such as Bengaluru, uncoordinated isolated signal timings 
    create severe queue spillback, intersection starvation, and network-wide gridlock. 
    
    This framework implements **Four Interconnected Operations Research Network Models** to optimize vehicular flow 
    across 226 geocoded intersections derived from 118 official Bharat Electronics Limited (BEL) & Bengaluru 
    Traffic Police (BTP) signal design drawings:
    
    1. **Model 1: Maximum Flow (Ford-Fulkerson / Dinic)**  
       Calculates the upper bound of hourly vehicular throughput ($F^*$) across corridor cuts, identifying saturated bottleneck links via the Max-Flow Min-Cut Theorem.
    
    2. **Model 2: Minimum Cost Flow (Network Simplex)**  
       Solves the optimal multicommodity mass-balance traffic allocation $\\min \\sum c_{ij} x_{ij}$ minimizing total vehicular travel delay while respecting capacity bounds $x_{ij} \\le u_{ij}$.
    
    3. **Model 3: Shortest Path (Dijkstra)**  
       Computes minimum-impedance routing between critical origin-destination pairs and quantifies travel-time savings after signal timing reconfiguration.
    
    4. **Model 4: Signal Timing Linear Programming (SciPy HiGHS)**  
       Optimizes phase green splits $g_{jp}$ to minimize residual queues subject to cycle conservation $\\sum g_{jp} + L_j = C_j$, minimum clearance bounds, and lane saturation capacities.
    
    **The Feedback Loop:** Model 4's optimized green splits update effective movement capacities $u_{ij}$ and Webster delay impedances $c_{ij}$, which directly re-parameterize Models 1, 2, and 3.
    """)

with col_right:
    st.markdown("""
    ### 🗺️ Study Corridors
    The framework evaluates five major congested Bengaluru arterial corridors:
    
    • **Corridor A (Outer Ring Road):** Silk Board $\\to$ HSR $\\to$ Bellandur $\\to$ Marathahalli $\\to$ Doddanekundi $\\to$ KR Puram  
    • **Corridor B (Old Airport Road):** Domlur Flyover $\\to$ Kodihalli $\\to$ HAL $\\to$ Marathahalli  
    • **Corridor C (Hosur Road):** Madiwala Checkpost $\\to$ St. John's $\\to$ Silk Board $\\to$ Electronic City  
    • **Corridor D (Indiranagar / CMH Road):** CMH Rd $\\to$ 100ft Rd $\\to$ Double Rd $\\to$ Swami Vivekananda Rd  
    • **Corridor E (Bannerghatta Road):** Dairy Circle $\\to$ Jayadeva $\\to$ Vega City $\\to$ Gottigere  
    
    ---
    #### 🚀 Navigate Multi-Page Modules
    Use the **sidebar page navigator** on the left to explore each model in detail, run interactive solvers, inspect datasets, and review sensitivity stress tests.
    """)

st.markdown("---")

# Module Overview Grid
st.markdown("### 📚 Operations Research Module Directory")
m1, m2, m3 = st.columns(3)

with m1:
    st.markdown("""
    <div class="or-card">
        <h4 style="color:#06B6D4; margin-top:0;">01 & 02. Data & Network</h4>
        <p style="font-size:0.88rem; color:#94A3B8;">
            <b>Overview & Dataset Explorer:</b> Audit 118 PDF/CAD signal plans, inspect geocoded nodes, approach lanes, and TOD phase schedules.<br><br>
            <b>Network Visualization:</b> Dual-level graph explorer for Macro corridors and Micro turning movements.
        </p>
    </div>
    """, unsafe_allow_html=True)

with m2:
    st.markdown("""
    <div class="or-card">
        <h4 style="color:#22C55E; margin-top:0;">03 & 04. Flow & Routing</h4>
        <p style="font-size:0.88rem; color:#94A3B8;">
            <b>Maximum Flow:</b> Cut capacity analysis and bottleneck edge detection using Dinic's algorithm.<br><br>
            <b>Minimum Cost Flow:</b> Balanced mass-conservation transshipment allocation with Network Simplex.
        </p>
    </div>
    """, unsafe_allow_html=True)

with m3:
    st.markdown("""
    <div class="or-card">
        <h4 style="color:#F59E0B; margin-top:0;">05, 06 & 07. Optimization & Sim</h4>
        <p style="font-size:0.88rem; color:#94A3B8;">
            <b>Shortest Path & Signal LP:</b> Dijkstra impedance comparison and exact HiGHS queue-minimizing green split LP.<br><br>
            <b>Simulation & Analytics:</b> Meso-queue dynamics, +10% to +30% demand sensitivity, and dual theorems.
        </p>
    </div>
    """, unsafe_allow_html=True)
