"""
Reusable GIS Map Component for Bengaluru Ambulance Route Optimization.
Built with Folium, Leaflet, and Streamlit-Folium.
Provides multi-layer geographic visualization, real street geometry polylines,
interactive junction/road inspection popups, and layer controls.
"""

import os
import math
import warnings
from typing import Dict, List, Any, Tuple, Optional
import streamlit as st
import pandas as pd

# Suppress upstream Folium / xyzservices CartoDB API key warnings
warnings.filterwarnings("ignore", message=".*CartoDB.*", category=UserWarning)
warnings.filterwarnings("ignore", message=".*api_key.*", category=UserWarning)

try:
    import folium
    from folium import plugins
    HAS_FOLIUM = True
except ImportError:
    folium = None
    plugins = None
    HAS_FOLIUM = False

try:
    from streamlit_folium import st_folium
    HAS_STREAMLIT_FOLIUM = True
except ImportError:
    st_folium = None
    HAS_STREAMLIT_FOLIUM = False

BENGALURU_LAT = 12.9716
BENGALURU_LON = 77.5946

def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two lat/lon coordinates in meters."""
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def get_status_color(status: str) -> str:
    """Returns CSS hex color for coordinate/geometry verification status."""
    st_up = str(status).upper()
    if st_up in ["VERIFIED", "ACTUAL"]:
        return "#10B981"  # Emerald green
    elif st_up in ["NEEDS_VERIFICATION", "ESTIMATED", "EXTERNAL"]:
        return "#F59E0B"  # Amber
    else:
        return "#EF4444"  # Crimson red

def build_intersection_popup(node_data: Dict[str, Any]) -> str:
    """Builds a rich HTML popup card for an intersection marker."""
    name = node_data.get("name", node_data.get("intersection_name", "Intersection"))
    nid = node_data.get("intersection_id", "N/A")
    verif = node_data.get("verification_status", "NEEDS_VERIFICATION")
    v_color = get_status_color(verif)
    
    ps = node_data.get("police_station", "Bengaluru Police")
    ctrl = node_data.get("control_type", "Fixed Time")
    cycle = node_data.get("cycle_time_sec", node_data.get("cycle_time", 120))
    approaches = node_data.get("num_approaches", "Multiple")
    pdf = node_data.get("source_pdf", "BEL_Engineering_Plan.pdf")
    page = node_data.get("source_page", node_data.get("page_number", 1))
    lat = node_data.get("latitude", node_data.get("lat", 0.0))
    lon = node_data.get("longitude", node_data.get("lon", 0.0))
    
    html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 12px; width: 280px; color: #0F172A; padding: 4px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; border-bottom: 2px solid #0284C7; padding-bottom: 4px;">
            <b style="font-size: 13px; color: #0369A1;">📍 {name}</b>
        </div>
        <div style="margin-bottom: 6px;">
            <span style="background: {v_color}; color: #FFFFFF; font-size: 9px; font-weight: 700; padding: 2px 6px; border-radius: 4px; text-transform: uppercase;">
                {verif}
            </span>
            <span style="font-size: 10px; color: #64748B; margin-left: 6px;">ID: <code>{nid}</code></span>
        </div>
        <table style="width: 100%; border-collapse: collapse; font-size: 11px; margin-bottom: 6px;">
            <tr><td style="color:#64748B; padding:2px 0;">Coordinates:</td><td><b>{lat:.4f}°N, {lon:.4f}°E</b></td></tr>
            <tr><td style="color:#64748B; padding:2px 0;">Jurisdiction:</td><td><b>{ps}</b></td></tr>
            <tr><td style="color:#64748B; padding:2px 0;">Control Type:</td><td><b>{ctrl}</b></td></tr>
            <tr><td style="color:#64748B; padding:2px 0;">Cycle Length:</td><td><b>{cycle} seconds</b></td></tr>
            <tr><td style="color:#64748B; padding:2px 0;">Approaches:</td><td><b>{approaches} legs</b></td></tr>
        </table>
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 4px; padding: 4px 6px; font-size: 10px; color: #475569;">
            <b>Data Provenance:</b> BEL Drawing <code>{pdf}</code> (p. {page})
        </div>
    </div>
    """
    return html

def build_road_popup(edge_data: Dict[str, Any]) -> str:
    """Builds a rich HTML popup card for a road segment polyline."""
    rname = edge_data.get("road_name", "Arterial Road Segment")
    eid = edge_data.get("edge_id", "EDGE_LINK")
    u_name = edge_data.get("from_name", edge_data.get("from_node", "Start"))
    v_name = edge_data.get("to_name", edge_data.get("to_node", "End"))
    direction = edge_data.get("direction", "FORWARD")
    length = edge_data.get("length_m", 500.0)
    lanes = edge_data.get("lanes", 2)
    cap = edge_data.get("capacity", edge_data.get("base_capacity", 2400))
    flow = edge_data.get("traffic_flow", edge_data.get("flow", 0.0))
    cost = edge_data.get("cost", 1.0)
    delay = edge_data.get("signal_delay_min", 0.5)
    
    # Saturation / Bottleneck state
    util = (flow / cap * 100.0) if cap > 0 else 0.0
    is_bn = edge_data.get("is_bottleneck", False) or util >= 99.0
    bn_badge = '<span style="background: #EF4444; color: white; padding: 1px 4px; border-radius: 3px; font-size: 9px; font-weight: bold;">SATURATED CUT</span>' if is_bn else '<span style="background: #10B981; color: white; padding: 1px 4px; border-radius: 3px; font-size: 9px;">NORMAL</span>'
    
    geom_src = edge_data.get("geometry_source", "OSM_WAY_CENTERLINE")
    verif = edge_data.get("verification_status", "VERIFIED")
    v_color = get_status_color(verif)
    
    html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 12px; width: 280px; color: #0F172A; padding: 4px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; border-bottom: 2px solid #0D9488; padding-bottom: 4px;">
            <b style="font-size: 13px; color: #0F766E;">🛣️ {rname}</b>
        </div>
        <div style="margin-bottom: 6px;">
            <span style="background: {v_color}; color: white; font-size: 9px; font-weight: 700; padding: 2px 6px; border-radius: 4px;">
                {verif}
            </span>
            <span style="margin-left: 6px;">{bn_badge}</span>
        </div>
        <div style="font-size: 10px; color: #64748B; margin-bottom: 6px;">
            <b>Trajectory:</b> {u_name} &rarr; {v_name}
        </div>
        <table style="width: 100%; border-collapse: collapse; font-size: 11px; margin-bottom: 6px;">
            <tr><td style="color:#64748B; padding:2px 0;">Direction:</td><td><b>{direction}</b></td></tr>
            <tr><td style="color:#64748B; padding:2px 0;">Road Length:</td><td><b>{length:,.1f} meters</b></td></tr>
            <tr><td style="color:#64748B; padding:2px 0;">Approach Lanes:</td><td><b>{lanes} lanes</b></td></tr>
            <tr><td style="color:#64748B; padding:2px 0;">Link Capacity:</td><td><b>{cap:,.0f} PCU/hr</b></td></tr>
            <tr><td style="color:#64748B; padding:2px 0;">Traffic Flow:</td><td><b>{flow:,.1f} PCU/hr</b></td></tr>
            <tr><td style="color:#64748B; padding:2px 0;">Utilization (v/c):</td><td><b>{util:.1f}%</b></td></tr>
            <tr><td style="color:#64748B; padding:2px 0;">Travel Time/Delay:</td><td><b>{cost:.2f} min ({delay:.2f}m delay)</b></td></tr>
        </table>
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 4px; padding: 4px 6px; font-size: 10px; color: #475569;">
            <b>Geometry Source:</b> <code>{geom_src}</code>
        </div>
    </div>
    """
    return html

def build_map_legend_html() -> str:
    """Builds a clean, light floating HTML legend explaining map markers, line widths, and layers."""
    return """
    <div style="
        position: fixed; 
        bottom: 24px; 
        left: 24px; 
        z-index: 9999; 
        background: rgba(255, 255, 255, 0.96); 
        border: 1px solid #E2E8F0; 
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.08);
        padding: 10px 14px; 
        border-radius: 8px; 
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 11px; 
        color: #0F172A;
        max-width: 260px;
        backdrop-filter: blur(4px);
    ">
        <div style="font-weight: 700; color: #0284C7; margin-bottom: 6px; font-size: 12px; letter-spacing: 0.04em;">
            🗺️ BENGALURU GIS MAP LEGEND
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 4px;">
            <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #16A34A; border: 1px solid #FFFFFF; margin-right: 8px;"></span>
            <span>Verified Junction (OSM Crossroad)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 4px;">
            <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #F59E0B; border: 1px solid #FFFFFF; margin-right: 8px;"></span>
            <span>Estimated Geocode (Needs Verif)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 6px;">
            <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #DC2626; border: 1px solid #FFFFFF; margin-right: 8px;"></span>
            <span>Unverified / Landmark Approx</span>
        </div>
        <div style="border-top: 1px solid #E2E8F0; padding-top: 5px; margin-top: 5px;">
            <div style="display: flex; align-items: center; margin-bottom: 3px;">
                <span style="display: inline-block; width: 18px; height: 3px; background: #0284C7; margin-right: 8px;"></span>
                <span>Arterial Road Network</span>
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 3px;">
                <span style="display: inline-block; width: 18px; height: 4px; background: #DC2626; margin-right: 8px;"></span>
                <span>Saturated Bottleneck Link</span>
            </div>
            <div style="display: flex; align-items: center;">
                <span style="display: inline-block; width: 18px; height: 4px; background: #16A34A; margin-right: 8px;"></span>
                <span>Dijkstra Optimal Route</span>
            </div>
        </div>
    </div>
    """

def create_bengaluru_gis_map(
    center_lat: float = BENGALURU_LAT,
    center_lon: float = BENGALURU_LON,
    zoom_start: int = 12,
    intersections: Optional[List[Dict[str, Any]]] = None,
    roads: Optional[List[Dict[str, Any]]] = None,
    source_node: Optional[str] = None,
    sink_node: Optional[str] = None,
    highlight_path_nodes: Optional[List[str]] = None,
    baseline_path_nodes: Optional[List[str]] = None,
    optimized_path_nodes: Optional[List[str]] = None,
    flow_dict: Optional[Dict[str, Dict[str, float]]] = None,
    bottleneck_edges: Optional[List[Tuple[str, str]]] = None,
    show_legend: bool = True
) -> Optional[Any]:
    """
    Creates a full-featured Folium GIS map of Bengaluru.
    """
    if not HAS_FOLIUM:
        return None

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom_start,
        tiles=None,
        control_scale=True
    )

    # Base Tile Layers
    folium.TileLayer(
        tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        name="OpenStreetMap (Default)",
        overlay=False,
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
        attr='&copy; <a href="https://carto.com/">CARTO</a>',
        name="CartoDB Voyager (Street Detail)",
        overlay=False,
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        attr='&copy; <a href="https://carto.com/">CARTO</a>',
        name="CartoDB Positron (Light Canvas)",
        overlay=False,
        control=True
    ).add_to(m)

    # Feature Groups for Interactive Layer Toggling
    fg_roads = folium.FeatureGroup(name="🛣️ Arterial Roads (OSM Geometry)", show=True)
    fg_nodes = folium.FeatureGroup(name="📍 Signalized Intersections (BEL CAD)", show=True)
    fg_bottlenecks = folium.FeatureGroup(name="🔴 Saturated Cut Bottlenecks (Max Flow)", show=True)
    fg_flow = folium.FeatureGroup(name="⚡ Network Traffic Flow (Solver)", show=bool(flow_dict))
    fg_path = folium.FeatureGroup(name="🛣️ Shortest Path Route (Dijkstra)", show=bool(highlight_path_nodes))
    fg_base_route = folium.FeatureGroup(name="🛣️ Baseline Route (BEL Delays)", show=bool(baseline_path_nodes))
    fg_opt_route = folium.FeatureGroup(name="🛣️ Signal-Optimized Route (HiGHS LP)", show=bool(optimized_path_nodes))

    # Add Roads Layer
    if roads:
        for r in roads:
            geom = r.get("geometry", [])
            if not geom or len(geom) < 2:
                continue

            u = r.get("from_node", "")
            v = r.get("to_node", "")
            
            # Check flow
            fl = 0.0
            if flow_dict and u in flow_dict and v in flow_dict[u]:
                fl = flow_dict[u][v]
                r["traffic_flow"] = fl

            # Check bottleneck
            is_bn = False
            if bottleneck_edges and ((u, v) in bottleneck_edges or (v, u) in bottleneck_edges):
                is_bn = True
                r["is_bottleneck"] = True

            popup_html = build_road_popup(r)
            popup = folium.Popup(popup_html, max_width=320)

            # Determine polyline styling
            if is_bn:
                # Add to bottleneck layer
                folium.PolyLine(
                    locations=geom,
                    color="#EF4444",
                    weight=5.5,
                    opacity=0.95,
                    popup=popup,
                    tooltip=f"🚨 Bottleneck Cut: {r.get('road_name', 'Link')}"
                ).add_to(fg_bottlenecks)
            elif fl > 0:
                # Add to flow layer with proportional width
                w = min(8.0, max(2.5, (fl / 800.0) * 2.5))
                # Congestion color-coding: green (v/c <= 0.70), amber (0.70 < v/c <= 0.85), red (v/c > 0.85)
                cap_val = r.get("capacity", 2400)
                vc_ratio = (fl / cap_val) if cap_val > 0 else 0.0
                f_color = "#22C55E" if vc_ratio <= 0.70 else ("#F59E0B" if vc_ratio <= 0.85 else "#EF4444")
                folium.PolyLine(
                    locations=geom,
                    color=f_color,
                    weight=w,
                    opacity=0.88,
                    popup=popup,
                    tooltip=f"Flow: {fl:,.0f} PCU/hr (v/c: {vc_ratio*100:.1f}%) on {r.get('road_name', 'Link')}"
                ).add_to(fg_flow)
            else:
                # Default arterial line
                folium.PolyLine(
                    locations=geom,
                    color="#38BDF8",
                    weight=2.0,
                    opacity=0.6,
                    popup=popup,
                    tooltip=r.get("road_name", "Arterial Link")
                ).add_to(fg_roads)

    # Add Single Shortest Path Layer if provided
    if highlight_path_nodes and roads:
        path_pairs = set(zip(highlight_path_nodes[:-1], highlight_path_nodes[1:]))
        for r in roads:
            u = r.get("from_node", "")
            v = r.get("to_node", "")
            if (u, v) in path_pairs:
                geom = r.get("geometry", [])
                if geom and len(geom) >= 2:
                    folium.PolyLine(
                        locations=geom,
                        color="#10B981",
                        weight=6.0,
                        opacity=0.95,
                        tooltip=f"Optimal Path: {r.get('road_name', 'Road')}"
                    ).add_to(fg_path)

    # Add Dual Baseline vs Optimized Routes Comparison Layers
    if baseline_path_nodes and roads:
        base_pairs = set(zip(baseline_path_nodes[:-1], baseline_path_nodes[1:]))
        for r in roads:
            u = r.get("from_node", "")
            v = r.get("to_node", "")
            if (u, v) in base_pairs:
                geom = r.get("geometry", [])
                if geom and len(geom) >= 2:
                    folium.PolyLine(
                        locations=geom,
                        color="#F59E0B",
                        weight=5.0,
                        opacity=0.9,
                        tooltip=f"Baseline Segment: {r.get('road_name', 'Road')}"
                    ).add_to(fg_base_route)

    if optimized_path_nodes and roads:
        opt_pairs = set(zip(optimized_path_nodes[:-1], optimized_path_nodes[1:]))
        for r in roads:
            u = r.get("from_node", "")
            v = r.get("to_node", "")
            if (u, v) in opt_pairs:
                geom = r.get("geometry", [])
                if geom and len(geom) >= 2:
                    folium.PolyLine(
                        locations=geom,
                        color="#10B981",
                        weight=6.5,
                        opacity=0.95,
                        tooltip=f"Signal-Optimized Segment: {r.get('road_name', 'Road')}"
                    ).add_to(fg_opt_route)

    # Add Intersections Layer
    if intersections:
        for node in intersections:
            lat = float(node.get("latitude", node.get("lat", BENGALURU_LAT)))
            lon = float(node.get("longitude", node.get("lon", BENGALURU_LON)))
            nid = node.get("intersection_id", "")
            v_status = node.get("verification_status", "NEEDS_VERIFICATION")
            color = get_status_color(v_status)

            popup_html = build_intersection_popup(node)
            popup = folium.Popup(popup_html, max_width=300)

            # Highlight Source / Sink pins
            if source_node and nid == source_node:
                folium.Marker(
                    location=[lat, lon],
                    popup=popup,
                    tooltip=f"🟢 Origin / Source (s): {node.get('name', nid)}",
                    icon=folium.Icon(color="green", icon="play", prefix="fa")
                ).add_to(fg_nodes)
            elif sink_node and nid == sink_node:
                folium.Marker(
                    location=[lat, lon],
                    popup=popup,
                    tooltip=f"🔴 Destination / Sink (t): {node.get('name', nid)}",
                    icon=folium.Icon(color="red", icon="stop", prefix="fa")
                ).add_to(fg_nodes)
            else:
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=5.5,
                    color="#0B1220",
                    weight=1.2,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.9,
                    popup=popup,
                    tooltip=f"{node.get('name', nid)} ({v_status})"
                ).add_to(fg_nodes)

    # Add Feature Groups to Map
    fg_roads.add_to(m)
    fg_nodes.add_to(m)
    if bottleneck_edges:
        fg_bottlenecks.add_to(m)
    if flow_dict:
        fg_flow.add_to(m)
    if highlight_path_nodes:
        fg_path.add_to(m)
    if baseline_path_nodes:
        fg_base_route.add_to(m)
    if optimized_path_nodes:
        fg_opt_route.add_to(m)

    # Add Layer Control
    folium.LayerControl(position="topright", collapsed=False).add_to(m)

    # Add Fullscreen Control
    plugins.Fullscreen(position="topleft").add_to(m)

    # Add Legend if requested
    if show_legend:
        m.get_root().html.add_child(folium.Element(build_map_legend_html()))

    return m

def render_gis_map_in_streamlit(
    m: Any,
    height: int = 600,
    key: Optional[str] = None
):
    """
    Renders the Folium map inside Streamlit.
    Optimized to prevent unnecessary re-running and provides multi-tiered rendering fallbacks.
    """
    if not HAS_FOLIUM:
        import sys
        py_exe = sys.executable
        st.error(
            f"### ⚠️ Interactive GIS Map Component Unavailable\n\n"
            f"`folium` is not installed in the currently active Python runtime:\n"
            f"- **Active Interpreter:** `{py_exe}`\n\n"
            f"To enable interactive OpenStreetMap / Leaflet navigation, run in your terminal:\n"
            f"```bash\n"
            f'"{py_exe}" -m pip install folium streamlit-folium geopandas osmnx\n'
            f"```"
        )
        return

    if m is None:
        st.warning(
            "⚠️ **GIS Map Notice**: No map object was generated for the current parameter configuration. "
            "Please verify that origin and destination nodes are distinct and valid."
        )
        return

    # Tier 1: Interactive bi-directional Leaflet widget via streamlit-folium
    if HAS_STREAMLIT_FOLIUM:
        try:
            st_folium(
                m,
                height=height,
                use_container_width=True,
                returned_objects=[],  # Do not trigger rerun on map pan/zoom
                key=key
            )
            return
        except Exception:
            # Fall through to Tier 2 iframe rendering if component bridge encounters an error
            pass

    # Tier 2: Resilient Leaflet HTML iframe rendering fallback
    # Guarantees the interactive map ALWAYS renders if folium is available
    try:
        html_content = m._repr_html_()
        st.components.v1.html(html_content, height=height)
    except Exception as err:
        st.error(f"⚠️ Error rendering Leaflet map: {err}")

def build_hospital_popup(h_row: Dict[str, Any], c_row: Optional[Dict[str, Any]] = None) -> str:
    """Builds an informative HTML popup card for a hospital facility and its snapped road connection."""
    name = h_row.get("hospital_name", "Hospital")
    hid = h_row.get("hospital_id", "N/A")
    verif = h_row.get("verification_status", "HOSPITAL_EMERGENCY_UNVERIFIED")
    srv = h_row.get("emergency_service_type", "GENERAL_HOSPITAL_UNVERIFIED")
    amenity = h_row.get("amenity", "hospital")
    addr = h_row.get("address", "Bengaluru, Karnataka")
    if not addr or pd.isna(addr):
        addr = "Bengaluru, Karnataka"
    phone = h_row.get("phone", "N/A")
    if pd.isna(phone):
        phone = "N/A"
    lat = h_row.get("latitude", 0.0)
    lon = h_row.get("longitude", 0.0)

    # Color badge
    color_map = {
        "VERIFIED_EMERGENCY": "#10B981",
        "EMERGENCY_PROBABLE_UNVERIFIED": "#3B82F6",
        "HOSPITAL_EMERGENCY_UNVERIFIED": "#F59E0B",
        "GENERAL_HEALTHCARE": "#64748B",
        "DUPLICATE_ENTRY": "#9333EA",
        "INCOMPLETE_OR_QUESTIONABLE": "#EF4444"
    }
    badge_color = color_map.get(verif, "#64748B")

    # Snapping info
    snap_html = ""
    if c_row is not None and not pd.isna(c_row.get("snapping_distance_m")):
        d_snap = c_row.get("snapping_distance_m", 0.0)
        c_stat = c_row.get("connection_status", "UNMATCHED")
        c_road = c_row.get("nearest_road_name", "Arterial Link")
        c_node = c_row.get("nearest_intersection_name", "Junction")
        t_acc = c_row.get("estimated_access_time_min", "N/A")
        c_badge_color = "#10B981" if c_stat == "DIRECT_GATE_PROXIMITY" else ("#F59E0B" if "ESTIMATED" in c_stat else "#EF4444")
        snap_html = f"""
        <div style="margin-top: 6px; padding: 6px; background: #F1F5F9; border-radius: 4px; border-left: 3px solid {c_badge_color};">
            <div style="font-weight: 700; color: #1E293B; font-size: 11px;">🔗 Road Network Access</div>
            <div style="color: #475569; font-size: 10px; margin-top: 2px;"><b>Connection Status:</b> <span style="color: {c_badge_color}; font-weight: 700;">{c_stat}</span></div>
            <div style="color: #475569; font-size: 10px;"><b>Nearest Road:</b> {c_road}</div>
            <div style="color: #475569; font-size: 10px;"><b>Nearest Junction:</b> {c_node}</div>
            <div style="color: #475569; font-size: 10px;"><b>Snapping Distance:</b> <b>{d_snap:,.1f} meters</b></div>
            <div style="color: #475569; font-size: 10px;"><b>Est. Driveway Delay:</b> <b>{t_acc} min</b></div>
        </div>
        """
    else:
        snap_html = """
        <div style="margin-top: 6px; padding: 6px; background: #FEF2F2; border-radius: 4px; border-left: 3px solid #EF4444;">
            <div style="font-weight: 700; color: #991B1B; font-size: 11px;">⚠️ Unmatched / Exceeds Threshold</div>
            <div style="color: #B91C1C; font-size: 10px;">No candidate arterial road node within configured distance.</div>
        </div>
        """

    html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 12px; width: 290px; color: #0F172A; padding: 4px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; border-bottom: 2px solid {badge_color}; padding-bottom: 4px;">
            <b style="font-size: 13px; color: #0F172A;">🏥 {name}</b>
        </div>
        <div style="margin-bottom: 6px;">
            <span style="background: {badge_color}; color: #FFFFFF; font-size: 9px; font-weight: 700; padding: 2px 6px; border-radius: 4px; text-transform: uppercase;">
                {verif}
            </span>
            <span style="font-size: 10px; color: #64748B; margin-left: 6px;">ID: <code>{hid}</code></span>
        </div>
        <table style="width: 100%; border-collapse: collapse; font-size: 10.5px; margin-bottom: 4px;">
            <tr><td style="color:#64748B; padding:2px 0;">Classification:</td><td><b>{srv}</b></td></tr>
            <tr><td style="color:#64748B; padding:2px 0;">Coordinates:</td><td><b>{lat:.4f}°N, {lon:.4f}°E</b></td></tr>
            <tr><td style="color:#64748B; padding:2px 0;">Address:</td><td>{addr}</td></tr>
            <tr><td style="color:#64748B; padding:2px 0;">Phone:</td><td>{phone}</td></tr>
        </table>
        {snap_html}
    </div>
    """
    return html

def build_hospital_validation_legend() -> str:
    """Builds a floating HTML legend for hospital snapping validation with a clean light clinical design."""
    return """
    <div style="
        position: fixed; 
        bottom: 24px; 
        left: 24px; 
        z-index: 9999; 
        background: rgba(255, 255, 255, 0.96); 
        border: 1px solid #E2E8F0; 
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.08);
        padding: 10px 14px; 
        border-radius: 8px; 
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 11px; 
        color: #0F172A;
        max-width: 280px;
        backdrop-filter: blur(4px);
    ">
        <div style="font-weight: 700; color: #0284C7; margin-bottom: 6px; font-size: 12px; letter-spacing: 0.04em;">
            🏥 HOSPITAL VALIDATION LEGEND
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 4px;">
            <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #16A34A; margin-right: 8px;"></span>
            <span>Verified Emergency (103)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 4px;">
            <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #2563EB; margin-right: 8px;"></span>
            <span>Probable Emergency Tertiary (51)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 4px;">
            <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #F59E0B; margin-right: 8px;"></span>
            <span>General Hospital Unverified (869)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 4px;">
            <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #94A3B8; margin-right: 8px;"></span>
            <span>Non-Emergency Clinic (26)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 6px;">
            <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #DC2626; margin-right: 8px;"></span>
            <span>Unmatched / >2km Threshold (334)</span>
        </div>
        <div style="border-top: 1px solid #E2E8F0; padding-top: 5px; margin-top: 5px; font-size: 10px; color: #64748B;">
            <i>All 1,084 hospitals geocoded and snapped to arterial network.</i>
        </div>
    </div>
    """

def create_hospital_validation_map(
    df_hospitals: Optional[pd.DataFrame] = None,
    df_connections: Optional[pd.DataFrame] = None,
    intersections: Optional[List[Dict[str, Any]]] = None,
    roads: Optional[List[Dict[str, Any]]] = None,
    center_lat: float = BENGALURU_LAT,
    center_lon: float = BENGALURU_LON,
    zoom_start: int = 12,
    show_connectors: bool = True,
    status_filter: Optional[List[str]] = None,
    max_hospitals: int = 500,
    hospitals_df: Optional[pd.DataFrame] = None,
    connections_df: Optional[pd.DataFrame] = None,
    **kwargs: Any
) -> Optional[Any]:
    """
    Creates a dedicated multi-layer Folium GIS Map validating hospital locations,
    classification statuses, and snapping connectors to the road network.
    """
    if df_hospitals is None and hospitals_df is not None:
        df_hospitals = hospitals_df
    if df_connections is None and connections_df is not None:
        df_connections = connections_df
    if df_hospitals is None:
        df_hospitals = pd.DataFrame()
    if df_connections is None:
        df_connections = pd.DataFrame()

    if not HAS_FOLIUM:
        return None

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom_start,
        tiles=None,
        control_scale=True
    )

    # Base Tile Layers
    folium.TileLayer(
        tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        name="OpenStreetMap (Default)",
        overlay=False,
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
        attr='&copy; <a href="https://carto.com/">CARTO</a>',
        name="CartoDB Voyager (Streets)",
        overlay=False,
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        attr='&copy; <a href="https://carto.com/">CARTO</a>',
        name="CartoDB Positron (Light Canvas)",
        overlay=False,
        control=True
    ).add_to(m)

    # Road Network Layer
    fg_roads = folium.FeatureGroup(name="🛣️ Arterial Roads (OSM Polylines)", show=True)
    if roads:
        for r in roads:
            geom = r.get("geometry", [])
            if geom and len(geom) >= 2:
                folium.PolyLine(
                    locations=geom,
                    color="#0284C7",
                    weight=2.2,
                    opacity=0.65,
                    tooltip=r.get("road_name", "Arterial Link")
                ).add_to(fg_roads)
    fg_roads.add_to(m)

    # Intersections Layer
    fg_nodes = folium.FeatureGroup(name="📍 Signalized Intersections (226 Nodes)", show=False)
    if intersections:
        for node in intersections:
            lat = float(node.get("latitude", BENGALURU_LAT))
            lon = float(node.get("longitude", BENGALURU_LON))
            nid = node.get("intersection_id", "")
            nname = node.get("name", nid)
            folium.CircleMarker(
                location=[lat, lon],
                radius=4.5,
                color="#0F172A",
                weight=1,
                fill=True,
                fill_color="#38BDF8",
                fill_opacity=0.8,
                tooltip=f"Junction: {nname} ({nid})"
            ).add_to(fg_nodes)
    fg_nodes.add_to(m)

    # Hospital Feature Groups by Classification
    fg_verified = folium.FeatureGroup(name="🟢 Verified Emergency Trauma (103)", show=True)
    fg_probable = folium.FeatureGroup(name="🔵 Probable Emergency Tertiary (51)", show=True)
    fg_unverified = folium.FeatureGroup(name="🟡 General Hospitals Unverified (869)", show=False)
    fg_general = folium.FeatureGroup(name="⚪ Clinics & Specialty (26)", show=False)
    fg_unmatched = folium.FeatureGroup(name="🔴 Unmatched Facilities (>2km)", show=False)
    fg_connectors = folium.FeatureGroup(name="📏 Snapping Connector Links", show=show_connectors)

    # Index connections by hospital_id
    conn_dict = df_connections.set_index("hospital_id").to_dict(orient="index") if not df_connections.empty else {}

    # Render Hospitals
    df_render = df_hospitals.copy()
    if status_filter:
        df_render = df_render[df_render["verification_status"].isin(status_filter)]
    if len(df_render) > max_hospitals:
        df_render = df_render.head(max_hospitals)

    for _, row in df_render.iterrows():
        lat = row.get("latitude")
        lon = row.get("longitude")
        if pd.isna(lat) or pd.isna(lon):
            continue

        hid = row["hospital_id"]
        verif = row.get("verification_status", "HOSPITAL_EMERGENCY_UNVERIFIED")
        c_info = conn_dict.get(hid)

        popup_html = build_hospital_popup(row.to_dict(), c_info)
        popup = folium.Popup(popup_html, max_width=320)
        h_name = row.get("hospital_name", "Hospital")

        is_unmatched = c_info.get("exceeds_threshold", False) if c_info else False

        # Visual marker styling
        if is_unmatched:
            folium.CircleMarker(
                location=[lat, lon],
                radius=5.5,
                color="#7F1D1D",
                weight=1.2,
                fill=True,
                fill_color="#EF4444",
                fill_opacity=0.9,
                popup=popup,
                tooltip=f"🚨 [UNMATCHED] {h_name}"
            ).add_to(fg_unmatched)

        elif verif == "VERIFIED_EMERGENCY":
            folium.Marker(
                location=[lat, lon],
                popup=popup,
                tooltip=f"🟢 [VERIFIED EMERGENCY] {h_name}",
                icon=folium.Icon(color="green", icon="plus-sign", prefix="glyphicon")
            ).add_to(fg_verified)

        elif verif == "EMERGENCY_PROBABLE_UNVERIFIED":
            folium.Marker(
                location=[lat, lon],
                popup=popup,
                tooltip=f"🔵 [PROBABLE EMERGENCY] {h_name}",
                icon=folium.Icon(color="blue", icon="plus-sign", prefix="glyphicon")
            ).add_to(fg_probable)

        elif verif == "HOSPITAL_EMERGENCY_UNVERIFIED":
            folium.CircleMarker(
                location=[lat, lon],
                radius=4.5,
                color="#78350F",
                weight=1.0,
                fill=True,
                fill_color="#F59E0B",
                fill_opacity=0.85,
                popup=popup,
                tooltip=f"🟡 {h_name} (Unverified Casualty)"
            ).add_to(fg_unverified)

        else:
            folium.CircleMarker(
                location=[lat, lon],
                radius=4.0,
                color="#334155",
                weight=1.0,
                fill=True,
                fill_color="#94A3B8",
                fill_opacity=0.8,
                popup=popup,
                tooltip=f"⚪ {h_name} ({verif})"
            ).add_to(fg_general)

        # Draw Connector line if matched and available
        if show_connectors and c_info and not is_unmatched:
            s_lat = c_info.get("snapped_lat")
            s_lon = c_info.get("snapped_lon")
            d_snap = c_info.get("snapping_distance_m", 0.0)
            if s_lat is not None and s_lon is not None:
                folium.PolyLine(
                    locations=[[lat, lon], [s_lat, s_lon]],
                    color="#10B981" if verif == "VERIFIED_EMERGENCY" else "#38BDF8",
                    weight=1.8,
                    dash_array="4, 4",
                    opacity=0.75,
                    tooltip=f"Connector: {h_name} -> {c_info.get('nearest_road_name', 'Road')} ({d_snap:,.0f}m)"
                ).add_to(fg_connectors)

    fg_verified.add_to(m)
    fg_probable.add_to(m)
    fg_unverified.add_to(m)
    fg_general.add_to(m)
    fg_unmatched.add_to(m)
    fg_connectors.add_to(m)

    folium.LayerControl(position="topright", collapsed=False).add_to(m)
    plugins.Fullscreen(position="topleft").add_to(m)
    m.get_root().html.add_child(folium.Element(build_hospital_validation_legend()))

    return m

def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates initial bearing in degrees [0, 360) from point 1 to point 2."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlam = math.radians(lon2 - lon1)
    y = math.sin(dlam) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlam)
    bearing = (math.degrees(math.atan2(y, x)) + 360.0) % 360.0
    return bearing

def bearing_to_cardinal(bearing: float) -> str:
    """Converts bearing degrees to 8-point cardinal direction string."""
    dirs = ["North", "North-East", "East", "South-East", "South", "South-West", "West", "North-West"]
    idx = int((bearing + 22.5) // 45) % 8
    return dirs[idx]

def build_signal_marker_popup(sig: Dict[str, Any]) -> str:
    """Builds an informative HTML popup card for a traffic signal marker with timing details."""
    name = sig.get("junction_name", sig.get("name", "Signalized Junction"))
    pdf = sig.get("source_pdf", "BEL_Engineering_Drawing.pdf")
    page = sig.get("source_page", sig.get("page_number", 1))
    c_sec = float(sig.get("cycle_sec", 120.0))
    g_sec = float(sig.get("green_sec", 30.0))
    r_sec = float(sig.get("red_sec", max(0.0, c_sec - g_sec)))
    d_sec = float(sig.get("signal_delay_sec", 30.0))
    d_min = float(sig.get("signal_delay_min", round(d_sec / 60.0, 2)))
    v_stat = str(sig.get("verification_status", "VERIFIED"))
    v_color = "#10B981" if v_stat == "VERIFIED" else ("#F59E0B" if v_stat == "UNVERIFIED" else "#EF4444")
    plan = sig.get("plan_name", "WEEKDAY_MORNING_PEAK")
    app = sig.get("approach_code", "A")

    return f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 12px; width: 280px; padding: 4px; color: #0F172A;">
        <div style="font-weight: 700; color: #0369A1; border-bottom: 2px solid #0284C7; padding-bottom: 4px; margin-bottom: 5px;">
            🚦 {name}
        </div>
        <div style="margin-bottom: 6px;">
            <span style="background: {v_color}; color: #FFFFFF; font-size: 9px; font-weight: 700; padding: 2px 6px; border-radius: 4px;">
                {v_stat}
            </span>
            <span style="font-size: 10px; color: #64748B; margin-left: 6px;">Plan: <b>{plan}</b></span>
        </div>
        <table style="width: 100%; border-collapse: collapse; font-size: 11px; margin-bottom: 6px;">
            <tr><td style="color:#64748B;">Approach & Phase:</td><td><b>Arm {app}</b></td></tr>
            <tr><td style="color:#64748B;">Cycle Length (C):</td><td><b>{c_sec:.0f} seconds</b></td></tr>
            <tr><td style="color:#64748B;">Green Duration (G):</td><td><b>{g_sec:.0f} seconds</b></td></tr>
            <tr><td style="color:#64748B;">Red Duration (R):</td><td><b>{r_sec:.0f} seconds</b></td></tr>
            <tr style="background: #F0FDF4;"><td style="color:#166534; font-weight:700;">Est. Signal Delay:</td><td style="color:#166534; font-weight:700;"><b>{d_sec:.1f}s ({d_min:.2f} min)</b></td></tr>
        </table>
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 4px; padding: 4px 6px; font-size: 10px; color: #475569; margin-bottom: 4px;">
            <b>Provenance:</b> PDF Drawing <code>{pdf}</code> (p. {page})
        </div>
        <div style="font-size: 9px; color: #94A3B8; font-style: italic;">
            *Webster undersaturated uniform delay: R²/(2C). Static timing; no live preemption implied.
        </div>
    </div>
    """

def build_ambulance_route_legend() -> str:
    """
    Builds a clean, light floating responsive HTML legend for the Ambulance Route Map.
    Includes explicit academic disclaimer separating routing selection from live congestion.
    """
    return """
    <div style="
        position: fixed;
        bottom: 24px;
        right: 24px;
        z-index: 1000;
        background: rgba(255, 255, 255, 0.96);
        backdrop-filter: blur(8px);
        border: 1px solid #E2E8F0;
        padding: 12px 14px;
        border-radius: 10px;
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.08);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        color: #0F172A;
        font-size: 11px;
        max-width: 280px;
        line-height: 1.4;
    ">
        <div style="font-weight: 700; color: #0284C7; font-size: 11.5px; margin-bottom: 6px; letter-spacing: 0.04em;">
            🚑 AMBULANCE ROUTE OPTIMIZATION
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 4px;">
            <span style="display: inline-block; width: 12px; height: 12px; background: #16A34A; border: 2px solid #FFFFFF; border-radius: 50%; box-shadow: 0 0 2px rgba(0,0,0,0.3); margin-right: 8px;"></span>
            <span><b>Ambulance Origin</b> (Dispatch)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 4px;">
            <span style="display: inline-block; width: 12px; height: 12px; background: #DC2626; border: 2px solid #FFFFFF; border-radius: 50%; box-shadow: 0 0 2px rgba(0,0,0,0.3); margin-right: 8px;"></span>
            <span><b>Destination Hospital</b> (Emergency)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 4px;">
            <span style="display: inline-block; width: 18px; height: 4px; background: #0284C7; border-radius: 2px; margin-right: 8px;"></span>
            <span><b>Primary Route</b> (Minimum Time)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 4px;">
            <span style="display: inline-block; width: 18px; height: 3px; background: #EA580C; border-radius: 2px; margin-right: 8px; border-top: 1px dashed #EA580C;"></span>
            <span><b>Alternative Route 1</b> (Yen's K=2)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 4px;">
            <span style="display: inline-block; width: 18px; height: 3px; background: #7C3AED; border-radius: 2px; margin-right: 8px; border-top: 1px dashed #7C3AED;"></span>
            <span><b>Alternative Route 2</b> (Yen's K=3)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 4px;">
            <span style="display: inline-block; width: 18px; height: 3px; background: #F59E0B; border-radius: 2px; margin-right: 8px; border-top: 1px dashed #F59E0B;"></span>
            <span><b>Baseline Route</b> (Road Time Only)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 4px;">
            <span style="display: inline-block; width: 10px; height: 10px; background: #0284C7; border: 1.5px solid #FFFFFF; border-radius: 50%; box-shadow: 0 0 2px rgba(0,0,0,0.3); margin-right: 8px;"></span>
            <span><b>Verified Traffic Signal</b> (Webster)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 4px;">
            <span style="display: inline-block; width: 10px; height: 10px; background: #94A3B8; border: 1.5px solid #FFFFFF; border-radius: 50%; box-shadow: 0 0 2px rgba(0,0,0,0.3); margin-right: 8px;"></span>
            <span><b>Unverified Signal</b> (Estimated)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 6px;">
            <span style="display: inline-block; width: 18px; height: 2px; background: #CBD5E1; border-radius: 1px; margin-right: 8px;"></span>
            <span style="color: #64748B;">Arterial Road Network</span>
        </div>
        <div style="border-top: 1px solid #E2E8F0; padding-top: 5px; font-size: 9.5px; color: #64748B;">
            ⚠️ <i>Route colors denote mathematical path selection; live congestion not implied.</i>
        </div>
    </div>
    """

def create_ambulance_route_map(
    center_lat: float = BENGALURU_LAT,
    center_lon: float = BENGALURU_LON,
    zoom_start: int = 13,
    primary_route: Optional[Dict[str, Any]] = None,
    alternative_routes: Optional[List[Dict[str, Any]]] = None,
    comparison_route: Optional[Dict[str, Any]] = None,
    scenario_routes: Optional[Dict[str, Dict[str, Any]]] = None,
    signal_nodes: Optional[List[Dict[str, Any]]] = None,
    roads: Optional[List[Dict[str, Any]]] = None,
    origin_info: Optional[Dict[str, Any]] = None,
    destination_info: Optional[Dict[str, Any]] = None,
    hospital_info: Optional[Dict[str, Any]] = None,
    hospitals_catalog: Optional[pd.DataFrame] = None,
    show_background_roads: bool = True,
    show_legend: bool = True
) -> Optional[Any]:
    """
    Creates an interactive, multi-layer GIS route visualization map for ambulance dispatch.
    Implements Task 2 and Task 4 of Phase 3, Task 9 of Phase 4, and Task 8 of Phase 5.
    """
    if not HAS_FOLIUM:
        return None
    # Auto-center on route bounds if available
    all_points = []
    if primary_route and primary_route.get("route_geometry"):
        all_points.extend(primary_route["route_geometry"])
    if comparison_route and comparison_route.get("route_geometry"):
        all_points.extend(comparison_route["route_geometry"])
    if scenario_routes:
        for sc in scenario_routes.values():
            if sc.get("route_geometry"):
                all_points.extend(sc["route_geometry"])
    if origin_info and "latitude" in origin_info and "longitude" in origin_info:
        all_points.append([origin_info["latitude"], origin_info["longitude"]])
    if hospital_info and "latitude" in hospital_info and "longitude" in hospital_info:
        all_points.append([hospital_info["latitude"], hospital_info["longitude"]])

    if all_points:
        lats = [p[0] for p in all_points if not pd.isna(p[0])]
        lons = [p[1] for p in all_points if not pd.isna(p[1])]
        if lats and lons:
            center_lat = sum(lats) / len(lats)
            center_lon = sum(lons) / len(lons)

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom_start,
        tiles=None,
        control_scale=True
    )

    # Base Tile Layers
    folium.TileLayer(
        tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        name="OpenStreetMap Standard",
        overlay=False,
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        attr='&copy; <a href="https://carto.com/">CARTO</a>',
        name="CartoDB Positron (Clinical Light)",
        overlay=False,
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
        attr='&copy; <a href="https://carto.com/">CARTO</a>',
        name="CartoDB Voyager (Street Detail)",
        overlay=False,
        control=True
    ).add_to(m)

    # 1. Background Road Network Layer
    fg_roads = folium.FeatureGroup(name="🛣️ Arterial Road Network (Centerlines)", show=show_background_roads)
    if roads:
        for r in roads:
            coords = r.get("geometry", [])
            if not coords or len(coords) < 2:
                u_lat, u_lon = r.get("u_lat"), r.get("u_lon")
                v_lat, v_lon = r.get("v_lat"), r.get("v_lon")
                if None not in (u_lat, u_lon, v_lat, v_lon):
                    coords = [[u_lat, u_lon], [v_lat, v_lon]]

            if coords and len(coords) >= 2:
                rname = r.get("road_name", "Arterial Road")
                folium.PolyLine(
                    locations=coords,
                    color="#94A3B8",
                    weight=2.0,
                    opacity=0.55,
                    tooltip=f"{rname} (Speed: {r.get('speed_kmh', 30)} km/h)"
                ).add_to(fg_roads)
    fg_roads.add_to(m)

    # 2. Alternative Routes Feature Groups (Yen's K-Shortest Paths)
    alt_colors = ["#EA580C", "#7C3AED", "#F59E0B", "#2563EB", "#0D9488"]
    if alternative_routes:
        for idx, alt in enumerate(alternative_routes):
            rank = alt.get("rank", idx + 2)
            # Skip if this is rank 1 (which is primary)
            if rank == 1 and primary_route:
                continue

            color = alt_colors[(rank - 2) % len(alt_colors)]
            fg_alt = folium.FeatureGroup(
                name=f"🔶 Alternative {rank - 1} (Option {rank}: {alt.get('total_time_min', 0):.1f} min)",
                show=True
            )

            geom = alt.get("route_geometry", [])
            if geom and len(geom) >= 2:
                t_min = alt.get("total_time_min", 0.0)
                d_km = alt.get("total_distance_km", 0.0)
                d_desc = alt.get("divergence_description", "Alternative Path")

                popup_html = f"""
                <div style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 11.5px; width: 230px; padding: 4px; color: #0F172A;">
                    <div style="font-weight: 700; color: {color}; border-bottom: 2px solid {color}; padding-bottom: 3px; margin-bottom: 4px;">
                        Option {rank} (Alternative {rank - 1})
                    </div>
                    <div><b>Est. Travel Time:</b> {t_min:.2f} min</div>
                    <div><b>Total Distance:</b> {d_km:.2f} km</div>
                    <div><b>Segments:</b> {alt.get('num_segments', 0)} links</div>
                    <div style="margin-top: 4px; font-size: 10px; color: #64748B;">{d_desc}</div>
                </div>
                """

                folium.PolyLine(
                    locations=geom,
                    color=color,
                    weight=4.5,
                    dash_array="6, 6",
                    opacity=0.88,
                    popup=folium.Popup(popup_html, max_width=260),
                    tooltip=f"Alternative {rank - 1} ({t_min:.1f} min, {d_km:.2f} km)"
                ).add_to(fg_alt)

            fg_alt.add_to(m)

    # 3. Primary Route Feature Group (Minimum Estimated Travel Time)
    fg_primary = folium.FeatureGroup(name="🔷 Primary Route (Minimum Travel Time)", show=True)
    fg_waypoints = folium.FeatureGroup(name="🚦 Primary Route Intersections", show=True)

    if primary_route and primary_route.get("route_geometry"):
        p_geom = primary_route["route_geometry"]
        p_time = primary_route.get("total_time_min", 0.0)
        p_dist = primary_route.get("total_distance_km", 0.0)
        p_speed = primary_route.get("average_speed_kmh", 0.0)

        primary_popup_html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 12px; width: 250px; padding: 4px; color: #0F172A;">
            <div style="font-weight: 700; color: #0284C7; border-bottom: 2px solid #0284C7; padding-bottom: 4px; margin-bottom: 6px;">
                🔷 Primary Ambulance Route (Optimal)
            </div>
            <table style="width: 100%; border-collapse: collapse; font-size: 11px;">
                <tr><td style="color:#64748B;">Est. Travel Time:</td><td><b>{p_time:.2f} min</b></td></tr>
                <tr><td style="color:#64748B;">Total Road Distance:</td><td><b>{p_dist:.2f} km</b></td></tr>
                <tr><td style="color:#64748B;">Average Speed:</td><td><b>{p_speed:.1f} km/h</b></td></tr>
                <tr><td style="color:#64748B;">Network Segments:</td><td><b>{primary_route.get('num_segments', 0)} links</b></td></tr>
                <tr><td style="color:#64748B;">Routing Objective:</td><td><b>Minimum Time (IRC:106)</b></td></tr>
            </table>
        </div>
        """

        folium.PolyLine(
            locations=p_geom,
            color="#0284C7",
            weight=6.0,
            opacity=0.95,
            popup=folium.Popup(primary_popup_html, max_width=280),
            tooltip=f"Primary Optimal Route ({p_time:.1f} min, {p_dist:.2f} km)"
        ).add_to(fg_primary)

        # Add waypoint nodes along the primary path
        path_edges = primary_route.get("path_edges", [])
        for edge in path_edges:
            step = edge.get("step", 1)
            e_geom = edge.get("geometry", [])
            w_point = e_geom[0] if e_geom else None
            if w_point:
                step_popup = f"""
                <div style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 11px; width: 210px; padding: 3px; color: #0F172A;">
                    <b style="color: #0284C7;">Step {step}: {edge.get('from_name', 'Junction')}</b><br/>
                    <b>Road:</b> {edge.get('road_name', 'Arterial Link')}<br/>
                    <b>Speed:</b> {edge.get('speed_kmh', 30)} km/h | <b>Time:</b> {edge.get('travel_time_sec', 0):.0f}s<br/>
                    <b>Distance:</b> {edge.get('length_m', 0):,.0f} m
                </div>
                """
                folium.CircleMarker(
                    location=w_point,
                    radius=4.5,
                    color="#0284C7",
                    weight=1.5,
                    fill=True,
                    fill_color="#FFFFFF",
                    fill_opacity=0.95,
                    popup=folium.Popup(step_popup, max_width=240),
                    tooltip=f"Step {step}: {edge.get('from_name', 'Node')}"
                ).add_to(fg_waypoints)

    fg_primary.add_to(m)
    fg_waypoints.add_to(m)

    # 3b. Comparison Baseline Route Feature Group (Free-Flow Road Travel Time)
    if comparison_route and comparison_route.get("route_geometry"):
        fg_comp = folium.FeatureGroup(name="🟠 Baseline Route (Road Time Only)", show=True)
        c_geom = comparison_route["route_geometry"]
        c_time = comparison_route.get("total_time_min", 0.0)
        c_dist = comparison_route.get("total_distance_km", 0.0)
        c_sig = comparison_route.get("total_signal_delay_min", 0.0)

        comp_popup_html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 12px; width: 250px; padding: 4px;">
            <div style="font-weight: 700; color: #EA580C; border-bottom: 2px solid #EA580C; padding-bottom: 4px; margin-bottom: 6px;">
                🟠 Baseline Route (Road Time Only)
            </div>
            <table style="width: 100%; border-collapse: collapse; font-size: 11px;">
                <tr><td style="color:#64748B;">Road Travel Time:</td><td><b>{c_time:.2f} min</b></td></tr>
                <tr><td style="color:#64748B;">Unmodeled Signal Delay:</td><td><b>+{c_sig:.2f} min</b></td></tr>
                <tr><td style="color:#64748B;">Total Signal-Aware Time:</td><td><b>{c_time + c_sig:.2f} min</b></td></tr>
                <tr><td style="color:#64748B;">Total Road Distance:</td><td><b>{c_dist:.2f} km</b></td></tr>
                <tr><td style="color:#64748B;">Objective:</td><td><b>Min Road Time (No Signal Penalty)</b></td></tr>
            </table>
        </div>
        """

        folium.PolyLine(
            locations=c_geom,
            color="#EA580C",
            weight=5.0,
            dash_array="8, 8",
            opacity=0.90,
            popup=folium.Popup(comp_popup_html, max_width=270),
            tooltip=f"Baseline Route ({c_time:.1f} min, {c_dist:.2f} km)"
        ).add_to(fg_comp)

        fg_comp.add_to(m)

    # 3b-2. Multi-Scenario Traffic Routes (Phase 5 Scenario Analysis)
    if scenario_routes:
        for sc_key, sc_data in scenario_routes.items():
            sc_label = sc_data.get("label", sc_key)
            sc_color = sc_data.get("color", "#2563EB")
            geom = sc_data.get("route_geometry", [])
            if not geom or len(geom) < 2:
                continue

            dist_km = sc_data.get("distance_km", sc_data.get("total_hospital_distance_km", 0.0))
            tot_time = sc_data.get("total_time_min", sc_data.get("total_hospital_time_min", 0.0))
            ff_time = sc_data.get("free_flow_time_min", tot_time)
            traff_del = sc_data.get("traffic_delay_min", 0.0)
            sig_del = sc_data.get("signal_delay_min", 0.0)
            spd = sc_data.get("average_speed_kmh", 0.0)

            fg_sc = folium.FeatureGroup(name=f"📊 {sc_label} ({tot_time:.1f} min)", show=True)
            sc_popup = f"""
            <div style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 11.5px; width: 250px; padding: 4px;">
                <div style="font-weight: 700; color: {sc_color}; border-bottom: 2px solid {sc_color}; padding-bottom: 3px; margin-bottom: 5px;">
                    {sc_label}
                </div>
                <table style="width: 100%; border-collapse: collapse; font-size: 11px;">
                    <tr><td style="color:#64748B;">Total Journey:</td><td><b>{tot_time:.2f} min</b></td></tr>
                    <tr><td style="color:#64748B;">Distance:</td><td><b>{dist_km:.2f} km</b></td></tr>
                    <tr><td style="color:#64748B;">Free-Flow Time:</td><td><b>{ff_time:.2f} min</b></td></tr>
                    <tr><td style="color:#64748B;">Traffic Delay:</td><td><b>+{traff_del:.2f} min</b></td></tr>
                    <tr><td style="color:#64748B;">Signal Delay:</td><td><b>+{sig_del:.2f} min</b></td></tr>
                    <tr><td style="color:#64748B;">Effective Speed:</td><td><b>{spd:.1f} km/h</b></td></tr>
                </table>
            </div>
            """
            is_combined = (sc_key == "COMBINED_TRAFFIC_SIGNAL")
            folium.PolyLine(
                locations=geom,
                color=sc_color,
                weight=6.0 if is_combined else 4.0,
                opacity=0.92,
                popup=folium.Popup(sc_popup, max_width=270),
                tooltip=f"{sc_label} ({tot_time:.1f} min, {dist_km:.2f} km)"
            ).add_to(fg_sc)
            fg_sc.add_to(m)

    # 3c. Verified Traffic Signals & Delays Feature Group
    if signal_nodes:
        fg_signals = folium.FeatureGroup(name="🚦 Verified Signal Timing Delays", show=True)
        for s_info in signal_nodes:
            s_lat = s_info.get("latitude")
            s_lon = s_info.get("longitude")
            if s_lat and s_lon and not (pd.isna(s_lat) or pd.isna(s_lon)):
                popup_c = build_signal_marker_popup(s_info)
                v_stat = s_info.get("verification_status", "VERIFIED")
                fill_c = "#0284C7" if v_stat == "VERIFIED" else "#94A3B8"
                delay_s = s_info.get("signal_delay_sec", 30.0)

                folium.CircleMarker(
                    location=[s_lat, s_lon],
                    radius=5.5,
                    color="#FFFFFF",
                    weight=1.5,
                    fill=True,
                    fill_color=fill_c,
                    fill_opacity=0.92,
                    popup=folium.Popup(popup_c, max_width=290),
                    tooltip=f"🚦 {s_info.get('name', 'Signal')}: {delay_s:.1f}s delay ({v_stat})"
                ).add_to(fg_signals)

        fg_signals.add_to(m)

    # 4. Destination Hospital Feature Group
    fg_dest = folium.FeatureGroup(name="🏥 Destination Hospital", show=True)
    if hospital_info:
        h_lat = hospital_info.get("latitude")
        h_lon = hospital_info.get("longitude")
        if h_lat and h_lon and not (pd.isna(h_lat) or pd.isna(h_lon)):
            h_name = hospital_info.get("hospital_name", "Hospital")
            h_verif = hospital_info.get("verification_status", "HOSPITAL_EMERGENCY_UNVERIFIED")
            h_addr = hospital_info.get("address", "Bengaluru, Karnataka")
            h_delay = hospital_info.get("estimated_access_time_min", 1.0)

            dest_popup_html = f"""
            <div style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 12px; width: 270px; padding: 4px;">
                <div style="font-weight: 700; color: #DC2626; border-bottom: 2px solid #EF4444; padding-bottom: 4px; margin-bottom: 4px;">
                    🏥 DESTINATION: {h_name}
                </div>
                <div style="font-size: 10px; color: #10B981; font-weight: 700; margin-bottom: 4px;">
                    STATUS: {h_verif}
                </div>
                <div style="font-size: 11px; margin-bottom: 4px;"><b>Address:</b> {h_addr}</div>
                <div style="background: #FEF2F2; border-left: 3px solid #EF4444; padding: 4px 6px; border-radius: 4px; font-size: 10px; color: #991B1B;">
                    <b>Driveway Access:</b> 15 km/h campus speed + 1.0 min gate delay ({h_delay} min total).
                </div>
            </div>
            """

            folium.Marker(
                location=[h_lat, h_lon],
                popup=folium.Popup(dest_popup_html, max_width=300),
                tooltip=f"🏥 DESTINATION: {h_name}",
                icon=folium.Icon(color="red", icon="plus-sign", prefix="glyphicon")
            ).add_to(fg_dest)

            # Draw connector polyline to snapped road node if available
            s_lat = hospital_info.get("snapped_lat")
            s_lon = hospital_info.get("snapped_lon")
            if s_lat and s_lon and not (pd.isna(s_lat) or pd.isna(s_lon)):
                folium.PolyLine(
                    locations=[[s_lat, s_lon], [h_lat, h_lon]],
                    color="#DC2626",
                    weight=2.5,
                    dash_array="4, 4",
                    opacity=0.85,
                    tooltip=f"Hospital Driveway Connection ({hospital_info.get('snapping_distance_m', 0):,.0f} m)"
                ).add_to(fg_dest)

    elif destination_info:
        d_lat = destination_info.get("latitude")
        d_lon = destination_info.get("longitude")
        if d_lat and d_lon and not (pd.isna(d_lat) or pd.isna(d_lon)):
            d_name = destination_info.get("name", destination_info.get("intersection_id", "Destination"))
            folium.Marker(
                location=[d_lat, d_lon],
                popup=f"<b>Destination Intersection:</b> {d_name}",
                tooltip=f"Destination: {d_name}",
                icon=folium.Icon(color="red", icon="record", prefix="glyphicon")
            ).add_to(fg_dest)

    fg_dest.add_to(m)

    # 5. Ambulance Origin Feature Group
    fg_origin = folium.FeatureGroup(name="🚑 Ambulance Origin", show=True)
    if origin_info:
        o_lat = origin_info.get("latitude")
        o_lon = origin_info.get("longitude")
        if o_lat and o_lon and not (pd.isna(o_lat) or pd.isna(o_lon)):
            o_name = origin_info.get("name", origin_info.get("intersection_id", "Origin"))
            o_id = origin_info.get("intersection_id", "N/A")
            o_corr = origin_info.get("corridor", "Arterial")

            origin_popup_html = f"""
            <div style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 12px; width: 240px; padding: 4px;">
                <div style="font-weight: 700; color: #16A34A; border-bottom: 2px solid #10B981; padding-bottom: 4px; margin-bottom: 4px;">
                    🚑 AMBULANCE DISPATCH ORIGIN
                </div>
                <div><b>Intersection:</b> {o_name}</div>
                <div><b>ID:</b> <code>{o_id}</code></div>
                <div><b>Corridor:</b> {o_corr}</div>
                <div style="margin-top: 4px; color: #16A34A; font-weight: 600; font-size: 10px;">
                    ● Unit Status: Available for Immediate Departure
                </div>
            </div>
            """

            folium.Marker(
                location=[o_lat, o_lon],
                popup=folium.Popup(origin_popup_html, max_width=260),
                tooltip=f"🚑 ORIGIN: {o_name}",
                icon=folium.Icon(color="green", icon="play", prefix="glyphicon")
            ).add_to(fg_origin)

    fg_origin.add_to(m)

    # 6. Optional Surrounding Hospitals Catalog Overlay
    if hospitals_catalog is not None and not hospitals_catalog.empty:
        fg_nearby = folium.FeatureGroup(name="🏥 Nearby Emergency Hospitals", show=False)
        for _, h_row in hospitals_catalog.head(150).iterrows():
            lat = h_row.get("latitude")
            lon = h_row.get("longitude")
            if pd.isna(lat) or pd.isna(lon):
                continue
            verif = h_row.get("verification_status", "HOSPITAL_EMERGENCY_UNVERIFIED")
            hname = h_row.get("hospital_name", "Hospital")
            folium.CircleMarker(
                location=[lat, lon],
                radius=4.0,
                color="#DC2626" if verif == "VERIFIED_EMERGENCY" else "#F59E0B",
                weight=1.0,
                fill=True,
                fill_color="#EF4444" if verif == "VERIFIED_EMERGENCY" else "#FBBF24",
                fill_opacity=0.8,
                tooltip=f"{hname} ({verif})"
            ).add_to(fg_nearby)
        fg_nearby.add_to(m)

    # Controls & UI Elements
    folium.LayerControl(position="topright", collapsed=False).add_to(m)
    plugins.Fullscreen(position="topleft").add_to(m)

    if show_legend:
        m.get_root().html.add_child(folium.Element(build_ambulance_route_legend()))

    return m

