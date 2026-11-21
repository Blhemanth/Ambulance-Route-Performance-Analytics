# Bengaluru Traffic Data Inventory & Academic Provenance Audit

**Project:** Ambulance Route Optimization — Bengaluru, Karnataka, India  
**Phase:** Phase 5 — Bengaluru Traffic Data Integration, Congestion Modeling & Scenario Analysis  
**Output Dataset:** [`data/processed/bengaluru_traffic_data_inventory.csv`](file:///b:/Ambulance%20Route%20Optimization/data/processed/bengaluru_traffic_data_inventory.csv)  
**Date:** November 2026  

---

## 1. Executive Summary & Academic Integrity Statement

In adherence to strict academic standards, **no synthetic or imaginary GPS floating-car sensor feeds are represented as observed real-time telemetry**. During Phase 5, an exhaustive empirical data audit of public, municipal, and commercial traffic data portals for Bengaluru was conducted to identify verifiable traffic congestion metrics.

### Key Finding:
While open-government repositories (OpenCity.in, data.gov.in) provide municipal signal plans, road crash records, and bus timetables, **no publicly accessible, free continuous road-segment level GPS probe velocity stream exists for all 1,164 directed road links across Greater Bengaluru**. Consequently, empirical macroscopic benchmark speeds published in the **TomTom Traffic Index for Bengaluru (2023–2024)** combined with the **Comprehensive Traffic and Transportation Plan (CTTP) for Bengaluru** and **IRC:106-1990** standards were adopted to calibrate the macroscopic **Bureau of Public Roads (BPR) volume-delay formulation**.

---

## 2. Audited Traffic Data Sources Catalog

The table below summarizes the 6 candidate data sources audited during Phase 5:

| Dataset ID | Dataset Name | Hosting Entity | Data Modality | Spatial & Temporal Resolution | Provenance & Suitability |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **DS_001_BTP_SIGNAL_PLANS** | Bengaluru Traffic Police Signal Timing Plans | BTP / BEL / OpenCity | PDF Engineering Drawings (118 files) | 226 Junctions; Time-of-Day scheduled cycle splits | **ACTUAL_SIGNAL_TIMING_CAD_SPECIFICATION** — Successfully ingested in Phase 4 (226 junctions, 5,362 timing records). |
| **DS_002_OPENCITY_BUS_TIMINGS** | BMTC Bus Schedules & Route Timetables | BMTC / OpenCity | CSV / GTFS Static | Transit corridor stops; Scheduled headway intervals | **SCHEDULED_TRANSIT_TIMETABLE** — Reflects bus transit schedules; transit dwell times cannot be conflated with private/emergency vehicle speeds. |
| **DS_003_DATAGOVIN_ROAD_CRASHES** | Road Accidents and Severity in Bengaluru | Ministry of MoRTH / data.gov.in | Annual aggregate CSV reports | Police station jurisdictional circles; Annual totals | **HISTORICAL_SAFETY_STATISTICS** — Useful for hazard weighting; does not provide link-level dynamic vehicular speeds. |
| **DS_004_TOMTOM_TRAFFIC_INDEX** | TomTom Traffic Index — Bengaluru Urban Area | TomTom International BV | Empirical floating-car GPS speed benchmarks | Metropolitan urban core; Hourly peak vs off-peak speeds | **EMPIRICAL_CITY_BENCHMARK** — Ground truth calibration anchor: Peak rush-hour average 13.9 km/h (evening 13.2 km/h, morning 14.6 km/h); Off-peak free-flow 29.0 km/h; 74.4% congestion delay. |
| **DS_005_BMRDA_CTTP_SURVEYS** | Comprehensive Traffic and Transportation Plan (CTTP) | BMRDA / Directorate of Urban Land Transport (DULT) | Comprehensive transportation planning study | Peak volume-to-capacity (v/c) ratios by arterial corridor | **OFFICIAL_GOVERNMENT_SURVEY** — Provides validated v/c ranges: Outer Ring Road (1.1–1.3), Radial Arterials (0.9–1.2), City Core (1.0–1.2), Inter-peak (0.55–0.70). |
| **DS_006_OSM_HIGHWAY_ATTRIBUTES** | OpenStreetMap Road Centerlines & Functional Classes | OpenStreetMap Contributors | GIS Polylines & Tags | 1,164 directed edges; Functional road class & lanes | **ACTUAL_GIS_GEOMETRY** — Foundational geometry and road classifications ingested in Phase 0 & Phase 3. |

---

## 3. Ground Truth Empirical Benchmarks (TomTom & CTTP)

The empirical calibration anchors utilized in our congestion engine:
- **TomTom Rush-Hour Speed (Metropolitan Average):** $13.9\text{ km/h}$
- **TomTom Morning Peak Average:** $14.6\text{ km/h}$
- **TomTom Evening Peak Average:** $13.2\text{ km/h}$
- **TomTom Free-Flow Off-Peak Speed:** $29.0\text{ km/h}$
- **Average Extra Travel Time (Congestion Index):** $+74.4\%$ over free-flow
- **Corridor Volume-to-Capacity ($v/c$) Ratios:**
  - *Expressway / Radial Corridors:* Free-flow $v/c = 0.0$; Moderate $v/c = 0.55$; Heavy $v/c = 0.95$
  - *Major Arterials (e.g. Mysore Rd, Hosur Rd, ORR):* Free-flow $v/c = 0.0$; Moderate $v/c = 0.65$; Heavy $v/c = 1.15$
  - *Sub-Arterials (e.g. CMH Rd, Bannerghatta Rd):* Free-flow $v/c = 0.0$; Moderate $v/c = 0.70$; Heavy $v/c = 1.10$
  - *Collectors / Local Links:* Free-flow $v/c = 0.0$; Moderate $v/c = 0.60$; Heavy $v/c = 0.90$

---

## 4. Academic Provenance Classification Standard

Every edge attribute and routing result carries a transparent `provenance_level` tag:
1. `ACTUAL_MEASURED`: Directly extracted from municipal CAD signal plans (e.g. Phase 4 green and cycle times).
2. `EMPIRICAL_BENCHMARK`: City-wide floating car velocity measurements from TomTom and official CTTP mobility surveys.
3. `CALIBRATED_BPR_ESTIMATE`: Link-level travel time derived from the Bureau of Public Roads formula calibrated to TomTom benchmarks.
4. `ESTIMATED_GEOMETRY`: Road distances calculated using WGS-84 ellipsoidal geodesics and OSM centerlines.

**Strict Policy:** No synthetic data is conflated with observed ground telemetry.
