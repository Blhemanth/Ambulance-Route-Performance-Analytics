# BENGALURU SMART TRAFFIC OPTIMIZER
## COMPREHENSIVE APPLICATION ARCHITECTURE & CODEBASE AUDIT REPORT

**Date of Audit**: November 19, 2026  
**Auditor Roles**: Senior Software Engineer, GIS Engineer, Operations Research Specialist, UI/UX Auditor, QA Lead  
**Academic Focus**: Operations Research — Network Models (Maximum Flow, Minimum Cost Flow, Shortest Path, Signal Timing LP)  
**Corpus**: 118 PDF Signal Drawings from Bharat Electronics Limited (BEL) & Bengaluru Traffic Police (BTP)  
**Network Scale**: 226 Signalized Intersections, 652 Approaches, 879 Phase Movements, 5,362 Timing Plans, 1,142 Directed Edges  

---

## 1. EXECUTIVE AUDIT SUMMARY

This audit represents an empirical inspection of the complete codebase of the **Bengaluru Smart Traffic Optimizer**. Every page, computational module, data pipeline, and visualization component was evaluated against theoretical Operations Research standards, transportation engineering principles (IRC:106 / IRC:93), and GIS fidelity.

### Primary Architectural Finding: The GIS Representation Deficit
While the mathematical formulation and solver backends (NetworkX, SciPy HiGHS, Network Simplex, and Dijkstra) are algebraically sound and execute with 100% test pass rates, **the spatial visualization layer is fundamentally detached from real Bengaluru geography**:
1. **Abstract Centroid Cartography**: Pages 3, 4, and 6 visualize the road network as abstract straight line segments connecting intersection coordinates on a blank Cartesian plane (Plotly Scatter), cutting straight through residential buildings, lakes, parks, and flyovers.
2. **Missing Real Road Geometries**: No OpenStreetMap (OSM) street polylines or way-geometries are utilized.
3. **Total Visualization Absence on Key Pages**: Page 5 (Minimum Cost Flow) completely lacks a spatial network map, rendering optimal flow allocations solely in tabular format.
4. **No Layer Controls or Street Interactivity**: The user cannot switch between road capacity, directional flows, bottleneck cut boundaries, or street map tiles.

---

## 2. DETAILED PAGE-BY-PAGE AUDIT & CLASSIFICATION

---

### Page 0: Root Portal (`app.py`)
- **Current Functionality**: Executive gateway displaying system-wide KPI metrics (226 Intersections, 1,142 Directed Edges, 5,362 Timing Plans, 4 Coupled Models), an overview of the 5 study corridors, 3-phase module action cards, and workflow switcher.
- **UI/UX Issues**: Clean dark styling, but lacks an immediate spatial visual anchor. The user sees numbers and text cards without visual confirmation of Bengaluru's geographic boundary.
- **Mathematical Issues**: None. Accurately states the 4 interconnected OR models and the capacity feedback loop ($u_{ij} = s_{ij} \cdot g_{jp} / C_j$).
- **Data Issues**: Graph and datasets are loaded once into memory cleanly via cached helpers.
- **Visualization Issues**: No geographical mini-map or spatial overview of Bengaluru's metropolitan boundaries.
- **Bugs Verified**: None.
- **Missing Functionality**: Interactive geographical corridor selector map or metropolitan boundary overview.
- **Improvements**: Add an interactive GIS map preview showing the geographic spread of the 226 signalized nodes across Bengaluru's urban expanse.
- **Priority**: **LOW**

---

### Page 1: Corpus Architecture & Dataset Audit (`pages/1_Overview.py`)
- **Current Functionality**: High-level PDF corpus classification (114 Vector CAD vs 4 Scanned Raster drawings), Time-of-Day (TOD) plan distribution, police station jurisdiction counts, and data provenance traceability matrix.
- **UI/UX Issues**: Clear Donut charts and provenance tables.
- **Mathematical Issues**: None. Descriptive statistics.
- **Data Issues**: Accurately accounts for 118 PDF files. Provenance explicitly tags data as ACTUAL, EXTERNAL, or MEASURED.
- **Visualization Issues**: The spatial distribution of police stations and intersections is displayed as a tabular bar chart rather than a geospatial density map across Bengaluru's administrative zones.
- **Bugs Verified**: None.
- **Missing Functionality**: GIS spatial density map / choropleth showing intersection distribution by Bengaluru Traffic Police (BTP) divisions.
- **Improvements**: Embed an OpenStreetMap-backed density view showing regional signal clusters.
- **Priority**: **MEDIUM**

---

### Page 2: Signal Plan Explorer (`pages/2_Dataset_Explorer.py`)
- **Current Functionality**: Filterable tabular catalogs across 6 tabs: Intersections (226), Road Approaches (652), Signal Phases (879), Timing Plans (5,362), Extraction Audit Logs, and Manual Timing Adjustment with Webster Delay estimation.
- **UI/UX Issues**: Tab 1 and Tab 2 contain coordinates (lat/long) and street names, but provide no visual spatial confirmation of where an intersection is located on the real road network.
- **Mathematical Issues**: Webster delay equation in Tab 6 is rigorously implemented:
  $$d = \frac{C(1 - \lambda)^2}{2(1 - \lambda x)} + \frac{x^2}{2q(1 - x)}$$
- **Data Issues**: Coordinates for certain intersections are derived from police station centroids or nearest road landmarks and carry the tag `ESTIMATED`. Analysts cannot visually inspect if a node coordinate aligns with the actual physical crossroads.
- **Visualization Issues**: Complete lack of an embedded map view for coordinate verification.
- **Bugs Verified**: None. (Phase slider schema was previously hardened to match variable junction phase counts).
- **Missing Functionality**: "Verify on Map" button or side-by-side OpenStreetMap preview for any selected intersection.
- **Improvements**: Integrate an interactive OpenStreetMap Leaflet pane in Tab 1 allowing analysts to drag/verify coordinates against satellite/street imagery.
- **Priority**: **HIGH**

---

### Page 3: Road Network Topology & Turning Movements (`pages/3_Network_Visualization.py`)
- **Current Functionality**: Dual-level graph explorer: Level 1 Macro Corridor Network $G=(V,E)$ and Level 2 Micro Turning Movement Structure, plus Network Centrality analytics.
- **UI/UX Issues**: The macro network is rendered in Plotly Scatter with plain Cartesian axes (Longitude vs Latitude). The background is a solid dark fill with no geographical context (no roads, landmarks, water bodies, or street names).
- **Mathematical Issues**: **CRITICAL**: The edge lengths in $G_{\text{macro}}$ are computed using straight-line Euclidean/Haversine distance between node centroids ($dist_m = \text{haversine}(lat_1, lon_1, lat_2, lon_2)$), arbitrarily clamped to $[350, 2500]$ meters, rather than utilizing true OpenStreetMap curved road geometry lengths!
- **Data Issues**: Road links are currently defined via 33 hardcoded corridor connections plus nearest-neighbor heuristics, instead of an authentic OpenStreetMap edge topology.
- **Visualization Issues**: **CRITICAL**: Roads are drawn as straight lines connecting intersection dots, cutting through urban blocks, residential sectors, and lakes.
- **Bugs Verified**: Visual artifacts where straight lines cross non-road terrain.
- **Missing Functionality**: OpenStreetMap tile layer, satellite imagery basemap, real street polyline geometry, zoom-to-corridor controls, directional arrows, and clickable Leaflet popups showing junction signal timing plans.
- **Improvements**: Complete architectural overhaul using Folium / Leaflet / OSMnx street network geometry with toggleable layers.
- **Priority**: **CRITICAL**

---

### Page 4: Model 1 - Maximum Network Flow (`pages/4_Maximum_Flow.py`)
- **Current Functionality**: Solves the maximum hourly throughput $F^*$ from Source $s$ to Sink $t$ using Ford-Fulkerson / Dinic algorithms. Identifies saturated cut edges via the Max-Flow Min-Cut Theorem. Displays bottleneck table and capacity utilization histogram.
- **UI/UX Issues**: Effective KPI cards and bottleneck table, but the flow distribution map at the bottom of the page is an abstract Plotly scatter plot with straight lines.
- **Mathematical Issues**: Mathematically sound. Formulates primal maximum flow LP and verifies strong duality ($\max F = \min \text{Cut Capacity}$).
- **Data Issues**: Capacities calibrated from IRC:106 standards and green splits.
- **Visualization Issues**: **HIGH**: The minimum-cut bottlenecks are rendered as abstract dots and straight lines. A traffic planner cannot visually identify which real city streets constitute the bottleneck cut or where physical road widening is required.
- **Bugs Verified**: None (column index aliases and preset scoping verified).
- **Missing Functionality**: Real geographical map displaying:
  1. Street segments styled with line width proportional to traffic flow $x_{ij}$.
  2. Saturated bottleneck cut edges highlighted in vivid glowing red along their actual street curvature.
  3. Source ($s$) and Sink ($t$) pin markers on real Bengaluru street maps.
- **Improvements**: Replace Plotly scatter with Folium map rendering actual OSM street geometries for flow and cut edges.
- **Priority**: **HIGH**

---

### Page 5: Model 2 - Minimum Cost Flow (`pages/5_Minimum_Cost_Flow.py`)
- **Current Functionality**: Solves optimal multicommodity traffic allocation $\min \sum c_{ij} x_{ij}$ subject to flow balance and link capacities using Network Simplex. Identifies over-congested links ($v/c > 0.85$).
- **UI/UX Issues**: Tabular flow allocation and congestion pie charts are well presented, but **there is NO network map visualization whatsoever on this page**.
- **Mathematical Issues**: Rigorous Network Simplex execution satisfying Hoffman's circulation feasibility bounds ($F \le 0.95 F^*_{\text{max}}$). Zero-division defensive guards verified.
- **Data Issues**: Travel costs derived from free-flow travel time plus Webster signal delays.
- **Visualization Issues**: **CRITICAL**: The user is forced to inspect optimal link flows in a raw data table with no spatial comprehension of how traffic is distributed across parallel Bengaluru corridors.
- **Bugs Verified**: None.
- **Missing Functionality**: An interactive GIS map showing:
  1. Active flow-carrying road segments colored by volume-to-capacity ratio ($v/c$).
  2. Congestion layer highlighting over-saturated links ($v/c > 0.85$) in red.
  3. Green supply/demand pins at Origin and Destination.
- **Improvements**: Implement an interactive Folium map component displaying the Network Simplex flow distribution on actual street geometries.
- **Priority**: **CRITICAL**

---

### Page 6: Model 3 - Shortest Path Routing (`pages/6_Shortest_Path.py`)
- **Current Functionality**: Computes minimum-cost route between origin and destination using Dijkstra's algorithm. Evaluates Baseline route (BEL signal timings) vs Optimized route (HiGHS signal timings). Displays turn-by-turn itinerary table and stacked delay comparison.
- **UI/UX Issues**: Good KPI cards and turn-by-turn itinerary table.
- **Mathematical Issues**: Multi-attribute Dijkstra routing correctly supports travel time, free-flow time, physical distance, and economic cost.
- **Data Issues**: Routing paths use node centroid connections.
- **Visualization Issues**: **HIGH**: The "Geographical Shortest Path Alignment" map connects intersection centroids with straight line segments across city blocks, rather than following the true physical bends, curves, and turns of Bengaluru's road geometry.
- **Bugs Verified**: None (fixed previous metric ignoring bug).
- **Missing Functionality**: Real street routing polyline following OSM road centreline geometry, turn-by-turn waypoint popups, and side-by-side or layered comparison of the baseline vs optimized path.
- **Improvements**: Overlay the Dijkstra route directly onto real OpenStreetMap street polylines with turn direction arrows.
- **Priority**: **HIGH**

---

### Page 7: Model 4 - Traffic Signal Timing Linear Programming (`pages/7_Signal_Optimization.py`)
- **Current Functionality**: Formulates and solves queue-minimizing signal timing optimization via SciPy HiGHS simplex. Enforces cycle conservation $\sum g_p + L = C$ and departure bounds. Interactive phase arrival tuning sliders.
- **UI/UX Issues**: Comprehensive mathematical formulation and clean split bar charts.
- **Mathematical Issues**: Fully validated LP formulation. Clearance underflow guards prevent infeasible status codes.
- **Data Issues**: Phase counts and baseline timing plans derived directly from BEL CAD tables.
- **Visualization Issues**: Visualizations are limited to bar and radar charts. There is no spatial map showing the physical intersection layout, approach roads, or geographical context within the Bengaluru arterial network.
- **Bugs Verified**: None (fixed composite widget key collision).
- **Missing Functionality**: Mini-GIS map showing the intersection's exact geographic location on OpenStreetMap with satellite toggle and approach direction vectors.
- **Improvements**: Embed a compact Folium map pane showing the intersection node and its connecting road approaches.
- **Priority**: **MEDIUM**

---

### Page 8: Dynamic Simulation Centre (`pages/8_Simulation_Centre.py`)
- **Current Functionality**: Comparative dynamic meso-queue simulation tracking queue dissipation and delay accumulation over 1800s to 7200s under stochastic Poisson vehicular arrivals.
- **UI/UX Issues**: Well-designed provenance warning banner and clean time-series charts.
- **Mathematical Issues**: Discrete-time queue dynamics $Q(t+\Delta t) = \max(0, Q(t) + A(t) - D(t))$ are algebraically verified.
- **Data Issues**: Explicitly tagged as calibrated simulation, not field sensor counts.
- **Visualization Issues**: Visualizations are limited to 2D line charts and summary tables. There is no spatial heat map or bubble map showing which intersections across the corridor experience queue spillback.
- **Bugs Verified**: None (simulation cache hash invalidation verified).
- **Missing Functionality**: GIS spatial bubble layer where node circle radii and colors dynamically scale with simulated queue length.
- **Improvements**: Add a corridor GIS map showing spatial queue hotspots.
- **Priority**: **MEDIUM**

---

### Page 9: Analytics, Benchmarking & Sensitivity Analysis (`pages/9_Analytics.py`)
- **Current Functionality**: Evaluates Scenario A (Baseline), Scenario B (Optimized), and Scenario C (Sensitivity stress testing +10% to +30%), tracking bottleneck migration and system cost elasticity $dZ/d\lambda$.
- **UI/UX Issues**: High data density with clean tables and charts.
- **Mathematical Issues**: Elasticity calculations and stress scaling are theoretically sound.
- **Data Issues**: Clear provenance.
- **Visualization Issues**: Bottleneck migration is reported in a data table and bar chart, but not mapped geospatially to show how saturation shifts across Bengaluru's arterial corridors.
- **Bugs Verified**: None.
- **Missing Functionality**: Spatial bottleneck migration map showing color transitions of road links under +10%, +20%, and +30% demand surges.
- **Improvements**: Add an interactive GIS layer visualizing bottleneck migration across corridors.
- **Priority**: **LOW to MEDIUM**

---

### Page 10: Operations Research Methodology & Proofs (`pages/10_Methodology.py`)
- **Current Functionality**: Comprehensive theoretical derivations, primal-dual formulations, optimality criteria, 4-model coupling feedback diagram, assumptions, and scholarly references.
- **UI/UX Issues**: Excellent academic presentation with LaTeX equations.
- **Mathematical Issues**: None. Formulations are mathematically rigorous and complete.
- **Data Issues**: None.
- **Visualization Issues**: None (theoretical documentation page).
- **Bugs Verified**: None.
- **Missing Functionality**: GIS road-network mathematical modeling documentation (WGS84 projection, OpenStreetMap node-edge bijection, Euclidean vs network distance impedance).
- **Improvements**: Add a section detailing GIS network graph construction and spatial impedance calibration.
- **Priority**: **LOW**

---

## 3. AUDIT DEFECT & IMPROVEMENT SUMMARY MATRIX

| Page / Component | Module Focus | Defect / Limitation | Impact Classification | Required Upgrade |
| :--- | :--- | :--- | :--- | :--- |
| `pages/3_Network_Visualization.py` | Macro Network Topology | Abstract Cartesian scatter; straight-line edges across buildings; no map tiles. | **CRITICAL** | Real OpenStreetMap street geometry, Folium/Leaflet layer controls, clickable junction popups. |
| `pages/5_Minimum_Cost_Flow.py` | Model 2: Min Cost Flow | Complete absence of spatial network visualization; purely tabular results. | **CRITICAL** | Interactive GIS map rendering Network Simplex flow distribution, congestion layer ($v/c$), and origin/destination markers. |
| `pages/4_Maximum_Flow.py` | Model 1: Max Flow | Saturated bottleneck cuts rendered as abstract straight lines; city planners cannot locate road bottlenecks. | **HIGH** | Real map highlighting minimum-cut saturated edges in glowing red on actual OSM street curves. |
| `pages/6_Shortest_Path.py` | Model 3: Dijkstra Path | Route rendered as Euclidean straight line chords cutting across city blocks. | **HIGH** | Real street-following routing polyline with turn-by-turn waypoint popups. |
| `pages/2_Dataset_Explorer.py` | Ground Truth Explorer | Tabular view only; analysts cannot visually verify intersection coordinates against street imagery. | **HIGH** | Interactive OSM coordinate verification pane. |
| `pages/7_Signal_Optimization.py` | Model 4: Signal LP | Bar charts only; lacks spatial context of the intersection and its approach legs. | **MEDIUM** | Embedded mini-GIS map of junction approach legs. |
| `pages/8_Simulation_Centre.py` | Dynamic Simulation | 2D time series only; no spatial queue hotspot visualization. | **MEDIUM** | Corridor GIS queue bubble map. |
| `pages/1_Overview.py` | Corpus Audit | No spatial distribution of BTP police station signal clusters. | **MEDIUM** | Geospatial density map of BTP divisions. |
| `src/network/graph_builder.py` | Core Graph Engine | Haversine straight-line distance instead of OSM road geometry and network distances. | **CRITICAL** | Integrate OSM road network geometry layer with realistic road curvatures. |

---

## 4. VERIFICATION OF DEPENDENCIES & ENVIRONMENT

- `networkx`: 3.7 (Installed & Verified)
- `scipy`: 1.18.1 (Installed & Verified)
- `pulp`: 4.2.0 (Installed & Verified)
- `plotly`: 7.1.0 (Installed & Verified)
- `pydeck`: 0.9.3 (Installed & Verified)
- `streamlit`: 1.66.1 (Installed & Verified)
- `folium`: 1.0.0 (Installed & Verified)
- `streamlit-folium`: 0.27.4 (Installed & Verified)
- `branca`: 0.8.2 (Installed & Verified)

All unit tests pass: **23 of 23 unit tests passing in 8.55s**.
Working tree is clean; local Git repository is preserved. Strict no-remote-push rules remain active.
