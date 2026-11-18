"""
UI Helper functions and design components for the Bengaluru Smart Traffic Optimizer.
Provides dark theme injection, custom sidebar navigation, workflow page switching,
cached dataset loaders, custom KPI metric cards, and Plotly dark theme layout presets.
"""

import os
import pandas as pd
import streamlit as st
import networkx as nx
from typing import Dict, Any, Tuple, Optional
from src.network.graph_builder import GraphBuilder, map_police_station_to_corridor

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "processed")
STYLE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "style.css")

def load_custom_css():
    """Injects custom CSS for dark theme, typography, and micro-animations."""
    if os.path.exists(STYLE_PATH):
        with open(STYLE_PATH, "r", encoding="utf-8") as f:
            css = f.read()
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        .stApp { background-color: #080C14; color: #F8FAFC; }
        </style>
        """, unsafe_allow_html=True)

def render_sidebar_navigation(current_page: str = ""):
    """Renders a custom, categorized sidebar navigation replacing raw default page links."""
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-header">
            <div class="sidebar-title">
                <span class="live-dot"></span> BENGALURU SMART TRAFFIC
            </div>
            <div class="sidebar-sub">Operations Research Platform</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="nav-section-title">System Architecture</div>', unsafe_allow_html=True)
        st.page_link("app.py", label="Executive Portal", icon="🏛️", use_container_width=True)
        st.page_link("pages/1_Overview.py", label="01. Corpus Architecture", icon="📊", use_container_width=True)
        st.page_link("pages/2_Dataset_Explorer.py", label="02. Signal Plan Explorer", icon="📑", use_container_width=True)
        st.page_link("pages/3_Network_Visualization.py", label="03. Network Topology Map", icon="🗺️", use_container_width=True)
        
        st.markdown('<div class="nav-section-title">Core Network Models</div>', unsafe_allow_html=True)
        st.page_link("pages/4_Maximum_Flow.py", label="04. Model 1: Maximum Flow", icon="⚡", use_container_width=True)
        st.page_link("pages/5_Minimum_Cost_Flow.py", label="05. Model 2: Min Cost Flow", icon="⚖️", use_container_width=True)
        st.page_link("pages/6_Shortest_Path.py", label="06. Model 3: Shortest Path", icon="🛣️", use_container_width=True)
        st.page_link("pages/7_Signal_Optimization.py", label="07. Model 4: Signal Timing LP", icon="🚦", use_container_width=True)
        
        st.markdown('<div class="nav-section-title">Evaluation & Proofs</div>', unsafe_allow_html=True)
        st.page_link("pages/8_Simulation_Centre.py", label="08. Dynamic Simulation", icon="⏱️", use_container_width=True)
        st.page_link("pages/9_Analytics.py", label="09. Scenario Stress Testing", icon="📈", use_container_width=True)
        st.page_link("pages/10_Methodology.py", label="10. Formulations & Proofs", icon="📜", use_container_width=True)
        
        st.markdown("---")
        st.markdown("""
        <div style="padding: 0.6rem 0.75rem; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px;">
            <div style="font-size: 0.68rem; color: #94A3B8; font-weight: 700; letter-spacing: 0.05em; margin-bottom: 0.3rem;">ACTIVE SOLVERS</div>
            <div style="font-size: 0.72rem; color: #34D399; margin-bottom: 0.15rem;">● SciPy HiGHS Simplex / IPM</div>
            <div style="font-size: 0.72rem; color: #38BDF8; margin-bottom: 0.15rem;">● Network Simplex (Cost Flow)</div>
            <div style="font-size: 0.72rem; color: #818CF8; margin-bottom: 0.35rem;">● Dinic / Dijkstra (Max Flow & SP)</div>
            <div style="font-size: 0.68rem; color: #64748B; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 0.3rem;">
                226 Intersections · 1,142 Directed Edges
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_header(title: str, subtitle: str, badge_text: str = "Operations Research Framework", current_page: str = ""):
    """Renders a uniform, academically branded header banner and renders the sidebar navigation."""
    render_sidebar_navigation(current_page)
    st.markdown(f"""
    <div class="header-banner">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem; flex-wrap: wrap; gap: 0.5rem;">
            <div class="header-pretitle">
                <span class="live-dot"></span>
                <span>BENGALURU METROPOLITAN TRAFFIC MANAGEMENT // OPERATIONS RESEARCH LAB</span>
            </div>
            <span class="provenance-badge badge-external">{badge_text}</span>
        </div>
        <h1 class="header-title">{title}</h1>
        <div class="header-subtitle">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

def render_workflow_navigation(
    prev_page: Optional[str] = None,
    prev_label: Optional[str] = None,
    next_page: Optional[str] = None,
    next_label: Optional[str] = None
):
    """Renders a sleek bottom bar for seamless sequential page switching between models."""
    st.markdown("---")
    c_prev, c_spacer, c_next = st.columns([1.2, 0.6, 1.2])
    if prev_page and prev_label:
        with c_prev:
            st.page_link(prev_page, label=f"← {prev_label}", use_container_width=True)
    if next_page and next_label:
        with c_next:
            st.page_link(next_page, label=f"{next_label} →", use_container_width=True)

def render_metric(col, title: str, value: Any, subtitle: str = "", status: str = "normal"):
    """Renders a styled modern KPI metric box with top accent bar."""
    color_class = ""
    if status == "green":
        color_class = "green"
    elif status == "red":
        color_class = "red"
    elif status == "amber":
        color_class = "amber"

    html = f"""
    <div class="metric-box {color_class}">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-subtitle">{subtitle}</div>
    </div>
    """
    col.markdown(html, unsafe_allow_html=True)

def get_provenance_badge(provenance: str) -> str:
    """Returns HTML badge for provenance."""
    p_up = str(provenance).upper()
    cls_map = {
        "ACTUAL": "badge-actual",
        "EXTERNAL": "badge-external",
        "MEASURED": "badge-measured",
        "ESTIMATED": "badge-estimated",
        "SYNTHETIC": "badge-synthetic"
    }
    css_class = cls_map.get(p_up, "badge-estimated")
    return f'<span class="provenance-badge {css_class}">{p_up}</span>'

def get_plotly_layout(title: str = "", height: int = 500) -> Dict[str, Any]:
    """Returns dark-themed Plotly layout configuration."""
    return dict(
        title=dict(text=title, font=dict(color="#F8FAFC", size=15, family="Plus Jakarta Sans, sans-serif")),
        paper_bgcolor="rgba(15, 23, 42, 0.4)",
        plot_bgcolor="rgba(8, 12, 20, 0.6)",
        font=dict(color="#94A3B8", family="Plus Jakarta Sans, sans-serif"),
        height=height,
        margin=dict(l=40, r=40, t=50, b=40),
        xaxis=dict(
            gridcolor="rgba(255, 255, 255, 0.06)",
            linecolor="rgba(255, 255, 255, 0.1)",
            tickfont=dict(color="#94A3B8"),
            title=dict(font=dict(color="#F8FAFC"))
        ),
        yaxis=dict(
            gridcolor="rgba(255, 255, 255, 0.06)",
            linecolor="rgba(255, 255, 255, 0.1)",
            tickfont=dict(color="#94A3B8"),
            title=dict(font=dict(color="#F8FAFC"))
        ),
        legend=dict(
            bgcolor="rgba(15, 23, 42, 0.8)",
            bordercolor="rgba(255, 255, 255, 0.08)",
            font=dict(color="#F8FAFC")
        )
    )

@st.cache_data
def load_all_datasets() -> Dict[str, pd.DataFrame]:
    """Loads all processed traffic datasets from CSV with enriched columns."""
    df_intersections = pd.read_csv(os.path.join(DATA_DIR, "intersections.csv"))
    df_roads = pd.read_csv(os.path.join(DATA_DIR, "roads.csv"))
    df_phases = pd.read_csv(os.path.join(DATA_DIR, "signal_phases.csv"))
    df_timings = pd.read_csv(os.path.join(DATA_DIR, "signal_timings.csv"))
    
    # Safe error log reader
    err_path = os.path.join(DATA_DIR, "extraction_errors.csv")
    df_errors = pd.DataFrame(columns=["file_name", "error_type", "message", "page_number"])
    if os.path.exists(err_path) and os.path.getsize(err_path) > 10:
        try:
            df_errors = pd.read_csv(err_path)
        except Exception:
            pass

    # Enrich df_intersections with corridor, cycle_time_sec, num_phases
    if "corridor" not in df_intersections.columns:
        df_intersections["corridor"] = df_intersections.apply(
            lambda r: map_police_station_to_corridor(r.get("police_station", ""), r.get("name", "")),
            axis=1
        )
    if "cycle_time_sec" not in df_intersections.columns:
        c_map = df_timings.groupby("intersection_id")["cycle_length_sec"].mean().to_dict()
        df_intersections["cycle_time_sec"] = df_intersections["intersection_id"].map(c_map).fillna(120).astype(int)
    if "num_phases" not in df_intersections.columns:
        p_map = df_phases.groupby("intersection_id")["phase_number"].nunique().to_dict()
        df_intersections["num_phases"] = df_intersections["intersection_id"].map(p_map).fillna(3).astype(int)

    # Enrich df_roads with compatible column aliases
    if "from_intersection_id" not in df_roads.columns:
        df_roads["from_intersection_id"] = df_roads["intersection_id"]
    if "to_intersection_id" not in df_roads.columns:
        df_roads["to_intersection_id"] = df_roads["intersection_id"]
    if "base_capacity_pcu_hr" not in df_roads.columns and "capacity_pcu_hr" in df_roads.columns:
        df_roads["base_capacity_pcu_hr"] = df_roads["capacity_pcu_hr"]
    if "effective_capacity_pcu_hr" not in df_roads.columns and "capacity_pcu_hr" in df_roads.columns:
        df_roads["effective_capacity_pcu_hr"] = (df_roads["capacity_pcu_hr"] * 0.45).round(0)

    # Enrich df_phases with compatible column aliases
    if "approach_direction" not in df_phases.columns and "approach_code" in df_phases.columns:
        df_phases["approach_direction"] = df_phases["approach_code"]
    if "movement_type" not in df_phases.columns and "permitted_movements" in df_phases.columns:
        df_phases["movement_type"] = df_phases["permitted_movements"]
    if "lanes_served" not in df_phases.columns:
        df_phases["lanes_served"] = 2

    # Enrich df_timings with compatible column aliases
    if "green_duration_sec" not in df_timings.columns and "green_time_sec" in df_timings.columns:
        df_timings["green_duration_sec"] = df_timings["green_time_sec"]
    if "amber_sec" not in df_timings.columns and "yellow_time_sec" in df_timings.columns:
        df_timings["amber_sec"] = df_timings["yellow_time_sec"]
    if "red_sec" not in df_timings.columns and "all_red_sec" in df_timings.columns:
        df_timings["red_sec"] = df_timings["all_red_sec"]

    return {
        "intersections": df_intersections,
        "roads": df_roads,
        "phases": df_phases,
        "timings": df_timings,
        "errors": df_errors
    }

@st.cache_resource
def load_road_networks():
    """Initializes and returns Level 1 and Level 2 directed networks."""
    builder = GraphBuilder()
    G_macro, G_micro = builder.build_complete_bengaluru_network()
    return builder, G_macro, G_micro
