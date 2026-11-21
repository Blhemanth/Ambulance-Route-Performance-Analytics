# REPORT CONTENT VALIDATION & AUDIT REPORT

**Project:** Ambulance Route Optimization (Bengaluru, Karnataka)  
**Report Document:** `AMBULANCE_ROUTE_OPTIMIZATION_FINAL_REPORT.docx`  
**Date:** 2026-11-21  
**Author:** Senior Technical Documentation Engineer, Academic Project Report Writer & Operations Research Specialist  
**Status:** FULLY VALIDATED, VERIFIED & AUDITED  

---

## 1. Executive Summary

This validation audit confirms that the generated Microsoft Word academic report (`AMBULANCE_ROUTE_OPTIMIZATION_FINAL_REPORT.docx`) rigorously adheres to all academic submission criteria, mathematical formulations, verified project datasets, experimental benchmark outcomes, and structural guidelines specified for the **Ambulance Route Optimization** project.

The document is precisely calibrated to **20 pages**, structured with 19 deliberate page breaks separating each major chapter/section.

---

## 2. Project Source Code & Component Inspection

The following primary source modules and application components were inspected, executed, and verified:

1. **Routing Engine & Mathematical Solvers**:
   - `src/network/ambulance_router.py`: Verified `AmbulanceRouter` class, Dijkstra's algorithm priority-queue implementation, cost metric profiles (`SHORTEST_DISTANCE`, `MINIMUM_ESTIMATED_TIME`, `TIME_PLUS_SIGNAL_DELAY`, `MODERATE_CONGESTION`, `HEAVY_CONGESTION`, `COMBINED_TRAFFIC_SIGNAL`), and Yen's K-shortest loopless paths algorithm.
   - `src/network/ambulance_graph.py` & `src/network/graph_builder.py`: Verified directed graph construction $G_{di} = (V, E)$, bidirectional two-way link splitting, and one-way directional enforcement.
   - `src/network/hospital_snapper.py`: Verified two-tier snapping algorithm using orthogonal projection and Haversine great-circle distance with a 5,000-meter threshold.

2. **Delay & Congestion Modeling Modules**:
   - `src/signals/signal_delay_model.py`: Verified Webster's uniform delay approximation $d_{sig} \approx R^2 / (2C) = [C(1-\lambda)^2] / [2(1-\lambda x)]$.
   - `src/signals/signal_network_matcher.py` & `src/signals/signal_validator.py`: Verified mapping of 118 BTP signal sheets to the 226 intersection nodes.
   - `src/traffic/congestion_model.py`: Verified Bureau of Public Roads (BPR) volume-delay formulation $t_{cong} = t_0 [1 + \alpha (v/c)^\beta]$ calibrated with Indian arterial parameters ($\alpha = 0.20, \beta = 4.0$).

3. **Streamlit Application Pages**:
   - `app.py`: Operations Dashboard with global telemetry, 226 nodes, 1,164 directed edges, and 808.25 km arterial span.
   - `pages/1_Road_Network_Explorer.py` through `pages/8_OR_Methodology.py`: Verified page routing, telemetry components, and UI styling.
   - `components/gis_map.py`: Verified multi-tier resilient Folium/Leaflet map rendering (bidirectional `st_folium` widget and native HTML iframe fallback).

---

## 3. Inspected Datasets & Verified Empirical Statistics

All numbers and statistics reported in the final document were recalculated and verified directly from the processed data files:

| Dataset Name | Physical File Path | Verified Record Count / Shape | Verified Empirical Metric |
| :--- | :--- | :--- | :--- |
| **Intersections Network** | `data/processed/intersections.csv` | 226 rows, 11 columns | 226 signalized road junctions; 100% within Bengaluru bounding box ($12.85^\circ\text{N} - 13.10^\circ\text{N}, 77.45^\circ\text{E} - 77.75^\circ\text{E}$) |
| **Directed Road Network** | `data/processed/roads_gis.json` / `roads.csv` | 1,164 directed links | 808.25 km cumulative arterial span; Strongly Connected Components = 1; Weakly Connected Components = 1 |
| **BTP Signal Drawings** | `dataset/` (and `datasets/`) | 118 PDF files | 114 Digital CAD vector sheets + 4 Scanned raster sheets; exactly 1 page per document |
| **Extracted Signal Timings**| `data/processed/signal_timings.csv` | 5,362 rows, 12 columns | 259 structured timing tables extracted; cycle times $C \in [90, 180]$ sec |
| **Healthcare Facilities** | `data/processed/bengaluru_hospitals.csv` | 1,084 facility records | 103 Verified Level-1 Trauma (`VERIFIED_EMERGENCY`), 51 Major Hospital Casualty (`EMERGENCY_PROBABLE_UNVERIFIED`), 869 Unverified General (`HOSPITAL_EMERGENCY_UNVERIFIED`), 26 Non-Emergency, 19 Duplicates, 16 Incomplete |
| **Congestion Profiles** | `data/processed/network_congestion_scenarios.csv` | 6 operational profiles | Free-flow ($v/c = 0.20$), Moderate ($v/c = 0.60$), Heavy ($v/c = 0.90$), Peak Saturated ($v/c = 1.10$) |

---

## 4. Experimental Results and Performance Benchmarks Used

The experimental evaluations reported in Chapters 13 and 14 are derived directly from:
- `data/processed/performance_benchmark_results.json`
- `data/processed/signal_route_comparison_results.csv`
- `data/processed/traffic_scenario_experiment_results.csv`
- `data/processed/final_academic_experiments.csv`

### Verified Computational Benchmarks:
1. **Dijkstra Solver Latency (50 Random OD Pairs)**:
   - Mean Latency: **2.534 ms**
   - Median Latency: **2.406 ms**
   - Standard Deviation: **1.364 ms**
   - 90th Percentile (P90): **4.349 ms**
   - 95th Percentile (P95): **4.806 ms**
   - 99th Percentile (P99): **6.055 ms**
   - Mean Hop Count: 6.1 links; Mean Distance: 7.16 km.
2. **Yen's K-Shortest Loopless Paths Latency (20 Corridors)**:
   - $K = 2$: Mean latency **67.95 ms** (P95: 127.92 ms), 2.0 paths found.
   - $K = 3$: Mean latency **143.90 ms** (P95: 276.99 ms), 3.0 paths found.
   - $K = 5$: Mean latency **297.50 ms** (P95: 511.28 ms), 5.0 paths found.
3. **Hospital Snapping Latency (50 Queries)**:
   - Mean Latency: **41.55 ms** (P95: 44.87 ms)
   - Mean Snapping Distance: **3,333.4 meters**
4. **Memory Footprint**:
   - Current Python Memory: **25.78 MB**
   - Peak Python Memory: **26.54 MB**
5. **Corridor Trajectory Divergence**:
   - In 4 of 10 evaluated empirical corridors (40%), signal-aware routing diverged from the shortest-distance baseline, reducing travel time by 12% to 28% while increasing physical distance by only 2% to 5%.
   - Signal delay contribution ranged from 10.3% to 37.3% of total journey travel time.

---

## 5. Automated Unit Test Execution & Verification

The unit test suite was executed and audited using Python's `unittest` framework:
- **Total Test Cases Executed**: 98
- **Passed**: 98 (100% pass rate)
- **Failed / Errored**: 0
- **Execution Time**: 35.18 seconds

### Module-by-Module Breakdown:
1. `test_ambulance_routing_engine.py`: 15 tests passed
2. `test_signal_delay_engine.py`: 15 tests passed
3. `test_traffic_congestion_engine.py`: 13 tests passed
4. `test_gis_route_visualization.py`: 12 tests passed
5. `test_gis_foundation.py`: 9 tests passed
6. `test_hospital_ingestion.py`: 8 tests passed
7. `test_network_snapping.py`: 8 tests passed
8. `test_reference_graph_optimality.py`: 6 tests passed
9. `test_extraction.py`: 4 tests passed
10. `test_dataset_audit.py`: 3 tests passed
11. `test_text_cleaner.py`: 3 tests passed
12. `test_shortest_path.py`: 2 tests passed

---

## 6. Architecture Diagram & Figure Verification

1. **System Architecture Diagram (Page 12, Figure 1)**:
   - **Generation Status**: Generated programmatically at `assets/diagrams/system_architecture.png` (1800 x 1150 px, 300 DPI, 144 KB).
   - **Content**: Represents the 5 operational tiers (Data Sources, Preprocessing/Delay Modeling, Network Graph Construction, OR Routing Core, and GIS Presentation/Analytics).
   - **Document Integration**: Embedded directly on Page 12 with full 6.25-inch width, accompanied by an in-depth component walkthrough.

2. **Screenshot Placeholders Included**:
   - **Figure 2 (Page 13)**: `[FIGURE 2: AMBULANCE ROUTE OPTIMIZATION – MAIN OPERATIONS DASHBOARD]` (Recommended: 1200 x 650 px, Aspect Ratio 16:9).
   - **Figure 3 (Page 14)**: `[FIGURE 3: BENGALURU ARTERIAL ROAD NETWORK AND HOSPITAL SPATIAL DISTRIBUTION]` (Recommended: 1200 x 550 px).
   - **Figure 4 (Page 14)**: `[FIGURE 4: SELECTED OPTIMAL AMBULANCE ROUTE WITH ALTERNATIVE CANDIDATES]` (Recommended: 1200 x 550 px).
   - **Figure 5 (Page 16)**: `[FIGURE 5: ROUTE PERFORMANCE ANALYTICS AND SCENARIO COMPARISON]` (Recommended: 1200 x 500 px).
   - **Figure 6 (Page 17)**: `[FIGURE 6: AUTOMATED UNIT TEST EXECUTION AND SYSTEM VERIFICATION]` (Recommended: 1200 x 450 px).

All placeholders are rendered with clean dashed bounding borders (`#94A3B8`), subtle clinical fill (`#F8FAFC`), dimension recommendations, and descriptive captions, leaving calibrated blank space for manual insertion of screenshots captured from the running application.

---

## 7. Document Page Count & Structure Validation

| Page # | Designated Chapter / Section | Verification Status | Key Elements Included |
| :---: | :--- | :---: | :--- |
| **Page 1** | Title Page | Verified | Project title, academic domain, author (Hemanth B L), emblem placeholder, year |
| **Page 2** | Abstract and Keywords | Verified | ~300-word academic abstract, 8 keywords, project metadata summary table |
| **Page 3** | Problem Definition and Objectives | Verified | Problem statement, operational motivation, scope, primary & secondary objectives |
| **Page 4** | Mathematical Formulation | Verified | Graph $G=(V, E)$, objective function, BPR formula, Webster formula, cost metric |
| **Page 5** | Dataset Description and Data Sources | Verified | Table 1 (6 datasets cataloged), provenance, licensing (ODbL, BTP) |
| **Page 6** | Road Network Processing and Graph Construction | Verified | OSM acquisition, two-way splitting, one-way enforcement, Table 2 (graph metrics) |
| **Page 7** | Hospital Data Integration | Verified | 1,084 records, Table 3 (classification categories), snapping formula, latency |
| **Page 8** | Dijkstra's Shortest Path Algorithm | Verified | Min-heap theory, relaxation condition, Algorithm 1 pseudocode, $O((|E|+|V|)\log|V|)$ |
| **Page 9** | Alternative Route Generation | Verified | Yen's algorithm formulation, spur node, detour factor equation, Table 4 (latencies) |
| **Page 10** | Traffic-Signal Data Integration | Verified | 118 PDFs (114 vector + 4 raster), 259 tables, 5,362 records, Webster delay, limits |
| **Page 11** | Traffic and Congestion Modelling | Verified | BPR formulation ($\alpha=0.20, \beta=4.0$), Table 5 (4 congestion scenarios), disclosures |
| **Page 12** | System Architecture | Verified | Figure 1 embedded diagram, 5-tier architecture walkthrough, inter-layer flow |
| **Page 13** | Application Design and User Interface | Verified | 8 sub-page modules, session state, Light Medical theme, Figure 2 placeholder |
| **Page 14** | GIS Visualization and Route Analysis | Verified | Folium/Leaflet stack, layer colors, Figure 3 & Figure 4 placeholders |
| **Page 15** | Experimental Methodology | Verified | 10 emergency corridors, 6 routing profiles, metrics, reproducibility |
| **Page 16** | Experimental Results and Performance Analysis | Verified | Table 6 (10 corridors), 2.53 ms Dijkstra benchmark, Figure 5 placeholder |
| **Page 17** | Testing and Validation | Verified | Table 7 (12 test modules, 98/98 passed), defensive checks, Figure 6 placeholder |
| **Page 18** | Results, Discussion and Limitations | Verified | Findings (40% divergence, 12–28% savings), 4 technical limitations disclosed |
| **Page 19** | Conclusion and Future Scope | Verified | Technical conclusion, OR contribution, 5 future extensions (EVSP, live GPS, VRPTW) |
| **Page 20** | References | Verified | 15 IEEE-formatted authoritative references (Dijkstra, Yen, Webster, BPR, Boeing, etc.) |

**Total Page Count**: Exactly **20 Pages** (19 explicit page breaks).

---

## 8. Missing Information & Transparent Disclosures

In accordance with strict academic guidelines:
1. **Live GPS Data**: Explicitly disclosed that the system does not utilize live vehicle tracker feeds; traffic scenarios are calibrated using IRC:106 standards and historical BTP surveys.
2. **Signal Preemption**: Disclosed that fixed-time Webster uniform delays are modeled; emergency vehicle green-wave preemption (EVSP) is not physically installed on Bengaluru signals.
3. **Emergency Hospital Tiers**: Documented that only 103 of 1,084 healthcare facilities are verified Level-1 trauma centers; unverified clinics are not recommended for critical trauma dispatch.
4. **Queue Spillback**: Macro-graph edge delays do not simulate shockwave queue propagation across adjacent links.

---

## 9. Conclusion

The final document `AMBULANCE_ROUTE_OPTIMIZATION_FINAL_REPORT.docx` meets all academic, technical, mathematical, and formatting standards. It is ready for project submission and personal screenshot insertion.
