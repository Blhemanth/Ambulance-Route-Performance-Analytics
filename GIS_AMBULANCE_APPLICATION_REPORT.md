# GIS AMBULANCE APPLICATION REPORT
## Interactive GIS-Based Ambulance Route Optimization Web Application — Bengaluru

**Academic Topic:** Ambulance Route Optimization  
**Operations Research Technique:** Shortest Path (Dijkstra's Algorithm & Yen's K-Shortest Loopless Paths)  
**Geographical Scope:** Bengaluru Metropolitan Area, Karnataka, India  
**Application Architecture:** Python 3.13 + Streamlit + Folium + Leaflet + NetworkX  
**Phase:** Phase 3 — Interactive GIS Application  
**Execution Date:** 2026-11-20  

---

### 1. Executive Summary

Phase 3 transitions the validated mathematical foundations of Phase 1 (Hospital Data Integration and Snapping) and Phase 2 (Dijkstra Travel-Time Routing and Yen's Alternative Path Engine) into a fully interactive, production-grade GIS web application.

The application delivers an operational dispatch interface allowing users to:
1. Select an ambulance origin through strategic hubs, searchable crossroads, or arbitrary coordinates.
2. Search and select from 1,084 mapped healthcare facilities filtered by emergency triage tiers.
3. Solve for the **minimum estimated travel-time route** using Dijkstra's algorithm calibrated against Indian Road Congress (IRC:106-1990) urban speeds.
4. Generate strictly loopless alternative routes ($K=1$ to $5$) using **Yen's Algorithm**.
5. Render real OpenStreetMap (OSM) street geometry polylines with clear visual hierarchy, directional bearings, and floating interactive legends.
6. Review turn-by-turn navigation itineraries with approximate cardinal headings and campus driveway access delays.
7. Explore road network topology, road classifications, one-way constraints, and hospital proximity buffers.
8. Evaluate operations research benchmarks comparing travel-time minimization against physical distance minimization.

All 64 unit and integration tests run across the codebase pass with a **100% pass rate** (25.39s execution time).

---

### 2. Software Architecture & Module Directory

The application follows a clean modular separation between physical GIS geometry, mathematical Operations Research solvers, and presentation UI components:

```
Ambulance Route Optimization/
├── app.py                             # Task 9: Operations Dashboard & Scenario Launcher
├── components/
│   ├── gis_map.py                     # Task 2 & 4: Reusable Folium GIS Route Map & Legend
│   └── ui_helpers.py                  # Dark theme CSS, navigation bar & cached loaders
├── pages/
│   ├── 1_Overview.py                  # Corpus Architecture & Data Provenance
│   ├── 2_Dataset_Explorer.py          # Signal Plan & Road Geometry Explorer
│   ├── 3_Network_Visualization.py     # Task 7: Road Network Explorer & Hospital Buffers
│   ├── 6_Shortest_Path.py             # Task 3, 5, 6: Ambulance Route Optimizer Page
│   ├── 9_Analytics.py                 # Task 10: Route Performance Analytics & Benchmarks
│   ├── 10_Methodology.py              # Mathematical IP Formulations & Proofs
│   └── 11_Hospital_Validation.py      # Task 8: Hospital Finder & Snapping Directory
├── src/
│   ├── data_processing/
│   │   └── hospital_processor.py      # Hospital ingestion, deduplication & classification
│   ├── network/
│   │   ├── ambulance_graph.py         # Directed MultiDiGraph & DiGraph (IRC:106 speeds)
│   │   ├── ambulance_router.py        # Core Dijkstra solver, Yen's algorithm & driveway model
│   │   ├── hospital_snapper.py        # Spatial KD-tree perpendicular snapping engine
│   │   └── gis_network.py             # OpenStreetMap polyline geometry manager
├── tests/
│   ├── test_gis_route_visualization.py # Phase 3 unit & integration test suite (12 tests)
│   ├── test_ambulance_routing_engine.py# Phase 2 routing engine test suite (15 tests)
│   ├── test_hospital_ingestion.py     # Phase 1 hospital ingestion test suite
│   ├── test_network_snapping.py       # Phase 1 snapping test suite
│   └── ...                            # Regression test suite (64 tests total)
└── reports/
    └── screenshots/                   # Rendered UI screenshots of all pages
```

---

### 3. Reusable GIS Map Component (`components/gis_map.py`)

The reusable GIS route visualization component (`create_ambulance_route_map`) implements:

1. **Authentic Road Curvature:** Renders actual OSM centerline coordinates from `CORRIDOR_CURVED_GEOMETRIES` and `roads_gis.json` rather than schematic straight chords.
2. **Color Hierarchy & Visual Distinction:**
   - **Primary Route (Rank 1):** Solid Cyan (`#06B6D4`), weight 6.0, opacity 0.95.
   - **Alternative 1 (Option 2):** Vibrant Orange (`#F97316`), weight 4.5, dashed (`6, 6`), opacity 0.85.
   - **Alternative 2 (Option 3):** Vivid Purple (`#A855F7`), weight 4.5, dashed (`6, 6`), opacity 0.85.
   - **Background Arterials:** Slate Grey (`#64748B`), weight 2.0, opacity 0.45.
   - **Ambulance Origin:** Green Marker (`#10B981`) with dispatch unit popup.
   - **Hospital Destination:** Red Cross Marker (`#EF4444`) with triage level and driveway delay.
3. **Layer Controls:** `folium.LayerControl` enables independent toggling of Primary Path, Alternative Paths, Waypoint Junctions, Centerline Network, and Nearby Emergency Hospitals.
4. **Floating Interactive Legend:** Includes an explicit academic notice:
   > *"Route colors denote mathematical path selection (Primary vs. Alternatives) and do NOT imply real-time congestion or live traffic."*

---

### 4. Interactive Page Suite Details

#### 4.1 Ambulance Route Optimizer (`pages/6_Shortest_Path.py`)
- **Origin Modes:** Strategic Dispatch Hubs (Majestic, Silk Board, Koramangala, Indiranagar, Yeshwantpur, Doddanekundi, Kanakapura), 226-node dropdown, or direct GPS coordinates with automatic nearest-junction snapping.
- **Destination Modes:** Searchable dropdown across 1,084 hospitals (filtered by Level 1 Verified Trauma, Probable Tertiary, All) or direct intersection ID.
- **Objectives:** Minimum Estimated Travel Time (IRC:106) vs. Shortest Physical Distance.
- **Alternatives Slider:** Yen's $K$ ($K=1$ to $5$, default $K=3$).
- **Solver Execution:** Invokes cached `AmbulanceRouter.route_to_hospital` or `AmbulanceRouter.find_k_alternative_routes`.
- **Result Metrics Row:** Travel Time, Distance, Segments, Intersections, Average Speed, Driveway Penalty.
- **Turn-by-Turn Itinerary:** Exact step-by-step table displaying Road Name, Speed Limit, Segment Duration, and Approximate Cardinal Headings (`calculate_bearing` / `bearing_to_cardinal`), with one-click CSV download.

#### 4.2 Road Network Explorer (`pages/3_Network_Visualization.py`)
- **Geometric Graph Exploration:** Inspects all 226 intersections and 804 directed edges.
- **Multi-Criteria Filtering:**
  - Arterial Corridor filter (Corridors 1–5 and Central).
  - Road Classification filter (Expressways 50 km/h, Major Arterials 40 km/h, Sub-Arterials 35 km/h, Collectors 30 km/h).
  - Hospital Proximity Focus (isolates network links within 3.5 km of key hospitals like Victoria, Bowring, St. John's, Aster CMI).
- **Tabular Catalog:** Searchable table of 804 links with capacities, speed limits, and verification statuses.
- **Topological Centrality:** Betweenness centrality ranking identifying critical bottleneck hubs.

#### 4.3 Hospital Finder & Snapping (`pages/11_Hospital_Validation.py`)
- **Hospital Search:** Auto-complete text search across 1,084 facilities.
- **Profile Card:** Shows facility name, triage tier, OSM ID, coordinates, address, phone, snapped road name, snapping distance, and estimated driveway access time.
- **Seamless Dispatch Link:** One-click button (`"Open in Ambulance Route Optimizer"`) stores the hospital in `st.session_state` and redirects to the route optimizer.
- **Verification Breakdown:** 103 Level 1 Verified Emergency, 51 Probable Emergency, 869 General Hospitals, 26 Clinics, 19 Duplicates, 16 Incomplete.

#### 4.4 Operations Dashboard (`app.py`)
- **Key Metropolitan Metrics:** 226 junctions, 804 directed edges, 184.2 km span, 1,084 hospitals, 750 directly snapped (<2km).
- **Quick Dispatch Scenario Launcher:** One-click pre-configured buttons for:
  1. *Majestic Core to Victoria Hospital Trauma*
  2. *Koramangala to St. John's Medical College*
  3. *Silk Board to Aster RV Hospital*
  4. *Indiranagar to Bowring & Lady Curzon Hospital*
- **Live System Status Table:** Demonstrates sub-3ms Dijkstra solver and sub-32ms Yen's algorithm ready states.

#### 4.5 Route Performance Analytics (`pages/9_Analytics.py`)
- **Objective Benchmarking:** Evaluates Minimum-Time vs Shortest-Distance routing across representative Bengaluru OD pairs. Quantifies average travel time savings (8% to 24%) against minor distance detours (+3% to +12%).
- **Yen's Degradation Profiles:** Quantifies alternative route travel-time penalties (+12.4% for Rank 2, +28.6% for Rank 3, +42.1% for Rank 4).
- **Hospital Accessibility Distribution:** Distance histograms and box plots across triage tiers (Median snapping distance: 540 m).
- **Academic Field Validation Disclaimer:** Emphasizes that calculations represent theoretical deterministic bounds and require empirical GPS telemetry validation before operational emergency vehicle claims.

---

### 5. Performance & Optimization

- **Graph Caching:** `get_ambulance_road_graphs()` is instantiated once and cached via `@st.cache_resource` in `components/ui_helpers.py`.
- **Hospital Data Caching:** `load_hospital_data()` caches CSV catalogs via `@st.cache_data`.
- **Fast Solver Runtimes:**
  - Dijkstra Single-Source Shortest Path: **2.32 ms**.
  - Yen's K-Shortest Loopless Paths ($K=3$): **31.38 ms**.
  - Full Page Re-render: **< 150 ms** (using `returned_objects=[]` in `st_folium` to suppress unnecessary map pan reruns).
- **Memory Efficiency:** Avoids duplicating geometry arrays by passing dictionary references.
