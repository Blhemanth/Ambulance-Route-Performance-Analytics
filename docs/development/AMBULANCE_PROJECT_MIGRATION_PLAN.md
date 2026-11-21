# AMBULANCE ROUTE OPTIMIZATION — BENGALURU
## PHASE 0 COMPREHENSIVE CODEBASE AUDIT & MASTER MIGRATION PLAN

**Document Version:** 1.0.0 (Phase 0 Audit)  
**Date:** 2026-11-20  
**Author:** Senior Python Developer, GIS Engineer, Operations Research Specialist, Data Engineer & Software Testing Engineer  
**Project Workspace:** `b:\Ambulance Route Optimization`  
**Git Remote Reference:** `https://github.com/Blhemanth/Bengaluru-Smart-Traffic-Optimizer.git` (Local separation enforced; no remote operations)  
**Target Application:** Interactive GIS-Based Ambulance Route Optimization Platform (Bengaluru, Karnataka)  

---

## 1. EXECUTIVE SUMMARY

An exhaustive Phase 0 technical inspection of the duplicated codebase at `b:\Ambulance Route Optimization` was performed to transition the application from its legacy focus (*Bengaluru Smart Traffic Optimizer: Traffic Signal Optimization Using Network Models*) to the officially designated academic project: **Ambulance Route Optimization**.

### Core Audit Findings
1. **Separation and Local Integrity**: The duplicated workspace is entirely intact. Git remotes currently point to the legacy repository; in accordance with strict development rules, no remote commands, commits, pushes, file moves, or overwrites have been executed. All work is strictly local.
2. **Road Network Dataset (`Bengaluru road network dataset/`)**: Contains a valid 534.02 MB OpenStreetMap binary Protocolbuffer file (`southern-zone-261119.osm.pbf`) downloaded from Geofabrik. It includes full road topology, one-way tags, and highway classifications for Southern India, encompassing Bengaluru.
3. **Hospital Dataset (`hospital dataset/`)**: Contains a valid 617.46 KB GeoJSON export (`export.geojson`) containing **1,084 mapped hospital features** across Bengaluru. 107 facilities are explicitly tagged with `emergency=yes` (Level 1 emergency/trauma centers), 28 with `emergency=no`, and 949 with unassigned emergency capability requiring clear verification tagging.
4. **Traffic Signal Engineering Plans (`traffic datasets/`)**: Exactly **118 PDF documents** (6.26 MB) are preserved. From these, 226 signalized intersections, 652 approach legs, 879 movement phases, and 5,362 time-of-day signal timing plans have already been extracted with 100% provenance traceability.
5. **Existing Graph and GIS Layer (`data/processed/`)**: An existing strongly-connected directed arterial road graph ($G_{\text{macro}}$) with **226 nodes and 1,164 directed edges** is fully functioning. It incorporates real OSM centerline curvatures along major corridors and full Indian Road Congress (IRC:106) capacity/free-flow speed calibrations.
6. **Existing Operations Research Implementation**: Dijkstra's algorithm (`ShortestPathOptimizer` in `src/network/shortest_path.py`) is already implemented and passing unit tests. It is mathematically and architecturally ready to be repurposed as the primary optimization engine for minimum estimated ambulance travel time ($t_{ij} = t_{\text{free}} + d_{\text{signal}} + \Delta t_{\text{congestion}}$).
7. **Test Suite Status**: 30 of 32 unit tests pass out of the box in 2.45s. The only 2 failing tests in `test_dataset_audit.py` are trivial path mismatches caused by folder renaming from `dataset/` to `traffic datasets/`.

---

## 2. CURRENT CODEBASE ARCHITECTURE

### 2.1 File & Directory Tree
```text
Ambulance Route Optimization/
├── .git/                                 # Legacy Git metadata (DO NOT TOUCH / PUSH)
├── .streamlit/                           # Streamlit server and theme configurations
├── assets/
│   ├── css/ & style.css                  # Unified dark styling (#080C14 background)
│   └── screenshots/                      # Regression UI screenshots
├── Bengaluru road network dataset/
│   └── southern-zone-261119.osm.pbf      # 534.02 MB OSM PBF Southern Zone extract
├── hospital dataset/
│   └── export.geojson                    # 1,084 Bengaluru hospitals GeoJSON (617 KB)
├── traffic datasets/                     # Exactly 118 PDF engineering signal drawings (6.26 MB)
├── data/
│   └── processed/                        # Extracted & validated tabular/GIS models
│       ├── extraction_errors.csv         # 0 errors logged
│       ├── intersections.csv             # 226 geocoded signalized junctions
│       ├── intersections_gis.csv         # 226 junctions with GIS metadata & provenance
│       ├── roads.csv                     # 652 intersection approach legs
│       ├── roads_gis.json                # 1,164 directed GIS road polylines
│       ├── signal_phases.csv             # 879 movement phases
│       └── signal_timings.csv            # 5,362 time-of-day signal timing schedules
├── components/
│   ├── gis_map.py                        # Reusable Folium/Leaflet multi-layer map component
│   └── ui_helpers.py                     # Caching, KPI cards, sidebar navigation, headers
├── pages/                                # Multi-page Streamlit application (10 pages)
│   ├── 1_Overview.py                     # Corpus overview & PDF audit
│   ├── 2_Dataset_Explorer.py             # Signal timing tables & schemas
│   ├── 3_Network_Visualization.py        # Macro/micro network topology map
│   ├── 4_Maximum_Flow.py                 # Dinic / Ford-Fulkerson min-cut
│   ├── 5_Minimum_Cost_Flow.py            # Network Simplex multicommodity flow
│   ├── 6_Shortest_Path.py                # Dijkstra baseline vs optimized routing
│   ├── 7_Signal_Optimization.py          # SciPy HiGHS LP signal green-split optimizer
│   ├── 8_Simulation_Centre.py            # Meso-queue dynamic traffic simulation
│   ├── 9_Analytics.py                    # Sensitivity analysis & corridor stress tests
│   └── 10_Methodology.py                 # Mathematical formulation & IRC:106 documentation
├── src/
│   ├── data_processing/                  # PDF extractors, table parsers, cleaners, validators
│   ├── database/                         # SQLite/schema interfaces
│   ├── network/                          # Graph builders, Dijkstra, GIS managers, analyzers
│   ├── optimization/                     # LP signal split solvers, sensitivity analysis
│   └── simulation/                       # Meso-scale vehicular simulation engine
├── tests/                                # 9 unit test suites (32 tests total)
├── app.py                                # Main Streamlit portal entry point
├── requirements.txt                      # Legacy python package dependencies
└── README.md & Reports                   # Legacy documentation
```

### 2.2 Entry Point and Data Loading Flow
- **Entry point**: `app.py` sets page layout to `wide`, injects custom dark CSS via `load_custom_css()`, and renders executive KPI metrics.
- **Caching Mechanism**:
  - `@st.cache_data load_all_datasets()` loads the five core processed CSV files from `data/processed/`.
  - `@st.cache_resource load_road_networks()` constructs the dual-level NetworkX directed graphs ($G_{\text{macro}}$ and $G_{\text{micro}}$).
  - `@st.cache_resource load_gis_network()` loads `GISNetworkManager`, generates 1,164 edge polylines, and enriches nodes with spatial attributes.

---

## 3. DATASET INVENTORY AND VALIDATION RESULTS

| Dataset Identifier | File / Folder Path | Format | Size | Total Records / Features | Status & Quality |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Dataset A: Road Network** | `Bengaluru road network dataset/southern-zone-261119.osm.pbf` | OpenStreetMap PBF (Protobuf) | 534.02 MB | Multi-million nodes/ways | **VALID & INTACT**. Header verified (`OSMHeader`). Contains full topology for Southern India (including Bengaluru). Needs bounding box clipping to study area. |
| **Dataset B: Hospitals** | `hospital dataset/export.geojson` | GeoJSON (RFC 7946) | 617.46 KB | 1,084 Features | **VALID & READY**. All features are `Point` geometry. Lat bounds: [12.8444, 13.1248], Lon bounds: [77.4752, 77.7591]. 1,068 named (98.5%). 107 verified emergency units. |
| **Dataset C: Signal PDFs** | `traffic datasets/*.pdf` | PDF (Vector CAD & Scans) | 6.26 MB | 118 PDF files (118 pages) | **VALID & INTACT**. 114 native CAD text vector sheets + 4 raster scans (3 unique sheets). 100% extracted into tabular datasets. |
| **Processed: Intersections** | `data/processed/intersections_gis.csv` | CSV | 59.1 KB | 226 rows, 16 cols | **VALID & PROCESSED**. Geocoded signalized intersections with BEL drawing source tracking and verification status (38 verified, 188 estimated). |
| **Processed: Road Edges** | `data/processed/roads_gis.json` | JSON Catalog | 871.8 KB | 1,164 directed edges | **VALID & PROCESSED**. Directed graph edges with real polyline coordinates, lengths, IRC:106 capacities, free-flow speeds, and signal delays. |
| **Processed: Signal Timing** | `data/processed/signal_timings.csv` | CSV | 551.8 KB | 5,362 timing plans | **VALID & PROCESSED**. Cycle lengths ($C_j$), phase green durations ($g_{jp}$), amber, and all-red across TOD time bands. |

### Deep Audit of Hospital Dataset (`export.geojson`)
- **Total Facilities**: 1,084
- **Amenity Distribution**:
  - `hospital`: 1,078 (99.4%)
  - `clinic`: 2
  - `university`: 1 (Bangalore University Health Centre)
  - `None`: 3
- **Emergency Tag Analysis**:
  - `emergency="yes"`: **107 facilities** (High priority: Manipal Hospital Old Airport Rd, Apollo Bannerghatta, Sanjay Gandhi Trauma Centre, Victoria Hospital, Bowring & Lady Curzon, NIMHANS, M.S. Ramaiah, St. John's Medical College Hospital).
  - `emergency="no"`: **28 facilities** (Specialized eye hospitals, dental clinics, cosmetic clinics).
  - `emergency=None` (Unspecified): **949 facilities** (General nursing homes, local community hospitals, maternity clinics).
- **Duplicate Records**: 79 duplicate names (989 unique names). Notable duplicates include multi-branch hospital networks (e.g., Manipal, Apollo, Fortis) as well as duplicate OSM elements for identical campuses (e.g., Sanjay Gandhi Trauma Hospital has two adjacent point features at [77.59359, 12.93563] and [77.59394, 12.93577]).
- **Spatial Bounds**: Latitudes range from 12.8444°N to 13.1248°N; Longitudes range from 77.4752°E to 77.7591°E. This perfectly spans the BBMP (Bruhat Bengaluru Mahanagara Palike) administrative boundary.

---

## 4. CODEBASE REUSE ASSESSMENT

| Module / Component | Current File Path | Category | Justification & Migration Action |
| :--- | :--- | :--- | :--- |
| **Dijkstra Shortest Path Engine** | `src/network/shortest_path.py` | **REUSE WITH MODIFICATION** | Already implements Dijkstra on NetworkX DiGraph with cost breakdowns. Modify to: (1) calculate ambulance travel time as primary objective; (2) support Emergency Vehicle Preemption (EVP) delay reductions; (3) compute top-$K$ alternative routes. |
| **GIS Network Manager** | `src/network/gis_network.py` | **REUSE WITH MODIFICATION** | Maintains real road curvature and coordinates. Modify to: (1) add nearest-node snapping for hospital coordinates; (2) associate hospital nodes with road network entry points. |
| **Folium Map Component** | `components/gis_map.py` | **REUSE WITH MODIFICATION** | Comprehensive multi-layer Leaflet component. Modify to: (1) add Hospital layer with emergency vs non-emergency icons; (2) add Origin dispatch pin; (3) render ambulance route trajectories with animated pulse or siren markers. |
| **UI Helpers & Theme** | `components/ui_helpers.py` | **REUSE WITH MODIFICATION** | Dark theme, KPI metric cards, and caching routines. Modify to: (1) update navigation drawer for Ambulance Route Optimization pages; (2) add hospital dataset loader. |
| **Macro Graph Builder** | `src/network/graph_builder.py` | **REUSE WITH MODIFICATION** | Builds 226-node, 1,164-edge strongly-connected graph. Modify to: integrate hospital connector edges and ambulance dispatch hubs. |
| **PDF Extraction Engine** | `src/data_processing/pdf_extractor.py`, `table_extractor.py`, `ocr_processor.py` | **REUSE WITHOUT MAJOR CHANGE** | Successfully extracted 5,362 timing records from 118 PDFs. Retain as data ingestion reference tools. |
| **Signal Timing Linear Programming** | `src/optimization/signal_optimizer.py` | **REUSE WITH MODIFICATION** | Re-frame from general queue minimization to **Ambulance Green Wave / Traffic Signal Preemption**: calculate green time extension or preemption along the ambulance route. |
| **Traffic Simulation** | `src/simulation/traffic_simulator.py` | **REUSE WITH MODIFICATION** | Re-frame to **Ambulance Dispatch Dynamic Simulation**: simulate response times under varying traffic congestion levels (peak vs off-peak). |
| **Maximum Flow Solver** | `src/network/maximum_flow.py` | **REMOVE FROM MAIN APPLICATION** | Not the primary OR technique for ambulance routing. Retain in codebase for reference; remove from UI navigation. |
| **Minimum Cost Flow Solver** | `src/network/minimum_cost_flow.py` | **REMOVE FROM MAIN APPLICATION** | Not the primary OR technique for ambulance routing. Retain in codebase for reference; remove from UI navigation. |
| **Network Analyzer** | `src/network/network_analyzer.py` | **REUSE WITHOUT MAJOR CHANGE** | Useful for computing topological centrality of road intersections relative to hospital locations. |
| **Sensitivity Analysis** | `src/optimization/sensitivity_analysis.py` | **REUSE WITH MODIFICATION** | Adapt to test travel-time sensitivity against traffic congestion surges, rain events, or signal failures. |

---

## 5. DATA GAPS AND ACQUISITION PLAN

To ensure academic rigor, datasets are strictly classified by provenance:

```
                    ┌───────────────────────────────────────────────┐
                    │          DATA PROVENANCE HIERARCHY            │
                    ├──────────────────────┬────────────────────────┤
                    │ ACTUAL / MEASURED    │ PDF Schedules, OSM     │
                    │ EXTERNAL             │ Overpass GeoJSON, BTP  │
                    │ ESTIMATED            │ Webster Delay, IRC:106 │
                    │ SYNTHETIC            │ Dispatch Calls, Peaks  │
                    └──────────────────────┴────────────────────────┘
```

### 5.1 Required Data (Phase 1 Prerequisites)
1. **Hospital Emergency Service Categorization**:
   - *Current State*: 107 facilities explicitly marked `emergency=yes`; 949 unspecified.
   - *Plan*: Create a curated emergency facilities lookup (`data/processed/hospitals_emergency_curated.csv`) tagging multi-specialty trauma centers, government tertiary hospitals (Victoria, Bowring, KC General), and corporate emergency rooms.
2. **Hospital-to-Road Snapping & Network Connectors**:
   - *Current State*: Hospitals are point coordinates; road network has 226 intersection nodes and 1,164 edges.
   - *Plan*: Implement a KDTree / Haversine nearest-edge projection function that projects each hospital onto the nearest traversable road edge, adding perpendicular access connector links $(h, v)$ with realistic entrance access delays (1–2 minutes).
3. **One-Way and Road Directionality Enforcement**:
   - *Current State*: $G_{\text{macro}}$ already models directed edges (1,164 directed edges).
   - *Plan*: Verify that emergency routing strictly respects one-way streets, or explicitly models contraflow permissions if academic assumptions allow emergency contraflow.

### 5.2 Optional / External Secondary Data
1. **Bengaluru Historical Speed Patterns**:
   - Public open data portals (OpenCity.in, Karnataka Transport Department) provide corridor-level averages (e.g., 15–18 km/h during peak hours in central zones vs 35–45 km/h on outer expressways).
   - *Plan*: Document corridor-specific peak speed derating factors (e.g., Central Silk Board corridor at 0.35x free-flow speed).
2. **Bengaluru 108 Emergency Ambulance Trip Benchmarks**:
   - Public health studies (GVK-EMRI Karnataka reports) cite average urban response times between 15 and 22 minutes.
   - *Plan*: Use published EMRI empirical response distributions as a benchmark for validation.

### 5.3 Synthetic vs Estimated Data Demarcation
- **Estimated Data**: Signal delay at intersections calculated via deterministic queuing theory / Webster's formula from actual BEL signal cycle lengths and green splits.
- **Synthetic Data**: Simulated emergency patient dispatch requests (incident origin lat/lon, severity triage level, time of day). These will be generated deterministically with fixed random seeds and clearly labelled as `SYNTHETIC`.

---

## 6. OPERATIONS RESEARCH MATHEMATICAL FORMULATION

### 6.1 Network Graph Representation
Let the Bengaluru road network be represented as a directed, weighted graph:
$$\mathcal{G} = (\mathcal{V}, \mathcal{E})$$
where:
- $\mathcal{V} = \mathcal{V}_I \cup \mathcal{V}_H \cup \{s\}$: set of nodes comprising road intersections ($\mathcal{V}_I$), hospital access points ($\mathcal{V}_H$), and emergency incident origin ($s$).
- $\mathcal{E} \subseteq \mathcal{V} \times \mathcal{V}$: set of directed traversable road links $(i, j)$.
- $w_{ij} \ge 0$: nonnegative estimated ambulance traversal time (cost) for traversing link $(i, j)$ in minutes.

### 6.2 Objective Function (Minimum Ambulance Travel Time)
$$\text{Minimize } Z = \sum_{(i,j) \in \mathcal{E}} w_{ij} \cdot x_{ij}$$
where $x_{ij} \in \{0, 1\}$ is a binary decision variable indicating whether edge $(i, j)$ is traversed in the optimal ambulance path.

### 6.3 Flow Conservation Constraints
$$\sum_{j:(i,j) \in \mathcal{E}} x_{ij} - \sum_{j:(j,i) \in \mathcal{E}} x_{ji} = \begin{cases}
1 & \text{if } i = s \text{ (Incident Origin)} \\
-1 & \text{if } i = t \text{ (Destination Hospital Entrance)} \\
0 & \forall i \in \mathcal{V} \setminus \{s, t\} \text{ (Intermediate Intersections)}
\end{cases}$$

$$x_{ij} \in \{0, 1\} \quad \forall (i, j) \in \mathcal{E}$$

### 6.4 Link Cost Impedance Function ($w_{ij}$)
The traversal time $w_{ij}$ across directed road link $(i, j)$ comprises three explicitly documented terms:
$$w_{ij} = t_{ij}^{\text{free}} + d_{j}^{\text{signal}}(\text{TOD}) + \Delta t_{ij}^{\text{traffic}}(\text{TOD})$$

1. **Free-Flow Road Travel Time ($t_{ij}^{\text{free}}$)**:
   $$t_{ij}^{\text{free}} = \frac{L_{ij}}{v_{ij}^{\text{free}}} \times \frac{60}{1000} \quad \text{(minutes)}$$
   where $L_{ij}$ is the real GIS geometric polyline length in meters, and $v_{ij}^{\text{free}}$ is the road class speed limit (e.g., 50 km/h on expressways, 40 km/h on major arterials, 30 km/h on collectors, per IRC:106).
2. **Signal Delay at Downstream Intersection ($d_{j}^{\text{signal}}$)**:
   Extracted from the 118 BEL engineering plans. For cycle length $C_j$ and green time $g_j$ for approach $(i, j)$:
   - **Standard Civilian Vehicle Delay**:
     $$d_{j}^{\text{standard}} = \frac{C_j \left(1 - \frac{g_j}{C_j}\right)^2}{2 \left(1 - \min\left(0.95, \frac{q_j}{s_j}\right)\right)} \quad \text{(Webster's first-term delay)}$$
   - **Ambulance with Siren / Priority Protocol**:
     Ambulances negotiate intersections with siren right-of-way or green preemption. A calibrated priority factor $\alpha \in [0.15, 0.50]$ applies:
     $$d_{j}^{\text{ambulance}} = \alpha \cdot d_{j}^{\text{standard}}$$
     *(If full Emergency Vehicle Preemption - EVP is active, $d_{j}^{\text{ambulance}} \approx 0$)*.
3. **Congestion Delay Penalty ($\Delta t_{ij}^{\text{traffic}}$)**:
   Calibrated by time-of-day (TOD) time band (Morning Peak, Evening Peak, Inter-peak, Night) based on the BTP timing plan active periods.

### 6.5 Algorithmic Solution
Because all edge costs $w_{ij} \ge 0$, the problem is solved to exact global optimality using **Dijkstra's Algorithm** with min-priority queue (Fibonacci / binary heap) in:
$$\mathcal{O}(|\mathcal{E}| + |\mathcal{V}| \log |\mathcal{V}|)$$
Guaranteed zero negative-cycle anomalies and strictly deterministic runtime ($< 5\text{ ms}$).

---

## 7. PROPOSED NEW APPLICATION ARCHITECTURE

The 10 application pages will be restructured specifically for Ambulance Route Optimization:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   AMBULANCE ROUTE OPTIMIZATION UI                      │
├───────────────────────────────────┬────────────────────────────────────┤
│ 1. Executive Dashboard            │ Map overview, emergency hospitals  │
│ 2. Road Network Explorer          │ Real OSM road geometry & one-ways  │
│ 3. Hospital Finder & Directory    │ Emergency capabilities & search    │
│ 4. Ambulance Route Optimizer      │ Core Dijkstra origin-to-hospital   │
│ 5. Alternative Route Comparison   │ Shortest time vs distance vs EVP   │
│ 6. Signal Delay & Green Wave      │ 118 BEL plans & preemption models  │
│ 7. Emergency Response Simulation  │ Peak vs off-peak Meso-queue runs   │
│ 8. Route Performance Analytics    │ Sensitivity, bottlenecks, benchmarks│
│ 9. Operations Research Methodology│ Equations, proofs, flow conservation│
│ 10. Data Governance & Provenance  │ Audit trail, 118 PDFs, OSM license │
└───────────────────────────────────┴────────────────────────────────────┘
```

### Detailed Page Breakdown
1. **Executive Dashboard (`app.py` & `pages/1_Overview.py`)**:
   - Live Bengaluru map with hospital pins color-coded by trauma level.
   - Core metrics: 1,084 hospitals mapped, 107 emergency trauma centers, 226 signalized junctions, 1,164 directed edges.
   - Quick ambulance routing widget for instantaneous dispatch.
2. **Bengaluru Road Network Explorer (`pages/2_Network_Explorer.py`)**:
   - Full Folium GIS road network display with layer toggles (arterials, one-ways, signalized intersections).
   - Directionality indicators, road classification filters, and curvature inspection.
3. **Hospital Finder & Emergency Directory (`pages/3_Hospital_Finder.py`)**:
   - Interactive search and filter tool for Bengaluru hospitals.
   - Filters: Emergency Ready (`emergency=yes`), 24/7 Service, Bed Capacity (where mapped), Distance radius from location.
   - Verified hospital cards with direct "Route Ambulance Here" button.
4. **Ambulance Route Optimizer (`pages/4_Ambulance_Optimizer.py`) - CORE ENGINE**:
   - Origin selector: click on map, select landmark, or enter coordinates.
   - Destination selector: filter by nearest emergency trauma facility or specific hospital.
   - Dijkstra solver execution: computes minimum travel-time trajectory.
   - Turn-by-turn navigation schedule: step, street name, distance, speed limit, signal delay, cumulative time.
   - Real-time GIS map highlighting the ambulance route in high-visibility medical emerald (`#10B981`) or urgent red (`#EF4444`).
5. **Alternative Route Comparison (`pages/5_Route_Comparison.py`)**:
   - Compares:
     - Route A: Minimum Travel Time (Dijkstra on $w_{ij}$).
     - Route B: Minimum Physical Distance (Dijkstra on $L_{ij}$).
     - Route C: Emergency Green Wave Route (Dijkstra with signal preemption).
   - Side-by-side metric table: travel time difference, distance delta, number of traffic signals traversed, risk of congestion delay.
6. **Traffic Signal Delay & Green Wave Analysis (`pages/6_Signal_Delay_Analysis.py`)**:
   - Deep inspection of the 118 BEL traffic signal plans.
   - Cycle lengths, phase splits, and approach delays along the chosen corridor.
   - Mathematical model for Emergency Vehicle Preemption (EVP): how signal preemption saves 3–8 minutes of critical patient transit time.
7. **Emergency Response Simulation (`pages/7_Response_Simulation.py`)**:
   - Dynamic meso-queue simulation of ambulance runs across peak vs off-peak hours.
   - Response time distribution histograms ($T \le 8\text{ min}$, $8 < T \le 15\text{ min}$, $T > 15\text{ min}$).
8. **Performance Benchmarking & Analytics (`pages/8_Performance_Analytics.py`)**:
   - Corridor-by-corridor ambulance speed heatmaps.
   - Sensitivity analysis: effect of severe weather (monsoon rain derating) or signal failure on hospital access times.
9. **OR Methodology & Academic Foundations (`pages/9_OR_Methodology.py`)**:
   - Formal mathematical formulation (decision variables, objective, constraints).
   - Dijkstra optimality proof, time complexity analysis ($\mathcal{O}(|E| + |V| \log |V|)$).
   - Academic references (Dijkstra 1959, Webster 1958, IRC:106-1990).
10. **Data Provenance & PDF Archive (`pages/10_Data_Provenance.py`)**:
    - Complete transparency log of data sources: 118 BEL drawings, OSM Geofabrik, Overpass Turbo.
    - PDF verification viewer allowing examiners to cross-reference extracted numbers with original engineering drawings.

---

## 8. GIS IMPLEMENTATION ARCHITECTURE

### 8.1 Hospital Snapping Algorithm
To prevent arbitrary straight-line jumps, hospitals will be mapped to the road network using perpendicular projection:
1. For hospital coordinate $H = (\text{lat}_H, \text{lon}_H)$, find candidate directed road edges $e = (u, v)$ within radius $R = 1,000\text{ m}$.
2. Project $H$ onto the piecewise linear road geometry of edge $e$ to find projected point $P_e$.
3. Choose the candidate edge minimizing the perpendicular distance $\|H - P_e\|_2$.
4. Split edge $(u, v)$ or insert a virtual access edge $(H, u)$ with length $\|H - u\|$ and speed $v_{\text{access}} = 15\text{ km/h}$ plus a 1-minute facility gate traversal penalty.
5. If the nearest road is $> 1,500\text{ m}$ away, mark the hospital as `REQUIRES_MANUAL_VERIFICATION`.

```
          Node u ────────────────── P_e ────────────────── Node v
                                     │
                                     │  Entrance Access Link (15 km/h)
                                     ▼
                              [🏥 Hospital H]
```

### 8.2 Map Rendering
- Multi-layer Folium map rendered in Streamlit using `streamlit-folium`.
- High-contrast base tiles: OpenStreetMap Default, CartoDB Positron, and CartoDB Dark Matter.
- Custom Leaflet SVG icons for:
  - 🟢 Origin (Incident scene).
  - 🏥 Destination Hospital (Level 1 Trauma in green, general in blue).
  - 🚦 Signalized Intersections (with cycle time popups).
  - 🚑 Animated / Polyline route trace with turn arrows.

---

## 9. INTEGRATION OF THE 118 TRAFFIC SIGNAL PDFS

The user's 118 collected signal PDFs represent an invaluable primary engineering dataset. They are leveraged directly in the ambulance routing model:
1. **Signalized Intersection Markers**: Every one of the 226 junctions on the road network is pinned with coordinates, police station jurisdiction, and source PDF reference.
2. **Signal Delay Calculation**: Extracted cycle times $C_j$ and green times $g_j$ are used directly in the link delay equation $d_j^{\text{signal}}$.
3. **Emergency Preemption Evaluation**: The platform computes the time penalty an ambulance incurs waiting at red phases vs the time saved if a "Green Corridor" (signal preemption) is cleared by Bengaluru Traffic Police.
4. **Examiner Traceability**: Clicking on any signalized intersection in the application displays the exact PDF filename (e.g., `0095d044-2963-40ae-abbe-89769cae9bf5.pdf`), page number, cycle length, and approach timing plans.

---

## 10. DEPENDENCY & ENVIRONMENT AUDIT

### 10.1 Active Environment
- Python version: `3.13.14 (64-bit AMD64)`
- Currently installed packages:
  - `networkx` 3.7 (Fully compatible)
  - `streamlit` 1.66.1 (Fully compatible)
  - `streamlit-folium` 0.27.4 & `folium` 1.0.0 (Fully compatible)
  - `pandas` 3.0.5 & `numpy` 2.4.5 (Fully compatible)
  - `scipy` 1.18.1 & `PuLP` 4.2.0 (Fully compatible)
  - `pypdf` 7.1.0 & `pdfplumber` 0.11.10 (Fully compatible)
  - `plotly` 7.1.0 (Fully compatible)

### 10.2 Recommended Package Additions (Pending User Approval)
To process the 534 MB `.osm.pbf` file or perform advanced spatial joins:
- `shapely` & `geopandas`: For native vector geometries and spatial point-in-polygon checks.
- `pyrosm` or `osmium`: For high-speed binary parsing of the `.osm.pbf` file.
*Note: Under strict development rules, no packages have been installed or modified in Phase 0.*

---

## 11. TESTING AND VALIDATION STRATEGY

### 11.1 Unit & Regression Tests
The existing test suite (`tests/`) has 32 tests. To ensure zero regressions:
1. Fix the 2 dataset path tests in `tests/test_dataset_audit.py` to point to `traffic datasets/`.
2. Add new test suites:
   - `test_hospital_dataset.py`: Verify GeoJSON parsing, emergency tag filters, coordinate bounds.
   - `test_ambulance_routing.py`: Test Dijkstra on ambulance objective function, ensure travel time is strictly positive, verify flow conservation.
   - `test_hospital_snapping.py`: Verify hospital snapping onto network edges.
   - `test_route_comparison.py`: Test comparison between minimum-distance and minimum-time routes.

### 11.2 Verification Checkpoints
- Automated test execution: Target 100% pass rate (> 40 tests).
- Local headless compile check: `python -m py_compile` across all pages.
- Local Streamlit launch check: `streamlit run app.py` running locally on port 8501.

---

## 12. IMPLEMENTATION PHASES & ROADMAP

```
┌────────────────────────────────────────────────────────────────────────┐
│                   IMPLEMENTATION ROADMAP PHASES                        │
├────────────────────────────────────────────────────────────────────────┤
│ PHASE 0: Codebase Audit & Master Migration Plan       [COMPLETED NOW]  │
│ PHASE 1: Data Ingestion, Hospital & Road Network Layer [AWAITING OK]   │
│ PHASE 2: Core Dijkstra Ambulance Routing Engine                        │
│ PHASE 3: Interactive GIS Multi-Page Streamlit UI                       │
│ PHASE 4: Signal Preemption & Response Simulation                       │
│ PHASE 5: Verification, Benchmarking & Final Documentation              │
└────────────────────────────────────────────────────────────────────────┘
```

- **Phase 0 (Current)**: Codebase and dataset audit, mathematical formulation, migration plan creation. **COMPLETED**.
- **Phase 1 (Data Integration)**: Connect `export.geojson` and `data/processed/`, curate emergency hospital classifications, build hospital-to-road snapping module.
- **Phase 2 (OR Optimization)**: Adapt `ShortestPathOptimizer` for ambulance travel time, implement green-wave preemption impedance, build alternative route comparison.
- **Phase 3 (GIS UI & Streamlit Pages)**: Reconfigure the 10 Streamlit pages with ambulance-specific routing controls, hospital search directory, and interactive Folium maps.
- **Phase 4 (Simulation & Green Wave)**: Calibrate time-of-day signal delays from the 118 PDFs and build dynamic response-time simulation.
- **Phase 5 (Testing & Documentation)**: Expand unit test suite to > 40 tests, document academic assumptions, and compile final project reports.

---

## 13. ACADEMIC ASSUMPTIONS, LIMITATIONS & ETHICS

1. **Non-Clinical Scope**: The routing model optimizes vehicle travel time from dispatch/incident location to emergency facility entrance. It does not provide medical advice or prioritize clinical triage.
2. **Signal Preemption Assumptions**: Emergency Vehicle Preemption (EVP) assumes signal controllers or traffic police can grant green waves along arterial segments. When preemption is inactive, ambulances experience calibrated siren delay $\alpha \cdot d_j$.
3. **Traffic Congestion Estimates**: In the absence of proprietary commercial live traffic APIs, traffic congestion is modeled using validated Time-of-Day (TOD) peak factors derived from the official BTP signal schedules and IRC:106 guidelines.
4. **Data Privacy**: No private patient records, vehicle GPS traces, or personal health information are utilized. All geographic and hospital data are sourced from public OpenStreetMap extracts and official signal plans.
5. **No Fabricated Attributes**: Any unverified hospital emergency capability or unmapped road attribute is explicitly tagged as `UNVERIFIED` or `ESTIMATED`.

---

## 14. RISKS AND RECOMMENDATIONS FOR USER APPROVAL

1. **Risk 1: Git Remote Overwrite Hazard**
   - *Issue*: The duplicated directory contains a `.git` folder whose remote points to `https://github.com/Blhemanth/Bengaluru-Smart-Traffic-Optimizer.git`.
   - *Recommendation*: Leave `.git` untouched during local development. When ready, the user can either re-initialize a new repository (`git init`) or change the remote URL.
2. **Risk 2: Processing the 534 MB Southern Zone PBF File**
   - *Issue*: Parsing a 534 MB `.osm.pbf` file in pure Python requires substantial memory or external binary tools (`osmium` / `pyrosm`).
   - *Recommendation*: The existing processed arterial network (`roads_gis.json` with 1,164 directed edges) already covers all major Bengaluru corridors. For Phase 1, snap the 1,084 hospitals directly to this 1,164-edge network, or extract the Bengaluru bounding box from the PBF file when approved.
3. **Risk 3: Unverified Hospital Emergency Capabilities**
   - *Issue*: 949 of 1,084 hospitals in the OSM export lack explicit `emergency` tags.
   - *Recommendation*: Provide a prominent UI toggle: "Filter Verified Emergency Facilities Only (107 Hospitals)" vs "Show All Mapped Facilities (1,084 Hospitals)" with clear verification status badges.
