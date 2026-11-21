"""
Page 2 / Hospital Finder: Hospital Data Integration, Search & Network Snapping.
Ambulance Route Optimization — Bengaluru.

Provides:
- Interactive hospital search across 1,084 facilities.
- Evidence-based emergency trauma classification tiers.
- Network snapping metrics (nearest road, intersection, access delay).
- One-click handoff to Ambulance Route Optimizer.
- Spatial snapping inspection map.
"""

import os
import streamlit as st
import pandas as pd
from components.ui_helpers import (
    load_custom_css,
    render_header,
    render_metric,
    render_workflow_navigation,
    load_gis_network,
    load_hospital_data
)
from components.gis_map import (
    create_hospital_validation_map,
    render_gis_map_in_streamlit
)

st.set_page_config(
    page_title="Hospital Finder & Snapping | Bengaluru GIS",
    page_icon="🏥",
    layout="wide"
)

load_custom_css()

render_header(
    title="Hospital Finder & Road Network Snapping",
    subtitle="Search 1,084 Healthcare Facilities, Inspect Emergency Triage Status & Connect to Route Optimizer",
    badge_text="GIS Facilities & Snapping",
    current_page="pages/2_Hospital_Finder.py"
)

# Load underlying GIS road network and hospitals
gis_mgr, roads_gis, df_intersections_gis = load_gis_network()
intersections_list = df_intersections_gis.to_dict(orient="records")
df_hospitals, df_connections = load_hospital_data()

# Top KPI Metrics Row
c1, c2, c3, c4 = st.columns(4)
total_hosp = len(df_hospitals)
n_verified_em = len(df_hospitals[df_hospitals["verification_status"] == "VERIFIED_EMERGENCY"])
n_probable_em = len(df_hospitals[df_hospitals["verification_status"] == "EMERGENCY_PROBABLE_UNVERIFIED"])
n_unverified_hosp = len(df_hospitals[df_hospitals["verification_status"] == "HOSPITAL_EMERGENCY_UNVERIFIED"])

render_metric(c1, "Total Mapped Facilities", f"{total_hosp:,}", "OSM Overpass GeoJSON Export", "normal")
render_metric(c2, "Verified Level 1 Emergency", f"{n_verified_em:,}", "Explicit emergency=yes Tag", "green")
render_metric(c3, "Probable Tertiary Trauma", f"{n_probable_em:,}", "Major Hospital Networks", "normal")
render_metric(c4, "General Hospital (Unverified)", f"{n_unverified_hosp:,}", "Casualty Status Unconfirmed", "amber")

st.markdown("---")

tab_search, tab_map_inspect, tab_audit = st.tabs([
    "🔍 Hospital Search & Route Handoff",
    "🗺️ Network Snapping GIS Map",
    "📊 Data Quality & Classification Audit"
])

# -------------------------------------------------------------
# TAB 1: HOSPITAL SEARCH & ROUTE HANDOFF
# -------------------------------------------------------------
with tab_search:
    st.markdown("#### Search Hospital Facilities & Hand Off to Route Optimizer")
    st.caption("Locate verified trauma hospitals or specialty care centers and instantly dispatch the Route Optimizer to that destination.")

    col_s1, col_s2, col_s3 = st.columns([2, 1.2, 1.2])
    with col_s1:
        query = st.text_input("Search hospital by name or address:", placeholder="e.g. Victoria, Bowring, St. John, Manipal, Fortis")
    with col_s2:
        tier_filter = st.selectbox(
            "Filter Verification Tier:",
            ["All Tiers", "VERIFIED_EMERGENCY", "EMERGENCY_PROBABLE_UNVERIFIED", "HOSPITAL_EMERGENCY_UNVERIFIED"]
        )
    with col_s3:
        snap_filter = st.selectbox(
            "Snapping Threshold:",
            ["All Facilities", "Snapped Within 2.0 km", "Exceeds 2.0 km Warning Threshold"]
        )

    # Filter DataFrame
    filtered_df = df_hospitals.copy()
    if query:
        q_low = query.lower()
        filtered_df = filtered_df[
            filtered_df["hospital_name"].str.lower().str.contains(q_low, na=False) |
            filtered_df["address"].str.lower().str.contains(q_low, na=False) |
            filtered_df["hospital_id"].str.lower().str.contains(q_low, na=False)
        ]
    if tier_filter != "All Tiers":
        filtered_df = filtered_df[filtered_df["verification_status"] == tier_filter]
    
    # Merge connection snapping information
    if not df_connections.empty:
        filtered_df = filtered_df.merge(
            df_connections[["hospital_id", "nearest_intersection_id", "nearest_road_name", "snapping_distance_m", "estimated_access_time_min", "exceeds_threshold"]],
            on="hospital_id",
            how="left"
        )
        if snap_filter == "Snapped Within 2.0 km":
            filtered_df = filtered_df[~filtered_df["exceeds_threshold"]]
        elif snap_filter == "Exceeds 2.0 km Warning Threshold":
            filtered_df = filtered_df[filtered_df["exceeds_threshold"]]

    st.write(f"Displaying **{len(filtered_df)}** matching facilities:")

    # Detailed Hospital Card Selector
    if not filtered_df.empty:
        hosp_options = filtered_df.head(100).to_dict(orient="records")
        hosp_labels = {
            r["hospital_id"]: f"{r['hospital_name']} ({r['verification_status']}) — {str(r.get('address', 'Bengaluru'))[:35]}"
            for r in hosp_options
        }
        
        selected_hid = st.selectbox(
            "Select facility to inspect emergency telemetry:",
            options=[r["hospital_id"] for r in hosp_options],
            format_func=lambda x: hosp_labels.get(x, x)
        )
        
        h_rec = next(r for r in hosp_options if r["hospital_id"] == selected_hid)
        
        # Hospital Telemetry Panel
        st.markdown(f"""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-top: 3px solid #16A34A; border-radius: 8px; padding: 16px; margin: 12px 0; box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05); color: #0F172A;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h3 style="margin: 0; color: #0284C7;">🏥 {h_rec['hospital_name']}</h3>
                <span class="provenance-badge badge-actual">{h_rec['verification_status']}</span>
            </div>
            <p style="color: #64748B; font-size: 13px; margin: 4px 0 12px 0;">ID: <code>{h_rec['hospital_id']}</code> | Coordinates: {h_rec['latitude']:.5f}, {h_rec['longitude']:.5f}</p>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; font-size: 13px; color: #334155;">
                <div><b>Emergency Service Type:</b><br/>{h_rec.get('emergency_service_type', 'Emergency Triage')}</div>
                <div><b>Address:</b><br/>{h_rec.get('address', 'Not documented')}</div>
                <div><b>Operator / Network:</b><br/>{h_rec.get('operator', 'Independent / Private')}</div>
                <div><b>Phone:</b><br/>{h_rec.get('phone', '108 / 112')}</div>
                <div><b>Snapped Entry Intersection:</b><br/><code>{h_rec.get('nearest_intersection_id', 'None')}</code></div>
                <div><b>Nearest Network Road:</b><br/>{h_rec.get('nearest_road_name', 'Arterial Link')}</div>
                <div><b>Snapping Distance:</b><br/><b>{h_rec.get('snapping_distance_m', 0):,.0f} m</b></div>
                <div><b>Campus Access Delay:</b><br/><b style="color: #D97706;">+{h_rec.get('estimated_access_time_min', 1.0):.1f} min</b></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_act1, col_act2 = st.columns([1.5, 2])
        with col_act1:
            if st.button("🚀 Set as Active Destination in Route Optimizer", type="primary", width="stretch"):
                st.session_state["target_hospital_id"] = h_rec["hospital_id"]
                st.session_state["destination_type"] = "HOSPITAL"
                st.switch_page("pages/3_Ambulance_Route_Optimizer.py")
        with col_act2:
            st.caption(f"Clicking dispatches this hospital to the Dijkstra routing engine with its **+{h_rec.get('estimated_access_time_min', 1.0):.1f} min** driveway access delay.")

    else:
        st.info("No healthcare facilities matched the current filter criteria.")

# -------------------------------------------------------------
# TAB 2: NETWORK SNAPPING GIS MAP
# -------------------------------------------------------------
with tab_map_inspect:
    st.markdown("#### Spatial Snapping & Hospital Cluster Map")
    st.caption("Visualizes hospital facilities (green = Level 1 verified, amber = unverified) and their connection lines to the 226 arterial road junctions.")

    # Build and render hospital validation map
    df_matched_table = df_hospitals[~df_hospitals["is_duplicate"]].merge(
        df_connections[["hospital_id", "nearest_intersection_id", "nearest_road_name", "snapping_distance_m", "estimated_access_time_min", "exceeds_threshold"]],
        on="hospital_id",
        how="inner"
    )

    m_hosp = create_hospital_validation_map(
        center_lat=12.9716,
        center_lon=77.5946,
        zoom_start=12,
        intersections=intersections_list,
        roads=roads_gis,
        df_hospitals=df_matched_table.head(150),
        df_connections=df_connections.head(150),
        hospitals_df=df_matched_table.head(150),
        connections_df=df_connections.head(150)
    )
    render_gis_map_in_streamlit(m_hosp, height=580, key="hospital_finder_map")

    st.markdown("##### Snapping Distance Distribution (Top Connected Facilities)")
    display_cols = [c for c in ["hospital_name", "verification_status", "nearest_intersection_id", "nearest_road_name", "snapping_distance_m", "estimated_access_time_min", "address"] if c in df_matched_table.columns]
    st.dataframe(
        df_matched_table[display_cols].sort_values(by="snapping_distance_m").head(50),
        width="stretch",
        hide_index=True
    )

# -------------------------------------------------------------
# TAB 3: DATA QUALITY & ATTRIBUTE AUDIT
# -------------------------------------------------------------
with tab_audit:
    st.markdown("#### Data Quality, Deduplication & Attribute Audit")
    c_q1, c_q2 = st.columns(2)
    with c_q1:
        st.markdown("**Verification Status Distribution**")
        st.dataframe(df_hospitals["verification_status"].value_counts(), width="stretch")
    with c_q2:
        st.markdown("**Data Quality Flags**")
        st.dataframe(df_hospitals["data_quality_issue"].value_counts(), width="stretch")
    
    st.markdown("##### Duplicate Entries Detected (Within 300m Proximity)")
    df_dups = df_hospitals[df_hospitals["is_duplicate"]]
    st.dataframe(
        df_dups[["hospital_id", "osm_id", "hospital_name", "latitude", "longitude", "duplicate_of_index"]],
        width="stretch",
        hide_index=True
    )

render_workflow_navigation(
    prev_page="pages/1_Road_Network_Explorer.py",
    prev_label="01. Road Network Explorer",
    next_page="pages/3_Ambulance_Route_Optimizer.py",
    next_label="03. Route Optimizer"
)
