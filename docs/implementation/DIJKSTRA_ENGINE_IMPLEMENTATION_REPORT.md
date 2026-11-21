# DIJKSTRA ROUTING ENGINE IMPLEMENTATION REPORT
## PHASE 2: MINIMUM TRAVEL-TIME OPTIMIZATION & DIRECTED GRAPH FORMULATION
### Project: Ambulance Route Optimization — Bengaluru, Karnataka

**Document Version:** 1.0.0 (Phase 2 Engineering Report)  
**Date:** 2026-11-20  
**Author:** Senior Python Developer, Operations Research Specialist & GIS Engineer  
**Workspace:** `b:\Ambulance Route Optimization`  
**Core Modules:**  
- `src/network/ambulance_graph.py` (Directed road graph & IRC:106 speed calibration)  
- `src/network/ambulance_router.py` (Core Dijkstra engine, profiles, and hospital integration)  

---

## 1. MATHEMATICAL FORMULATION & OBJECTIVE FUNCTION

### 1.1 Problem Representation
The Bengaluru urban arterial network is modeled as a directed, weighted multi-graph:
$$\mathcal{G} = (\mathcal{V}, \mathcal{E})$$
where:
- $\mathcal{V}$: set of 226 geocoded road intersections and hospital entry nodes.
- $\mathcal{E}$: set of 1,164 directed road segments $(i, j)$ with unique identifiers and geometries.
- $w_{ij} \ge 0$: nonnegative estimated traversal cost (travel time in seconds or length in meters).

### 1.2 Binary Integer Linear Programming (ILP) Formulation
$$\text{Minimize } Z = \sum_{(i,j) \in \mathcal{E}} w_{ij} \cdot x_{ij}$$
subject to standard shortest-path flow conservation constraints:
$$\sum_{j:(i,j) \in \mathcal{E}} x_{ij} - \sum_{j:(j,i) \in \mathcal{E}} x_{ji} = \begin{cases}
1 & \text{if } i = s \text{ (Ambulance Origin)} \\
-1 & \text{if } i = t \text{ (Destination Hospital Entrance)} \\
0 & \forall i \in \mathcal{V} \setminus \{s, t\} \text{ (Intermediate Intersections)}
\end{cases}$$
$$x_{ij} \in \{0, 1\} \quad \forall (i, j) \in \mathcal{E}$$

Because all link impedances $w_{ij} \ge 0$, this binary integer program is solved to exact polynomial-time global optimality in $\mathcal{O}(|\mathcal{E}| + |\mathcal{V}| \log |\mathcal{V}|)$ using **Dijkstra's Algorithm** with a min-priority binary heap.

---

## 2. TRAVEL-TIME EDGE WEIGHT FORMULATION (TASK 3)

### 2.1 Traversal Time Calculation
Link travel time in seconds is computed strictly from physical distance and validated speed:
$$t_{ij} = \left(\frac{d_{ij}}{v_{ij}}\right) \times 3600 \quad \text{(seconds)}$$
where:
- $d_{ij}$: road distance in kilometers (calculated from high-precision polyline coordinates via Haversine distance, with minimum bound $d_{ij} \ge 0.005\text{ km}$).
- $v_{ij}$: estimated vehicle operating speed in kilometers per hour.

### 2.2 Indian Road Congress (IRC:106-1990) Speed Classification
In the absence of proprietary commercial live traffic sensors, link speeds are calibrated based on official Indian Road Congress urban road classification and corridor lane capacity:

| Road Class | Characteristics & Bengaluru Examples | Speed ($v_{ij}$) | Speed Provenance |
| :--- | :--- | :--- | :--- |
| **Expressway / Highway** | Bellary Road, Outer Ring Road, NH44, Elevated Flyovers | **50.0 km/h** | `ESTIMATED_IRC106_EXPRESSWAY` |
| **Major Arterial** | Mysore Road, Hosur Road, 100ft Indiranagar, Double Road | **40.0 km/h** | `ESTIMATED_IRC106_ARTERIAL` |
| **Sub-Arterial / Collector** | CMH Road, Bannerghatta Main Road, Koramangala 80ft | **35.0 km/h** | `ESTIMATED_IRC106_SUB_ARTERIAL` |
| **Local Connector / Street** | Cross streets, Layout connectors, inner residential roads | **30.0 km/h** | `ESTIMATED_IRC106_COLLECTOR` |
| **Driveway / Gate Access** | Hospital campus access, barrier gates, ambulance bays | **15.0 km/h** | `CAMPUS_DRIVEWAY_CALIBRATED` |

### 2.3 Edge Weight Robustness & Sanitization
The graph builder ([src/network/ambulance_graph.py](file:///b:/Ambulance%20Route%20Optimization/src/network/ambulance_graph.py)) guarantees:
- Non-negativity: $\forall e \in \mathcal{E}, w_{ij} > 0$.
- Zero / negative speed guard: clamped to minimum $5.0\text{ km/h}$.
- Missing speed limit guard: defaulted to IRC:106 class speed.
- Distance sanity check: clamped to minimum $1.0\text{ meter}$.
- All costs, distances, speeds, and provenance strings are stored in separate independent attributes.

---

## 3. ROUTING COST PROFILES (TASK 7)

The routing engine supports three decoupled operational profiles:
1. **`MINIMUM_ESTIMATED_TIME` (Default)**:
   - Objective: Minimize estimated ambulance transit duration.
   - Weight attribute: `travel_time_sec`.
   - Prioritizes higher-speed expressways and arterial corridors to avoid bottleneck delays.
2. **`SHORTEST_DISTANCE` (Benchmark)**:
   - Objective: Minimize total physical odometer distance.
   - Weight attribute: `length_m`.
   - Serves as an academic baseline to quantify the speed-versus-distance tradeoff.
3. **`TIME_PLUS_SIGNAL_DELAY` (Future Phase Preparation)**:
   - Interface prepared: $w_{ij} = t_{ij} + d_j^{\text{signal}}$.
   - Kept disabled in Phase 2 in strict adherence to phase boundary rules.

---

## 4. SAMPLE ROUTE DEMONSTRATION & TRADE-OFF BENCHMARK

### 4.1 Sample Corridor Route
- **Origin**: `INT_003_ADUGODI_JUNCTION` (Adugodi / Mico Layout)
- **Destination**: `INT_006_RAJALAXMIKALYANAMANTAPA` (South End Circle / Jayanagar)
- **Optimal Trajectory**: 7 road segments through BMTC Jn $\to$ Kadubeesanahalli Jn $\to$ Swagat Main Rd $\to$ Konanakunte $\to$ Kanakapura Ring Rd.
- **Dijkstra Runtime**: **2.32 milliseconds**.
- **Metrics**: Total Travel Time = **11.85 minutes**, Total Distance = **7.903 km**, Average Speed = **40.0 km/h**.

### 4.2 Distance vs. Time Trade-Off Comparison
Evaluating `INT_001_RAJARAJESHWARI_JUNCTION` $\to$ `INT_013_HULIMAVU_JUNCTION`:
- **Minimum Travel Time Route**:
  - Distance: $8.967\text{ km}$
  - Travel Time: **$13.45\text{ minutes}$**
- **Shortest Distance Route**:
  - Distance: **$8.957\text{ km}$** (saves 10 meters)
  - Travel Time: $13.50\text{ minutes}$ (0.05 min / 3 seconds slower)
- **Trade-Off Finding**: The fastest route selects higher-speed 40 km/h arterial links, willingly adding 10 meters of distance to save transit time.

---

## 5. HOSPITAL & ORIGIN DISPATCH INTEGRATION (TASK 8)

The router seamlessly integrates Phase 1 hospital records and snapping connectors:
1. Origin input: Can be any intersection ID (`INT_xxx`) or GPS coordinate.
2. Hospital input: Matched by ID (`BLR_HOSP_xxxx`) or name substring (e.g., `"Sanjay Gandhi"`, `"Manipal"`, `"Victoria"`).
3. Road-network shortest path is solved to the hospital's verified entry junction.
4. An explicit **Campus Driveway Access Segment** is appended:
   - Distance: `snapping_distance_m` (from Phase 1).
   - Speed: $15.0\text{ km/h}$.
   - Time: $\frac{d_{\text{snap}}}{1000} \cdot \frac{60}{15.0} + 1.0\text{ min}$ (gate barrier delay).
5. Verification status (`VERIFIED_EMERGENCY`, `EMERGENCY_PROBABLE_UNVERIFIED`, etc.) is exposed directly in the output dictionary so callers never mistake unverified clinics for trauma centers.
