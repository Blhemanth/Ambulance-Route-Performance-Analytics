# FINAL ACADEMIC PROJECT SUMMARY: AMBULANCE ROUTE OPTIMIZATION

**Official Academic Project Title**: **AMBULANCE ROUTE OPTIMIZATION**  
**Geographical Scope**: Bengaluru Metropolitan Region, Karnataka, India  
**Assigned Operations Research Technique**: Shortest Path Optimization  
**Primary Optimization Objective**: Minimum Estimated Ambulance Travel Time  
**Primary Algorithm**: Dijkstra's Shortest Path Algorithm (Min-Heap Priority Queue)  
**Alternative Path Algorithm**: Yen's K-Shortest Loopless Paths ($K \in [1, 5]$)  
**Supporting Real-World Data**: 118 Bengaluru Traffic Police Signal Timing PDFs & 1,084 Cleaned Hospitals  
**Application Stack**: Python 3.13, Streamlit, NetworkX, GeoPandas, Folium/Leaflet  
**Final Completion Date**: November 2026  
**Status**: **100% Complete, Fully Validated, Ready for Academic Submission & User Handover**

---

## 1. PROJECT GENESIS & ACADEMIC ALIGNMENT

This project was originally initiated as a general-purpose traffic optimizer. In consultation with academic guidelines, the topic was formally refocused onto **Ambulance Route Optimization**—a high-stakes, life-critical domain within Operations Research.

### The Emergency Medical Imperative:
In acute medical emergencies (severe trauma, acute myocardial infarction, ischemic stroke), patient prognosis is governed by the **"Golden Hour"**. In Greater Bengaluru—renowned for severe arterial traffic bottlenecks and complex multi-phase signalized intersections—conventional GPS routing often directs ambulances into gridlocked arterial segments. 

This project solves that life-critical challenge by formulating and implementing a dedicated **travel-time shortest path optimization engine** that models both mid-block traffic congestion drag (BPR formula) and terminal intersection signal delay (Webster's formula calibrated from 118 official Bengaluru Traffic Police PDFs), steering emergency vehicles along the true lowest-delay corridors.

---

## 2. SUMMARY OF COMPLETED DEVELOPMENT PHASES

The project was executed through six rigorous development phases, strictly adhering to local development safety constraints:

### Phase 0: Codebase & Dataset Audit
- Audited the full workspace, existing traffic networks, and datasets.
- Re-aligned the codebase to focus exclusively on ambulance routing.
- Established strict provenance tracking: `ACTUAL`, `EXTERNAL`, `MEASURED`, `ESTIMATED`, and `SYNTHETIC`.

### Phase 1: Hospital Data Integration & Network Snapping
- Aggregated, verified, and cleaned 1,084 healthcare facilities across Greater Bengaluru.
- Built `HospitalRoadSnapper` with perpendicular segment projection and nearest-node spatial matching.
- Established emergency access delay penalties (gate check-in and slow-speed driveway traversal).

### Phase 2: Project Cleanup & Dijkstra Travel-Time Optimization Engine
- Developed `AmbulanceRouter` and `AmbulanceGraphBuilder` enforcing strict non-negative edge weights ($w_{ij} > 0$).
- Proved and implemented non-double-counting edge weight decomposition: $w_{ij} = t_0 + \Delta t_{\text{traffic}} + d_{\text{signal}}$.
- Integrated Yen's K-Shortest Loopless Paths algorithm ($K=1..5$) for incident diversion.

### Phase 3: Interactive GIS Ambulance Route Optimization Application
- Built modern, high-contrast dark-themed Streamlit user interface (`app.py` and modular pages).
- Integrated interactive Folium/Leaflet maps rendering actual curved street polylines, junction markers, and hospital snapping pins.
- Implemented real-time interactive origin/destination selection, hospital routing, and alternative path visualization.

### Phase 4: Bengaluru Traffic Signal PDF Integration & Delay Estimation
- Audited and extracted all 118 official Bengaluru Traffic Police signal timing PDFs (114 vector text + 4 OCR raster).
- Extracted 7,647 timing records across 226 junctions, mapping 1,164 directed edges.
- Integrated Webster's signal delay formula and green-wave preemption attenuation ($\gamma \in [0.20, 1.0]$).

### Phase 5: Bengaluru Traffic Data Integration, Congestion Modeling & Scenario Analysis
- Integrated empirical Bengaluru traffic datasets (including TomTom 2023 rush-hour benchmark of 13.9 km/h).
- Implemented Bureau of Public Roads (BPR) congestion model with IRC:106-1990 road capacities.
- Formulated 6 canonical routing scenarios (A through F) across 10 Greater Bengaluru emergency corridors.

### Phase 6: Final Application Validation, Experimental Evaluation & Academic Completion
- Re-architected application navigation to a clean, logical 9-item workflow (Dashboard + 8 dedicated pages).
- Authored and passed deterministic mathematical reference-graph tests (optimality, one-way enforcement, flow conservation, looplessness).
- Executed full 60-run experimental evaluation across 10 canonical corridors and 6 scenarios.
- Benchmarked system performance: 2.53 ms Dijkstra solve latency, 143.9 ms Yen's K solve latency, < 27 MB memory footprint.
- Ran full test suite: **98 of 98 unit tests passing (100% pass rate)**.
- Authored 5 comprehensive academic evaluation reports.

---

## 3. FINAL APPLICATION ARCHITECTURE (9-ITEM WORKFLOW)

The user-facing Streamlit application is structured into 9 dedicated modules matching the required operational lifecycle:

```
Ambulance Route Optimization Application
├── 🏛️ app.py                              (0. Operations Dashboard & System Status)
└── pages/
    ├── 🗺️ 1_Road_Network_Explorer.py      (1. Road Network Explorer & GIS Layer)
    ├── 🏥 2_Hospital_Finder.py             (2. Hospital Finder & Road Snapping)
    ├── 🚑 3_Ambulance_Route_Optimizer.py   (3. Ambulance Route Optimizer)
    ├── 🔀 4_Alternative_Route_Comparison.py(4. Alternative Route Comparison & Blockage Bypass)
    ├── 🚦 5_Signal_Delay_Analysis.py       (5. Traffic Signal Delay Analysis)
    ├── 📊 6_Traffic_Scenario_Analysis.py   (6. Traffic Scenario Analysis)
    ├── 📈 7_Route_Performance_Analytics.py (7. Route Performance Analytics & Corridors)
    └── 📐 8_OR_Methodology.py              (8. OR Methodology & Mathematical Formulation)
```

---

## 4. KEY EXPERIMENTAL & BENCHMARKING FINDINGS

### 4.1 6-Scenario Experimental Results (60 Runs)
- **Signal-Aware Bypass**: In **70% of evaluated corridors**, signal-aware routing diverged from the shortest-distance path, accepting an average of 30 to 170 meters of additional physical distance to bypass high-delay red signals, reducing signal delay from **5.46 min to 4.21 min (a 22.9% reduction)**.
- **Signal Delay Dominance**: At intermediate traffic levels, traffic signals account for **92.3% of all trip delay**. Even in heavy rush hours, signal delay represents over 57% of total trip drag.
- **Combined Optimization**: In the combined scenario (congestion + signals), optimal routing saves **3.3 to 4.5 minutes** per emergency run—a clinically critical margin for the Golden Hour.

### 4.2 System Performance & Responsiveness
- **Dijkstra Latency**: Mean **2.53 ms** ($p_{95} = 4.81\text{ ms}$, max $6.99\text{ ms}$).
- **Yen's K-Shortest Paths ($K=3$)**: Mean **143.9 ms** ($p_{95} = 276.9\text{ ms}$).
- **Nearest Hospital Snapping**: Mean **41.5 ms** across 1,084 facilities.
- **Memory Footprint**: Peak Python heap allocation of **26.54 MB**.
- **Cold-Start Load Time**: **140.7 ms** for all four core datasets.

---

## 5. COMPLETE ACADEMIC DOCUMENTATION CATALOG

The following comprehensive academic reports have been generated and saved directly in the project root:

1. **[`FINAL_PROJECT_AUDIT_REPORT.md`](file:///B:/Ambulance%20Route%20Optimization/FINAL_PROJECT_AUDIT_REPORT.md)**:  
   Full audit of datasets, models, code structure, and data provenance.
2. **[`MATHEMATICAL_MODEL_VALIDATION_REPORT.md`](file:///B:/Ambulance%20Route%20Optimization/MATHEMATICAL_MODEL_VALIDATION_REPORT.md)**:  
   Formal OR Integer Programming formulation, sub-path optimality proofs, non-double-counting proof, and reference-graph verification.
3. **[`TRAFFIC_SIGNAL_PDF_VALIDATION_REPORT.md`](file:///B:/Ambulance%20Route%20Optimization/TRAFFIC_SIGNAL_PDF_VALIDATION_REPORT.md)**:  
   Detailed audit of 118 BTP signal PDFs, 7,647 records, Webster delay formulation, and preemption factors.
4. **[`FINAL_EXPERIMENTAL_EVALUATION_REPORT.md`](file:///B:/Ambulance%20Route%20Optimization/FINAL_EXPERIMENTAL_EVALUATION_REPORT.md)**:  
   Complete breakdown of the 6-scenario benchmark across 10 corridors (60 runs), tabular comparisons, and clinical implications.
5. **[`SYSTEM_PERFORMANCE_EVALUATION_REPORT.md`](file:///B:/Ambulance%20Route%20Optimization/SYSTEM_PERFORMANCE_EVALUATION_REPORT.md)**:  
   Quantitative latency, throughput, and memory profiling results.
6. **[`PROJECT_DEVELOPMENT_LOG.md`](file:///B:/Ambulance%20Route%20Optimization/PROJECT_DEVELOPMENT_LOG.md)**:  
   Full chronological engineering log covering all phases from project inception to Phase 6 completion.

---

## 6. STRICT BOUNDARY COMPLIANCE & USER HANDOVER

In accordance with strict development rules:
- **No Git Commits Made**: The agent performed zero `git commit` commands.
- **No Remote Git Pushes**: No pushes or synchronization with remote repositories were initiated.
- **No Deployment / Publishing**: No third-party or cloud deployments were initiated.
- **Zero Data Loss**: All 118 original PDF schedules, OSM shapefiles, GeoJSON layers, and unit test suites were strictly preserved.

### User Handover Instructions:

1. **Run the Full Test Suite**:
   ```bash
   python -m unittest discover tests
   ```
   *(Expected output: Ran 98 tests in ~35s — OK)*

2. **Launch the Streamlit Application**:
   ```bash
   streamlit run app.py
   ```
   *(Access via browser at `http://localhost:8501`)*

3. **Re-run Experimental Evaluations & Benchmarks (Optional)**:
   ```bash
   python -m src.analytics.final_experimental_evaluation
   python -m src.analytics.system_performance_benchmark
   ```

4. **User-Controlled Git Commit & Push (When Ready)**:
   ```bash
   git status
   git add .
   git commit -m "Final Academic Release: Ambulance Route Optimization — Bengaluru (Phase 6 Complete)"
   git push origin main
   ```
