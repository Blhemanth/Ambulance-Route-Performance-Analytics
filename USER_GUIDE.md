# USER GUIDE & EVALUATOR MANUAL
## Interactive GIS Ambulance Route Optimization Application — Bengaluru

**Academic Topic:** Ambulance Route Optimization  
**Geographical Scope:** Bengaluru Metropolitan Area, Karnataka, India  
**Target Audience:** Academic Evaluators, GIS Engineers, Operations Research Specialists & Transport Researchers  

---

### 1. Application Startup & Quickstart

To launch the local interactive web application, open a terminal in the project directory and execute:

```bash
python -m streamlit run app.py
```

The application will start the local web server and automatically open your default browser at:
`http://localhost:8501`

---

### 2. Page Navigation & Workflow Guide

The application features an intuitive categorized sidebar navigation enabling seamless traversal between modules:

```
Ambulance Routing System
├── 🏛️ Operations Dashboard              (app.py)
├── 🚑 01. Route Optimizer               (pages/6_Shortest_Path.py)
├── 🗺️ 02. Road Network Explorer         (pages/3_Network_Visualization.py)
├── 🏥 03. Hospital Finder & Snapping    (pages/11_Hospital_Validation.py)
├── 📈 04. Performance Analytics         (pages/9_Analytics.py)
├── 📊 05. Corpus & Geometry             (pages/1_Overview.py)
├── 📑 06. Signal Plan Explorer          (pages/2_Dataset_Explorer.py)
└── 📜 07. Formulations & Proofs         (pages/10_Methodology.py)
```

---

### 3. Step-by-Step User Instructions

#### 3.1 Executing an Optimal Ambulance Route
1. Navigate to **01. Route Optimizer** (`pages/6_Shortest_Path.py`).
2. **Choose Ambulance Origin:**
   - *Option A (Strategic Hubs):* Select a major dispatch hub (e.g. "Majestic KSR Railway Station Core", "Silk Board Arterial Hub").
   - *Option B (Searchable Junction):* Choose from any of the 226 geocoded arterial intersections.
   - *Option C (Manual Coordinates):* Enter latitude and longitude coordinates; the system snaps to the nearest network node.
3. **Choose Destination Hospital:**
   - Filter by triage tier: "🟢 Verified Emergency Trauma Centers", "🔵 Probable Emergency Tertiary", or "All Healthcare Facilities".
   - Select a receiving hospital (e.g., "Victoria Hospital", "St. John's Medical College Hospital", "Bowring and Lady Curzon Hospitals").
4. **Configure Routing Parameters:**
   - **Routing Objective:** Select *Minimum Estimated Time (IRC:106)* or *Shortest Distance (km)*.
   - **Alternative Routes (Yen's K):** Adjust slider between $K=1$ and $5$ (default $3$).
5. **Click "🚀 Calculate Optimal Ambulance Route":**
   - View the interactive GIS route map.
   - The **Primary Optimal Route** is traced in vibrant **Cyan / Blue** (`#06B6D4`).
   - **Alternative Routes** are highlighted in **Orange** (`#F97316`) and **Purple** (`#A855F7`).
6. **Inspect Results:**
   - Review primary metrics (Estimated Travel Time, Total Road Distance, Average Speed, Driveway Penalty).
   - Switch to the **Alternative Routes Tab** to evaluate time deltas (+min and %) and divergence points.
   - Switch to the **Time vs Distance Tab** to evaluate speed-distance tradeoffs.
   - Switch to the **Turn-by-Turn Tab** to view exact street names, speeds, segment times, and approximate cardinal headings. Click **"Download Itinerary (CSV)"** to save.

#### 3.2 Finding & Routing to a Hospital
1. Navigate to **03. Hospital Finder & Snapping** (`pages/11_Hospital_Validation.py`).
2. In the search box, type any hospital name (e.g., "Victoria", "Manipal", "Apollo", "St. John's", "Baptist").
3. Inspect the facility profile card: verified emergency status, OSM ID, address, coordinates, and road connection distance.
4. Click **"🚑 Open in Ambulance Route Optimizer"**: the selected hospital is automatically transferred to the Route Optimizer page as the target destination.

#### 3.3 Exploring the Road Network
1. Navigate to **02. Road Network Explorer** (`pages/3_Network_Visualization.py`).
2. Filter the network by **Arterial Corridor** (Corridors 1–5 or Central).
3. Filter by **Road Classification** (Expressways 50 km/h, Major Arterials 40 km/h, Sub-Arterials 35 km/h, Collectors 30 km/h).
4. Use the **Hospital Proximity Focus** selector to view all road links within 3.5 km of key trauma hospitals.
5. Search the **Road Segment Catalog** tab to look up any street name, capacity, and one-way flow constraint.

#### 3.4 Launching One-Click Scenarios from Dashboard
1. Navigate to the **Operations Dashboard** (`app.py`).
2. Under **Quick Emergency Dispatch Scenarios**, click any of the 4 scenario buttons:
   - *Central Core Dispatch* (Majestic $\to$ Victoria Hospital)
   - *South-East Corridor* (Koramangala $\to$ St. John's)
   - *South Arterial Ring* (Silk Board $\to$ Aster RV Hospital)
   - *East Shivaji Nagar Core* (Indiranagar $\to$ Bowring Hospital)
3. The application instantly pre-fills the route optimizer parameters and computes the optimal route.

---

### 4. Interactive Map Legend Guide

| Map Element | Visual Style | Meaning |
| :--- | :--- | :--- |
| **Ambulance Origin** | 🟢 Green Marker (`🚑`) | Dispatch unit departure intersection |
| **Hospital Destination** | 🔴 Red Cross Marker (`🏥`) | Receiving emergency medical trauma center |
| **Primary Route** | ━━ Solid Cyan Polyline (`#06B6D4`) | Global minimum estimated travel-time route |
| **Alternative 1** | ┅┅ Dashed Orange Polyline (`#F97316`) | Yen's Rank 2 loopless alternative route |
| **Alternative 2** | ┅┅ Dashed Purple Polyline (`#A855F7`) | Yen's Rank 3 loopless alternative route |
| **Road Centerlines** | ── Thin Slate Grey (`#64748B`) | Directed arterial street network |
| **Campus Driveway** | ┅┅ Dashed Red Line (`#DC2626`) | Campus access connector ($15\text{ km/h} + 1.0\text{ min}$ gate delay) |

> **Evaluator Note:** Route colors denote mathematical path selections (Primary vs. Alternatives) and do NOT imply real-time congestion or live traffic conditions.

---

### 5. Known Limitations & Research Boundaries

1. **Static Speed Model:** Travel times are computed using deterministic Indian Road Congress (IRC:106-1990) urban speed standards and physical distance measurements. Live GPS vehicle telemetry and dynamic traffic API feeds are excluded in compliance with the strict Phase 3 boundary.
2. **Driveway Approximation:** Campus driveway access delays are modeled using perpendicular Euclidean snapping distance at $15\text{ km/h}$ plus a calibrated $1.0\text{ min}$ security gate delay. Actual campus internal geometries vary by hospital.
3. **Field Validation:** Calculated response times represent theoretical algorithmic bounds. Real-world emergency response times require empirical fleet validation.
