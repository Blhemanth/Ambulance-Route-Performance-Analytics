"""
Traffic Signal Delay Analysis Page.
Phase 4 — Task 10: Dedicated Signal Timing & Delay Analysis Dashboard.

Features:
- Browse extracted junction signal records across all 118 PDFs (226 junctions, 5,362 timing records).
- Search and filter by junction, corridor, and time-of-day plan.
- View signal phases, approach allocations, green duration, red duration, and stated cycle length.
- View source PDF filename, page number, and extraction provenance.
- Inspect road-network matching verification status and incoming edge links.
- Review mathematical Webster delay calculations: d = R^2 / (2C).
- Audit data quality flags and unverified records (Task 4 checks).
"""

import os
import math
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.ui_helpers import (
    load_custom_css,
    render_header,
    render_metric,
    render_workflow_navigation,
    get_plotly_layout
)
from src.signals.signal_delay_model import calculate_webster_uniform_delay, SUPPORTED_TOD_PLANS

st.set_page_config(
    page_title="Signal Delay Analysis | Bengaluru GIS",
    page_icon="🚦",
    layout="wide"
)
load_custom_css()

render_header(
    title="Traffic Signal Delay Analysis",
    subtitle="Bengaluru Traffic Police Signal Timing PDF Integration, Webster Delay Modeling & Road-Network Matching",
    badge_text="Phase 4 — Operations Research",
    current_page="pages/12_Signal_Delay_Analysis.py"
)

# 1. Load Data
@st.cache_data
def load_signal_datasets():
    df_int = pd.read_csv("data/processed/intersections_gis.csv") if os.path.exists("data/processed/intersections_gis.csv") else pd.DataFrame()
    df_tim = pd.read_csv("data/processed/signal_timings.csv") if os.path.exists("data/processed/signal_timings.csv") else pd.DataFrame()
    df_pha = pd.read_csv("data/processed/signal_phases.csv") if os.path.exists("data/processed/signal_phases.csv") else pd.DataFrame()
    df_inv = pd.read_csv("data/processed/pdf_inventory.csv") if os.path.exists("data/processed/pdf_inventory.csv") else pd.DataFrame()
    df_map = pd.read_csv("data/processed/signal_network_mapping.csv") if os.path.exists("data/processed/signal_network_mapping.csv") else pd.DataFrame()
    df_aud = pd.read_csv("data/processed/signal_validation_audit.csv") if os.path.exists("data/processed/signal_validation_audit.csv") else pd.DataFrame()
    df_del = pd.read_csv("data/processed/edge_signal_delays.csv") if os.path.exists("data/processed/edge_signal_delays.csv") else pd.DataFrame()
    return df_int, df_tim, df_pha, df_inv, df_map, df_aud, df_del

df_int, df_tim, df_pha, df_inv, df_map, df_aud, df_del = load_signal_datasets()

# Academic Mathematical Formulation Expander
with st.expander("📐 Webster's Signal Delay Formulation & Fixed-Time Approximations", expanded=False):
    st.latex(r"""
    d_{\text{signal}} = \frac{R^2}{2C} = \frac{(C - G)^2}{2C}
    """)
    st.markdown(r"""
    **Delay Formulation & Academic Assumptions:**
    - **$C$:** Stated cycle length (seconds) from Bharat Electronics Limited (BEL) CAD signal plans.
    - **$G$:** Effective green interval allocated to the specific movement phase (seconds).
    - **$R = C - G$:** Red duration during which approaching vehicles incur delay (seconds).
    - **Uniform Arrival Regime:** Vehicles arrive at a uniform rate over the signal cycle ($v/c < 1.0$).
    - **Queue & Preemption Limitations:** The static engineering drawings record scheduled signal cycles.
      They do **not** reflect real-time adaptive queue detector counts or emergency vehicle siren preemption.
    - **Dijkstra Weight Non-Negativity:** For all valid schedules where $0 \le G \le C$, $0 \le d_{\text{signal}} \le \frac{C}{2}$,
      strictly preserving finite and non-negative routing edge weights.
    """)

# Summary Metrics Row
c1, c2, c3, c4, c5, c6 = st.columns(6)
render_metric(c1, "Signal Timing PDFs", f"{len(df_inv)} Documents", "114 Text + 4 Scanned", "normal")
render_metric(c2, "Signalized Junctions", f"{len(df_int)} Junctions", "226 GIS Nodes", "green")
render_metric(c3, "Extracted Timing Records", f"{len(df_tim):,} Records", "All TOD Intervals", "normal")
render_metric(c4, "Network Edges Mapped", f"{len(df_map):,} Edges", "100% Directional Links", "green")
render_metric(c5, "Average Signal Delay", f"{df_del['signal_delay_sec'].mean():.1f} sec", f"{df_del['signal_delay_sec'].mean()/60:.2f} min (Morning Peak)", "amber")
render_metric(c6, "Validation Audit Flags", f"{len(df_aud)} Issues", f"{len(df_aud[df_aud['severity']=='ERROR'])} Errors cataloged", "amber")

st.markdown("---")

# Main Navigation Tabs
tab_browser, tab_inventory, tab_audit, tab_analytics = st.tabs([
    "🔍 Junction Signal Browser",
    "📄 PDF Data Inventory (118 Docs)",
    "⚠️ Data Validation Audit (10 Checks)",
    "📈 Delay Distribution Analytics"
])

# TAB 1: JUNCTION SIGNAL BROWSER
with tab_browser:
    st.markdown("#### Interactive Junction Signal Timing Explorer")
    st.caption("Inspect approach allocations, signal phases, cycle lengths, and Webster delay for any intersection.")

    col_s1, col_s2, col_s3 = st.columns([2, 1.2, 1])

    with col_s1:
        junction_options = {
            r["intersection_id"]: f"{r['name']} ({r['intersection_id']})"
            for _, r in df_int.iterrows()
        }
        selected_iid = st.selectbox(
            "Select Signalized Intersection:",
            options=list(junction_options.keys()),
            format_func=lambda x: junction_options.get(x, x)
        )

    with col_s2:
        selected_plan = st.selectbox(
            "Filter Time-of-Day Plan:",
            SUPPORTED_TOD_PLANS,
            index=0
        )

    with col_s3:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        show_all_plans = st.checkbox("Show All Daily Plans", value=False)

    if selected_iid:
        int_row = df_int[df_int["intersection_id"] == selected_iid].iloc[0]
        
        # Details Card
        st.markdown(f"""
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 14px 18px; margin: 10px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <b style="font-size: 15px; color: #0284C7;">🚦 {int_row['name']}</b>
                <span style="background: #E0F2FE; color: #0369A1; font-weight: 700; font-size: 11px; padding: 3px 8px; border-radius: 4px;">
                    {int_row.get('verification_status', 'VERIFIED')}
                </span>
            </div>
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; font-size: 12px; color: #334155;">
                <div><b>Intersection ID:</b> <code>{selected_iid}</code></div>
                <div><b>Police Jurisdiction:</b> {int_row.get('police_station', 'Bengaluru Police')}</div>
                <div><b>Corridor:</b> {int_row.get('corridor', 'Arterial Corridor')}</div>
                <div><b>Source Document:</b> <code>{int_row.get('source_pdf', 'N/A')}</code> (p. {int_row.get('page_number', 1)})</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_j1, col_j2 = st.columns([1.3, 1])

        with col_j1:
            st.markdown("##### ⏱️ Signal Phase Timings & Webster Delay")
            
            # Filter timings for this junction
            jt = df_tim[df_tim["intersection_id"] == selected_iid].copy()
            if not show_all_plans:
                jt = jt[jt["plan_name"] == selected_plan]

            if not jt.empty:
                # Add Webster Delay column
                delays = []
                reds = []
                for _, r in jt.iterrows():
                    c = r["cycle_length_sec"]
                    g = r["green_time_sec"]
                    d_s, _ = calculate_webster_uniform_delay(c, g)
                    reds.append(max(0.0, c - g))
                    delays.append(d_s)

                jt["red_time_sec"] = reds
                jt["webster_delay_sec"] = delays
                jt["webster_delay_min"] = [round(d / 60.0, 2) for d in delays]

                display_t_cols = [
                    "plan_name", "start_time", "end_time", "phase_number",
                    "green_time_sec", "red_time_sec", "cycle_length_sec",
                    "webster_delay_sec", "webster_delay_min", "validation_status"
                ]
                st.dataframe(
                    jt[[c for c in display_t_cols if c in jt.columns]],
                    width="stretch",
                    hide_index=True
                )
            else:
                st.info(f"No timing records found for plan '{selected_plan}'. Try selecting 'Show All Daily Plans'.")

        with col_j2:
            st.markdown("##### 🛣️ Incoming Road Approaches & Mapped Network Edges")
            jm = df_map[df_map["gis_junction_id"] == selected_iid]
            if not jm.empty:
                m_cols = [
                    "road_edge_id", "from_node", "approach_code",
                    "approach_road_name", "signal_phase_number",
                    "matching_method", "verification_status"
                ]
                st.dataframe(
                    jm[[c for c in m_cols if c in jm.columns]],
                    width="stretch",
                    hide_index=True
                )
            else:
                st.info("No mapped directed edges found entering this junction.")

# TAB 2: PDF DATA INVENTORY (Task 2)
with tab_inventory:
    st.markdown("#### Complete 118 Traffic Signal PDF Inventory")
    st.caption("Comprehensive catalog of every original engineering drawing from Bharat Electronics Limited (BEL).")

    ci1, ci2, ci3 = st.columns(3)
    with ci1:
        inv_cat = st.multiselect("Filter by PDF Category:", options=df_inv["pdf_category"].unique(), default=df_inv["pdf_category"].unique())
    with ci2:
        inv_status = st.multiselect("Filter by Extraction Status:", options=df_inv["extraction_status"].unique(), default=df_inv["extraction_status"].unique())
    with ci3:
        search_pdf = st.text_input("Search Filename or Junction:", "")

    df_inv_f = df_inv[
        (df_inv["pdf_category"].isin(inv_cat)) &
        (df_inv["extraction_status"].isin(inv_status))
    ]
    if search_pdf:
        df_inv_f = df_inv_f[
            df_inv_f["filename"].str.contains(search_pdf, case=False, na=False) |
            df_inv_f["junction_names"].str.contains(search_pdf, case=False, na=False)
        ]

    st.dataframe(df_inv_f, width="stretch", hide_index=True)
    st.caption(f"Showing {len(df_inv_f)} of {len(df_inv)} documents.")

# TAB 3: DATA VALIDATION AUDIT (Task 4)
with tab_audit:
    st.markdown("#### Comprehensive 10-Check Signal Data Validation Audit")
    st.caption("Preserves original source values while cataloging discrepancies for academic transparency.")

    ca1, ca2 = st.columns([1, 1])
    with ca1:
        check_filter = st.multiselect(
            "Filter by Validation Check:",
            options=sorted(df_aud["check_name"].unique()),
            default=sorted(df_aud["check_name"].unique())
        )
    with ca2:
        severity_filter = st.multiselect(
            "Filter by Severity:",
            options=["ERROR", "WARNING", "INFO"],
            default=["ERROR", "WARNING"]
        )

    df_aud_f = df_aud[
        (df_aud["check_name"].isin(check_filter)) &
        (df_aud["severity"].isin(severity_filter))
    ]

    st.dataframe(df_aud_f, width="stretch", hide_index=True)
    st.caption(f"Showing {len(df_aud_f)} of {len(df_aud)} flagged audit findings.")

# TAB 4: DELAY DISTRIBUTION ANALYTICS
with tab_analytics:
    st.markdown("#### Signal Delay & Cycle Length Distribution Analytics")
    st.caption("Empirical distributions across all 1,164 network edges under morning peak operations.")

    col_a1, col_a2 = st.columns(2)

    with col_a1:
        if not df_del.empty:
            valid_delays = df_del[df_del["is_signal_available"]]
            fig_hist = px.histogram(
                valid_delays,
                x="signal_delay_sec",
                nbins=25,
                title="Webster Uniform Delay Distribution (Seconds)",
                color_discrete_sequence=["#06B6D4"]
            )
            fig_hist.update_layout(get_plotly_layout("Signal Delay Histogram", height=320))
            fig_hist.update_xaxes(title="Estimated Signal Delay (Seconds)")
            fig_hist.update_yaxes(title="Network Links Count")
            st.plotly_chart(fig_hist, width="stretch")

    with col_a2:
        if not df_del.empty:
            fig_scatter = px.scatter(
                df_del[df_del["is_signal_available"]],
                x="cycle_sec",
                y="signal_delay_sec",
                color="approach_code",
                title="Delay vs. Stated Cycle Length",
                hover_data=["intersection_id", "approach_code", "green_sec"]
            )
            fig_scatter.update_layout(get_plotly_layout("Cycle Length vs Delay", height=320))
            fig_scatter.update_xaxes(title="Cycle Length C (sec)")
            fig_scatter.update_yaxes(title="Webster Delay d (sec)")
            st.plotly_chart(fig_scatter, width="stretch")

# Page Navigation
render_workflow_navigation(
    prev_page="pages/6_Shortest_Path.py",
    prev_label="01. Ambulance Route Optimizer",
    next_page="pages/13_Traffic_Scenario_Analysis.py",
    next_label="03. Traffic Scenario Analysis"
)
