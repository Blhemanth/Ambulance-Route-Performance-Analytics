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

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
STYLE_PATH = os.path.join(PROJECT_ROOT, "assets", "style.css")

def load_custom_css():
    """Injects custom CSS for dark theme, typography, and micro-animations."""
    if os.path.exists(STYLE_PATH):
        with open(STYLE_PATH, "r", encoding="utf-8") as f:
            css = f.read()
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        .stApp { background-color: #F8FAFC; color: #0F172A; }
        </style>
        """, unsafe_allow_html=True)

def render_sidebar_navigation(current_page: str = ""):
    """Renders a custom, categorized sidebar navigation replacing raw default page links."""
    # Register Streamlit top-left application logo
    logo_banner_path = os.path.join(PROJECT_ROOT, "assets", "logo_banner.png")
    logo_icon_path = os.path.join(PROJECT_ROOT, "assets", "logo_icon.png")
    if hasattr(st, "logo") and os.path.exists(logo_banner_path):
        st.logo(logo_banner_path, icon_image=logo_icon_path if os.path.exists(logo_icon_path) else None)

    with st.sidebar:
        st.markdown("""
        <div class="sidebar-header">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                <div style="
                    width: 38px; 
                    height: 38px; 
                    border-radius: 9px; 
                    background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%); 
                    display: flex; 
                    align-items: center; 
                    justify-content: center; 
                    box-shadow: 0 2px 6px rgba(2, 132, 199, 0.25);
                    flex-shrink: 0;
                ">
                    <span style="font-size: 20px; line-height: 1;">🚑</span>
                </div>
                <div>
                    <div class="sidebar-title" style="font-size: 0.90rem; font-weight: 800; color: #0F172A; line-height: 1.15; letter-spacing: -0.01em;">
                        AMBULANCE ROUTE<br/><span style="color: #0284C7;">OPTIMIZATION</span>
                    </div>
                </div>
            </div>
            <div class="sidebar-sub" style="font-size: 0.67rem; color: #64748B; font-weight: 600; letter-spacing: 0.04em; margin-top: 4px;">
                Bengaluru Emergency Medical GIS · OR Platform
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="nav-section-title">Ambulance Routing System</div>', unsafe_allow_html=True)
        st.page_link("app.py", label="Operations Dashboard", icon="🏛️", width="stretch")
        st.page_link("pages/1_Road_Network_Explorer.py", label="01. Road Network Explorer", icon="🗺️", width="stretch")
        st.page_link("pages/2_Hospital_Finder.py", label="02. Hospital Finder & Snapping", icon="🏥", width="stretch")
        st.page_link("pages/3_Ambulance_Route_Optimizer.py", label="03. Ambulance Route Optimizer", icon="🚑", width="stretch")
        st.page_link("pages/4_Alternative_Route_Comparison.py", label="04. Alternative Route Comparison", icon="🔀", width="stretch")
        st.page_link("pages/5_Signal_Delay_Analysis.py", label="05. Traffic Signal Delay Analysis", icon="🚦", width="stretch")
        st.page_link("pages/6_Traffic_Scenario_Analysis.py", label="06. Traffic Scenario Analysis", icon="📊", width="stretch")
        st.page_link("pages/7_Route_Performance_Analytics.py", label="07. Route Performance Analytics", icon="📈", width="stretch")
        st.page_link("pages/8_OR_Methodology.py", label="08. OR Methodology & Formulations", icon="📜", width="stretch")
        
        st.markdown("---")
        st.markdown("""
        <div style="padding: 0.65rem 0.75rem; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px;">
            <div style="font-size: 0.68rem; color: #64748B; font-weight: 700; letter-spacing: 0.05em; margin-bottom: 0.35rem;">ACTIVE OR SOLVERS</div>
            <div style="font-size: 0.72rem; color: #16A34A; margin-bottom: 0.2rem; font-weight: 600;">● Signal-Aware Dijkstra</div>
            <div style="font-size: 0.72rem; color: #7C3AED; margin-bottom: 0.2rem; font-weight: 600;">● BPR Congestion Scenarios</div>
            <div style="font-size: 0.72rem; color: #0284C7; margin-bottom: 0.2rem; font-weight: 600;">● Baseline Minimum Time (IRC:106)</div>
            <div style="font-size: 0.72rem; color: #2563EB; margin-bottom: 0.2rem; font-weight: 600;">● Yen's K-Shortest Loopless Paths</div>
            <div style="font-size: 0.72rem; color: #D97706; margin-bottom: 0.35rem; font-weight: 600;">● Webster Fixed-Time Delay</div>
            <div style="font-size: 0.68rem; color: #64748B; border-top: 1px solid #E2E8F0; padding-top: 0.3rem;">
                226 Intersections · 1,164 Directed Edges
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
                <span>AMBULANCE ROUTE OPTIMIZATION // OPERATIONS RESEARCH LAB</span>
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
            st.page_link(prev_page, label=f"← {prev_label}", width="stretch")
    if next_page and next_label:
        with c_next:
            st.page_link(next_page, label=f"{next_label} →", width="stretch")

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
    """Returns light-themed Plotly layout configuration for medical/clinical dashboards."""
    return dict(
        title=dict(text=title, font=dict(color="#0F172A", size=15, family="Plus Jakarta Sans, sans-serif")),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#F8FAFC",
        font=dict(color="#334155", family="Plus Jakarta Sans, sans-serif"),
        height=height,
        margin=dict(l=40, r=40, t=50, b=40),
        xaxis=dict(
            gridcolor="#E2E8F0",
            linecolor="#CBD5E1",
            tickfont=dict(color="#64748B"),
            title=dict(font=dict(color="#0F172A"))
        ),
        yaxis=dict(
            gridcolor="#E2E8F0",
            linecolor="#CBD5E1",
            tickfont=dict(color="#64748B"),
            title=dict(font=dict(color="#0F172A"))
        ),
        legend=dict(
            bgcolor="#FFFFFF",
            bordercolor="#E2E8F0",
            font=dict(color="#0F172A")
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

@st.cache_resource
def load_gis_network():
    """Initializes and returns the GIS Network Manager and enriched roads catalog."""
    from src.network.gis_network import GISNetworkManager
    gis_mgr = GISNetworkManager()
    builder, G_macro, G_micro = load_road_networks()
    roads_gis = gis_mgr.build_roads_gis_catalog(G_macro)
    df_intersections_gis = gis_mgr.get_intersections_gis()
    if "corridor" not in df_intersections_gis.columns:
        from src.network.graph_builder import map_police_station_to_corridor
        df_intersections_gis["corridor"] = df_intersections_gis.apply(
            lambda r: map_police_station_to_corridor(r.get("police_station", ""), r.get("name", "")),
            axis=1
        )
    return gis_mgr, roads_gis, df_intersections_gis

@st.cache_resource
def load_ambulance_router():
    """
    Cached singleton loader for the Phase 2 AmbulanceRouter and road graphs.
    Caches graph construction and hospital catalogs across Streamlit interactions.
    """
    from src.network.ambulance_graph import get_ambulance_road_graphs
    from src.network.ambulance_router import AmbulanceRouter
    g_multi, g_di = get_ambulance_road_graphs()
    router = AmbulanceRouter(
        graph_multi=g_multi,
        graph_di=g_di,
        hospitals_csv_path=os.path.join(DATA_DIR, "bengaluru_hospitals.csv"),
        connections_csv_path=os.path.join(DATA_DIR, "hospital_road_connections.csv")
    )
    if not hasattr(router, "find_hospital_route") and hasattr(router, "route_to_hospital"):
        router.find_hospital_route = router.route_to_hospital
    return router

@st.cache_data
def load_hospital_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Loads and caches static hospital inventory and snapping connections."""
    h_path = os.path.join(DATA_DIR, "bengaluru_hospitals.csv")
    c_path = os.path.join(DATA_DIR, "hospital_road_connections.csv")
    df_hospitals = pd.read_csv(h_path) if os.path.exists(h_path) else pd.DataFrame()
    df_connections = pd.read_csv(c_path) if os.path.exists(c_path) else pd.DataFrame()
    return df_hospitals, df_connections

@st.cache_data
def load_congestion_scenario_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Loads and caches traffic data inventory and congestion scenarios."""
    inv_path = os.path.join(DATA_DIR, "bengaluru_traffic_data_inventory.csv")
    scen_path = os.path.join(DATA_DIR, "network_congestion_scenarios.csv")
    df_inv = pd.read_csv(inv_path) if os.path.exists(inv_path) else pd.DataFrame()
    df_scen = pd.read_csv(scen_path) if os.path.exists(scen_path) else pd.DataFrame()
    return df_inv, df_scen



