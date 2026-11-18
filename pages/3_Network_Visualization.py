"""
Page 3: Network Visualization.
Interactive dual-level graph explorer for Bengaluru:
- Level 1: Macro Arterial Directed Graph G = (V, E)
- Level 2: Micro Turning Movement Graph with Signal Phase Rights
- Topological Centrality & Critical Arterial Hubs
"""

import streamlit as st
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
from components.ui_helpers import (
    load_custom_css,
    render_header,
    get_plotly_layout,
    load_all_datasets,
    load_road_networks
)
from src.network.network_analyzer import NetworkAnalyzer

st.set_page_config(page_title="Network Visualization | Bengaluru Smart Traffic", page_icon="🗺️", layout="wide")
load_custom_css()

render_header(
    title="Road Network Topology & Turning Movements",
    subtitle="Level 1 Macro Directed Graph G=(V,E) and Level 2 Micro Turning Movement Structure",
    badge_text="Graph Theory & Topology"
)

data = load_all_datasets()
builder, G_macro, G_micro = load_road_networks()
df_nodes = data["intersections"]

tab_macro, tab_micro, tab_metrics = st.tabs([
    "🌐 Level 1: Macro Corridor Network",
    "🔀 Level 2: Micro Turning Movements",
    "📈 Topological Centrality & Hubs"
])

# TAB 1: MACRO NETWORK
with tab_macro:
    st.markdown("#### Bengaluru Metropolitan Directed Road Graph")
    col_f1, col_f2 = st.columns([1, 1])
    corridor_list = ["All Corridors"] + sorted(list(df_nodes["corridor"].dropna().unique()))
    sel_corr = col_f1.selectbox("Filter Display by Corridor:", corridor_list)
    color_by = col_f2.selectbox("Color Nodes By:", ["Corridor", "Cycle Length (s)", "Degree Centrality"])

    # Build node positions from lat/long
    node_x = []
    node_y = []
    node_text = []
    node_color = []
    
    # Subgraph filtering if corridor chosen
    if sel_corr != "All Corridors":
        sub_nodes = [n for n, d in G_macro.nodes(data=True) if d.get("corridor") == sel_corr]
        disp_graph = G_macro.subgraph(sub_nodes).copy()
    else:
        disp_graph = G_macro

    # Centrality calculation
    deg_cent = nx.degree_centrality(disp_graph)

    for node in disp_graph.nodes():
        d = disp_graph.nodes[node]
        lon = d.get("lon", 77.6)
        lat = d.get("lat", 12.9)
        name = d.get("name", node)
        cycle = d.get("cycle_time_sec", 120)
        corr = d.get("corridor", "General")
        
        node_x.append(lon)
        node_y.append(lat)
        node_text.append(f"<b>{name}</b><br>ID: {node}<br>Corridor: {corr}<br>Cycle: {cycle}s<br>Degree: {disp_graph.degree(node)}")
        
        if color_by == "Cycle Length (s)":
            node_color.append(cycle)
        elif color_by == "Degree Centrality":
            node_color.append(deg_cent.get(node, 0.0))
        else:
            # Map corridor to integer hash for categorical color
            node_color.append(hash(corr) % 100)

    # Build edge lines
    edge_x = []
    edge_y = []
    for u, v, d in disp_graph.edges(data=True):
        if u in disp_graph.nodes and v in disp_graph.nodes:
            x0 = disp_graph.nodes[u].get("lon", 77.6)
            y0 = disp_graph.nodes[u].get("lat", 12.9)
            x1 = disp_graph.nodes[v].get("lon", 77.6)
            y1 = disp_graph.nodes[v].get("lat", 12.9)
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

    fig_net = go.Figure()

    # Add edges
    fig_net.add_trace(go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1.5, color="rgba(6, 182, 212, 0.4)"),
        hoverinfo="none",
        mode="lines",
        name="Arterial Roads"
    ))

    # Add nodes
    fig_net.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode="markers",
        hoverinfo="text",
        text=node_text,
        marker=dict(
            showscale=True,
            colorscale="Viridis",
            color=node_color,
            size=10,
            line=dict(width=1.5, color="#0B1220"),
            colorbar=dict(
                title=color_by,
                thickness=14,
                tickfont=dict(color="#F1F5F9")
            )
        ),
        name="Intersections"
    ))

    layout = get_plotly_layout(f"Bengaluru Directed Macro Network ({disp_graph.number_of_nodes()} Nodes, {disp_graph.number_of_edges()} Edges)", height=650)
    layout["xaxis"]["title"] = "Longitude (°E)"
    layout["yaxis"]["title"] = "Latitude (°N)"
    fig_net.update_layout(layout)
    st.plotly_chart(fig_net, use_container_width=True)

# TAB 2: MICRO TURNING MOVEMENTS
with tab_micro:
    st.markdown("#### Level 2 Micro Turning Movement Structure")
    st.markdown("Inspect internal approach lanes, turning movement rights, and signal-controlled phase compatibility:")
    
    sel_int_micro = st.selectbox("Select Intersection for Micro Turning Diagram:", sorted(list(df_nodes["name"].unique())), key="sel_micro")
    
    # Schematic turning diagram
    fig_turn = go.Figure()
    
    # Compass approach positions
    approaches = {
        "Northbound Approach (South to North)": (0, -2, 0, -0.6, "#22C55E"),
        "Southbound Approach (North to South)": (0, 2, 0, 0.6, "#38BDF8"),
        "Eastbound Approach (West to East)": (-2, 0, -0.6, 0, "#F59E0B"),
        "Westbound Approach (East to West)": (2, 0, 0.6, 0, "#EF4444"),
    }
    
    # Center junction box
    fig_turn.add_shape(
        type="rect",
        x0=-0.6, y0=-0.6, x1=0.6, y1=0.6,
        line=dict(color="#06B6D4", width=2),
        fillcolor="rgba(23, 34, 53, 0.8)"
    )
    fig_turn.add_annotation(x=0, y=0, text=f"<b>{sel_int_micro}</b>", showarrow=False, font=dict(color="#F1F5F9", size=12))
    
    # Approach vectors
    for name, (x0, y0, x1, y1, color) in approaches.items():
        fig_turn.add_annotation(
            x=x1, y=y1, ax=x0, ay=y0,
            xref="x", yref="y", axref="x", ayref="y",
            showarrow=True, arrowhead=3, arrowsize=1.5, arrowwidth=3, arrowcolor=color
        )
        fig_turn.add_annotation(
            x=x0 * 1.25, y=y0 * 1.25,
            text=name.split("(")[0].strip(),
            showarrow=False,
            font=dict(color=color, size=11)
        )
        
    layout_micro = get_plotly_layout("Microscopic Approach & Movement Geometry", height=500)
    layout_micro["xaxis"]["range"] = [-3.5, 3.5]
    layout_micro["yaxis"]["range"] = [-3.5, 3.5]
    layout_micro["xaxis"]["showgrid"] = False
    layout_micro["yaxis"]["showgrid"] = False
    fig_turn.update_layout(layout_micro)
    st.plotly_chart(fig_turn, use_container_width=True)

# TAB 3: TOPOLOGICAL METRICS
with tab_metrics:
    st.markdown("#### Network Topology & Arterial Hub Analysis")
    analyzer = NetworkAnalyzer(G_macro)
    metrics = analyzer.compute_all_metrics()
    
    m_c1, m_c2, m_c3, m_c4 = st.columns(4)
    m_c1.metric("Network Density", f"{metrics.get('density', 0.0):.4f}")
    m_c2.metric("Average Clustering", f"{metrics.get('average_clustering', 0.0):.4f}")
    m_c3.metric("Strongly Connected Components", metrics.get("num_strongly_connected_components", 1))
    m_c4.metric("Weakly Connected Components", metrics.get("num_weakly_connected_components", 1))
    
    st.markdown("---")
    st.markdown("##### Top 10 Critical Arterial Hubs by Betweenness Centrality")
    st.caption("Intersections with highest betweenness centrality carry maximum routing influence and are vulnerable to network-wide bottleneck propagation.")
    
    betweenness = nx.betweenness_centrality(G_macro)
    top_hubs = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:10]
    
    hub_records = []
    for node, score in top_hubs:
        d = G_macro.nodes[node]
        hub_records.append({
            "Intersection ID": node,
            "Intersection Name": d.get("name", node),
            "Corridor": d.get("corridor", "N/A"),
            "Betweenness Centrality": round(score, 5),
            "Degree": G_macro.degree(node),
            "Cycle Length (s)": d.get("cycle_time_sec", 120)
        })
    st.dataframe(pd.DataFrame(hub_records), use_container_width=True)
