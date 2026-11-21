"""
Page 11 / Hospital Finder: Hospital Data Integration, Search & Network Snapping.
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
import folium
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
    current_page="pages/11_Hospital_Validation.py"
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

# 1. Hospital Search & Direct Routing Section (Task 8)
st.markdown("### 🔍 Search & Select Receiving Emergency Hospital")
st.caption("Search across 1,084 facilities by name or locality. Inspect verified triage credentials, road snapping distance, and dispatch an ambulance directly to this hospital.")

c_find1, c_find2 = st.columns([1.5, 1])

with c_find1:
    search_q = st.text_input("Enter Hospital Name or Area (e.g. Victoria, Bowring, Manipal, Apollo, St. John's):", "Victoria Hospital")
    
    # Filter matches
    if search_q.strip():
        m_df = df_hospitals[df_hospitals["hospital_name"].str.contains(search_q.strip(), case=False, na=False)]
    else:
        m_df = df_hospitals.head(20)

    if not m_df.empty:
        hosp_options = list(m_df["hospital_id"].values)
        def _format_hosp_label(r):
            a = r.get("address")
            a_str = str(a).strip() if pd.notna(a) and str(a).strip() else "Bengaluru"
            return f"{r['hospital_name']} ({r['verification_status']}) — {a_str[:35]}"

        hosp_display = {
            row["hospital_id"]: _format_hosp_label(row)
            for _, row in m_df.iterrows()
        }
        chosen_hid = st.selectbox(
            f"Select Matched Facility ({len(m_df)} matches found):",
            hosp_options,
            format_func=lambda x: hosp_display.get(x, x)
        )
    else:
        st.warning(f"No hospital found matching '{search_q}'. Showing first 10 verified trauma centers.")
        m_df = df_hospitals[df_hospitals["verification_status"] == "VERIFIED_EMERGENCY"].head(10)
        hosp_options = list(m_df["hospital_id"].values)
        chosen_hid = hosp_options[0]

    # Retrieve full record
    sel_h = df_hospitals[df_hospitals["hospital_id"] == chosen_hid].iloc[0].to_dict()
    sel_c = None
    if not df_connections.empty:
        c_match = df_connections[df_connections["hospital_id"] == chosen_hid]
        if not c_match.empty:
            sel_c = c_match.iloc[0].to_dict()

with c_find2:
    st.markdown("#### 🏥 Facility Profile Card")
    v_stat = sel_h.get("verification_status", "HOSPITAL_EMERGENCY_UNVERIFIED")
    v_color = "#10B981" if v_stat == "VERIFIED_EMERGENCY" else ("#3B82F6" if "PROBABLE" in v_stat else "#F59E0B")
    
    snap_dist = sel_c.get("snapping_distance_m", 0.0) if sel_c else 0.0
    snap_road = sel_c.get("nearest_road_name", "Arterial Road") if sel_c else "N/A"
    snap_node = sel_c.get("nearest_intersection_name", "Junction") if sel_c else "N/A"
    driveway_delay = sel_c.get("estimated_access_time_min", 1.0) if sel_c else 1.0
    is_unmatched = sel_c.get("exceeds_threshold", False) if sel_c else False

    addr_val = sel_h.get("address")
    addr_disp = str(addr_val).strip() if pd.notna(addr_val) and str(addr_val).strip() else "Bengaluru, Karnataka"

    st.markdown(f"""
    <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255, 255, 255, 0.1); border-left: 4px solid {v_color}; border-radius: 8px; padding: 12px;">
        <div style="font-weight: 700; font-size: 14px; color: #F8FAFC;">{sel_h.get('hospital_name')}</div>
        <div style="margin: 4px 0;">
            <span style="background: {v_color}; color: #FFFFFF; font-size: 9.5px; font-weight: 700; padding: 2px 6px; border-radius: 4px;">{v_stat}</span>
            <span style="font-size: 11px; color: #94A3B8; margin-left: 6px;">OSM ID: <code>{sel_h.get('osm_id', 'N/A')}</code></span>
        </div>
        <div style="font-size: 11.5px; color: #CBD5E1; margin-top: 6px;"><b>Address:</b> {addr_disp}</div>
        <div style="font-size: 11.5px; color: #CBD5E1;"><b>Coordinates:</b> {sel_h.get('latitude', 0):.4f}°N, {sel_h.get('longitude', 0):.4f}°E</div>
        <hr style="border: 0; border-top: 1px solid rgba(255,255,255,0.08); margin: 8px 0;"/>
        <div style="font-size: 11px; color: #38BDF8;">🔗 <b>Nearest Road Link:</b> {snap_road}</div>
        <div style="font-size: 11px; color: #94A3B8;">🚦 <b>Nearest Junction:</b> {snap_node}</div>
        <div style="font-size: 11px; color: #94A3B8;">📏 <b>Snapping Distance:</b> {snap_dist:,.0f} m | ⏱️ <b>Driveway Penalty:</b> +{driveway_delay} min</div>
    </div>
    """, unsafe_allow_html=True)

    if not is_unmatched:
        if st.button("🚑 Open in Ambulance Route Optimizer", type="primary", width="stretch"):
            st.session_state["target_hospital_id"] = chosen_hid
            st.switch_page("pages/6_Shortest_Path.py")
    else:
        st.warning("⚠️ This facility exceeds the 2km arterial snapping threshold and cannot be directly routed.")

st.markdown("---")

# 2. Interactive Map & Deep Validation Tabs
tab_map, tab_matched, tab_unmatched, tab_quality = st.tabs([
    "🗺️ Interactive GIS Hospital Map",
    "📋 Snapped Hospital Directory (750 Matched)",
    "⚠️ Unmatched Facilities (334 Peripheral)",
    "📊 Data Quality & Provenance Audit"
])

with tab_map:
    st.markdown("#### Spatial Validation View: Hospitals & Road Network Connectors")
    st.caption("Green markers denote verified emergency trauma centers, blue markers indicate tertiary referral hospitals, amber markers denote general clinics, and dashed lines trace driveway entry connectors.")
    
    c_m1, c_m2 = st.columns([1, 1])
    status_filter = c_m1.multiselect(
        "Filter Hospital Statuses on Map:",
        options=[
            "VERIFIED_EMERGENCY",
            "EMERGENCY_PROBABLE_UNVERIFIED",
            "HOSPITAL_EMERGENCY_UNVERIFIED",
            "GENERAL_HEALTHCARE",
            "DUPLICATE_ENTRY"
        ],
        default=["VERIFIED_EMERGENCY", "EMERGENCY_PROBABLE_UNVERIFIED"]
    )
    max_hosp_count = c_m2.slider("Maximum Facilities to Render:", 50, 1084, 300, 50)

    map_obj = create_hospital_validation_map(
        df_hospitals=df_hospitals,
        df_connections=df_connections,
        intersections=intersections_list,
        roads=roads_gis,
        show_connectors=True,
        status_filter=status_filter,
        max_hospitals=max_hosp_count
    )
    render_gis_map_in_streamlit(map_obj, height=620, key="hospital_map_view")

with tab_matched:
    st.markdown("#### Matched Healthcare Facilities (Directly Accessible from 226 Arterial Junctions)")
    st.caption("Facilities within the 2,000-meter threshold with computed campus access delay (15 km/h driveway penalty + 1.0 min gate delay).")
    
    df_matched_table = df_connections[~df_connections["exceeds_threshold"]].copy()
    if "address" not in df_matched_table.columns and "hospital_id" in df_matched_table.columns and not df_hospitals.empty:
        df_matched_table = df_matched_table.merge(
            df_hospitals[["hospital_id", "address"]].drop_duplicates(subset=["hospital_id"]),
            on="hospital_id",
            how="left"
        )
        df_matched_table["address"] = df_matched_table["address"].fillna("Bengaluru, Karnataka")

    display_cols = [
        c for c in [
            "hospital_id", "hospital_name", "emergency_status",
            "nearest_road_name", "nearest_intersection_name",
            "snapping_distance_m", "estimated_access_time_min",
            "connection_status", "address"
        ] if c in df_matched_table.columns
    ]
    st.dataframe(
        df_matched_table[display_cols].sort_values(by="snapping_distance_m"),
        width="stretch",
        hide_index=True
    )

with tab_unmatched:
    st.markdown("#### Unmatched & Peripheral Facilities (Requiring Secondary Street Network)")
    st.caption("Facilities tagged as unmatchable are either in peripheral suburban zones (Whitefield, Kengeri, Hoskote, Electronic City) or lack proximate arterial intersections in the 226-junction BEL model.")
    
    df_unmatched_table = df_connections[df_connections["exceeds_threshold"]].copy()
    unmatched_cols = [
        c for c in [
            "hospital_id", "hospital_name", "emergency_status",
            "nearest_intersection_name", "snapping_distance_m", "connection_status"
        ] if c in df_unmatched_table.columns
    ]
    st.dataframe(
        df_unmatched_table[unmatched_cols].sort_values(by="snapping_distance_m", ascending=False),
        width="stretch",
        hide_index=True
    )

with tab_quality:
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
    prev_page="pages/3_Network_Visualization.py",
    prev_label="02. Road Network Explorer",
    next_page="pages/9_Analytics.py",
    next_label="04. Performance Analytics"
)
