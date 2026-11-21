# HOSPITAL NETWORK SNAPPING REPORT
## PHASE 1: SPATIAL ACCESS MATCHING, DISTANCE CALIBRATION, AND THRESHOLD AUDIT
### Project: Ambulance Route Optimization — Bengaluru, Karnataka

**Document Version:** 1.0.0 (Phase 1 Engineering Report)  
**Date:** 2026-11-20  
**Author:** Senior GIS Engineer, Operations Research Specialist & Testing Engineer  
**Workspace:** `b:\Ambulance Route Optimization`  
**Road Network Input:** `data/processed/intersections_gis.csv` (226 nodes) & `roads_gis.json` (1,164 directed edges)  
**Hospital Input:** `data/processed/bengaluru_hospitals.csv` (1,084 facilities)  
**Processed Output:** `data/processed/hospital_road_connections.csv` (1,084 records, 18 columns)  

---

## 1. EXECUTIVE SUMMARY

In Phase 1, spatial network snapping was implemented ([src/network/hospital_snapper.py](file:///b:/Ambulance%20Route%20Optimization/src/network/hospital_snapper.py)) to map 1,084 Bengaluru hospital facilities onto candidate road network access points without fabricating fictitious straight-line vehicle paths.

### Key Snapping Results (2,000-Meter Threshold)
- **Total Facilities Evaluated**: 1,084
- **Successfully Matched ($\le 2,000\text{ m}$)**: **750 facilities (69.2%)**
- **Unmatched / Exceeds Threshold ($> 2,000\text{ m}$)**: **334 facilities (30.8%)**
- **Direct Gate Proximity ($\le 300\text{ m}$)**: **258 facilities (23.8%)**
- **Estimated Corridor Proximity ($300\text{ m} - 1,000\text{ m}$)**: **317 facilities (29.2%)**
- **Estimated Distant Access ($1,000\text{ m} - 2,000\text{ m}$)**: **175 facilities (16.1%)**
- **Mean Snapping Distance (All Facilities)**: 1,732.7 meters
- **Median Snapping Distance (All Facilities)**: 887.8 meters

---

## 2. SPATIAL MATCHING ALGORITHM & FORMULATION

### 2.1 Candidate Search Formulation
Given a hospital coordinate $H = (\text{lat}_H, \text{lon}_H)$ and the directed road graph $G = (V, E)$:

1. **Intersection Candidate Search**:
   Compute great-circle distance $d(H, v)$ to each intersection node $v \in V$:
   $$d_{\text{node}} = \min_{v \in V} \text{Haversine}(H, v)$$

2. **Perpendicular Road Polyline Projection**:
   For each directed road edge $e = (u, v) \in E$ with waypoint coordinates $(w_1, w_2, \dots, w_k)$:
   Compute the perpendicular Euclidean distance from $H$ to each line segment $(w_i, w_{i+1})$ using equirectangular projection:
   $$x = (\text{lon}_H - \text{lon}_{w_i}) \cos\left(\frac{\text{lat}_H + \text{lat}_{w_i}}{2}\right) \cdot k_x, \quad y = (\text{lat}_H - \text{lat}_{w_i}) \cdot k_y$$
   Find the projected point $P_e$ clamped to segment endpoints:
   $$t^* = \max\left(0, \min\left(1, \frac{\mathbf{HP} \cdot \mathbf{AB}}{\|\mathbf{AB}\|^2}\right)\right)$$
   $$d_{\text{edge}} = \min_{e \in E} \|H - P_e\|_2$$

3. **Primary Connector Selection**:
   The primary snapping distance is chosen as:
   $$d_{\text{snap}} = \min(d_{\text{node}}, d_{\text{edge}})$$
   Where $d_{\text{edge}} \le d_{\text{node}}$, the road polyline projection point $(\text{lat}_{\text{proj}}, \text{lon}_{\text{proj}})$ serves as the access point, avoiding unnecessary detours to distant intersection centroids.

---

## 3. TIERED CONNECTION CLASSIFICATION

Hospitals are classified into four connection tiers based on proximity and confidence:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   SNAPPING DISTANCE CLASSIFICATION                     │
├──────────────────────┬───────────────────────┬─────────────────────────┤
│ Tier                 │ Distance Range        │ Status Label            │
├──────────────────────┼───────────────────────┼─────────────────────────┤
│ Direct Proximity     │ d <= 300 meters       │ DIRECT_GATE_PROXIMITY   │
│ Corridor Access      │ 300 < d <= 1,000 m    │ ESTIMATED_CORRIDOR      │
│ Distant Access       │ 1,000 < d <= 2,000 m  │ ESTIMATED_DISTANT       │
│ Unmatched            │ d > 2,000 meters      │ UNMATCHED_EXCEEDS       │
└──────────────────────┴───────────────────────┴─────────────────────────┘
```

### Empirical Breakdown Across All 1,084 Facilities:

| Connection Status | Snapping Distance | Count | Percentage | Operational Guidance |
| :--- | :--- | :--- | :--- | :--- |
| **`DIRECT_GATE_PROXIMITY`** | $\le 300\text{ m}$ | **258** | 23.8% | High confidence. Immediate direct ambulance entry to arterial link. |
| **`ESTIMATED_CORRIDOR_PROXIMITY`** | $301\text{ m} - 1,000\text{ m}$ | **317** | 29.2% | Moderate confidence. Requires local street / driveway traversal to reach arterial network. |
| **`ESTIMATED_DISTANT_ACCESS`** | $1,001\text{ m} - 2,000\text{ m}$ | **175** | 16.1% | Low confidence. Substantial local road transit required before reaching arterial intersection. |
| **`UNMATCHED_EXCEEDS_THRESHOLD`** | $> 2,000\text{ m}$ | **334** | 30.8% | Unmatched. Facility is in outer suburban zone; cannot be reached on arterial network alone. |

---

## 4. VERIFIED EMERGENCY HOSPITAL MATCHING AUDIT

A dedicated analysis was conducted on the **103 verified emergency and trauma facilities** (`VERIFIED_EMERGENCY`):

| Connection Tier | Count | Percentage | Example Facilities |
| :--- | :--- | :--- | :--- |
| **Direct Proximity ($\le 300\text{m}$)** | 22 | 21.4% | Sanjay Gandhi Accident & Trauma (32.6m), Apollo Jayanagar (92.4m), Victoria Hospital (115.8m), Bowring Hospital (142.1m) |
| **Estimated Corridor ($300\text{m} - 1,000\text{m}$)** | 26 | 25.2% | Manipal Hospital Old Airport Rd (422.5m), M. S. Ramaiah Memorial (612.3m), NIMHANS (780.4m) |
| **Estimated Distant ($1,000\text{m} - 2,000\text{m}$)** | 13 | 12.6% | St. John's Medical College Hospital (1,184.7m), Fortis Hospital Cunningham Rd (1,452.1m) |
| **Exceeds Threshold ($> 2,000\text{m}$)** | 42 | 40.8% | Narayana Health City (Bommasandra, 8.2km), Columbia Asia Whitefield (6.8km), Aster CMI Sahakarnagar (3.8km) |

### Explanation of Unmatched Facilities:
The 42 verified emergency centers exceeding the 2,000m threshold are located in Greater Bengaluru's outer suburban and IT corridors (Whitefield, Electronic City / Bommasandra, Yelahanka North, Kengeri, and Hoskote). 

The legacy BEL engineering dataset focused on the 226 inner-city signalized intersections. This finding demonstrates why the OSM Southern Zone road network (Dataset A) will be essential in Phase 2 to supply secondary and suburban arterial links for peripheral trauma centers.

---

## 5. DRIVEWAY ACCESS PENALTY MODEL

To avoid unrealistic instantaneous arrival, an access delay model is incorporated for the connector link between the arterial road and the hospital emergency bay:
$$t_{\text{access}} = \frac{d_{\text{snap}}}{1000.0} \times \frac{60}{v_{\text{driveway}}} + t_{\text{barrier}} \quad \text{(minutes)}$$
where:
- $v_{\text{driveway}} = 15.0\text{ km/h}$ (cautious ambulance maneuvering through hospital gates, campus driveways, and pedestrian zones).
- $t_{\text{barrier}} = 1.0\text{ minute}$ (security barrier clearance, ambulance bay docking).

For example:
- Sanjay Gandhi Trauma Hospital ($d = 32.6\text{ m}$): $t_{\text{access}} = 1.13\text{ minutes}$.
- Manipal Hospital Old Airport Rd ($d = 422.5\text{ m}$): $t_{\text{access}} = 2.69\text{ minutes}$.
- St. John's Hospital ($d = 1,184.7\text{ m}$): $t_{\text{access}} = 5.74\text{ minutes}$.

---

## 6. SPATIAL VALIDATION VIEW IMPLEMENTATION (TASK 5)

A dedicated, interactive Streamlit validation page has been created at [pages/11_Hospital_Validation.py](file:///b:/Ambulance%20Route%20Optimization/pages/11_Hospital_Validation.py).

Features:
1. **Interactive Folium Validation Map**:
   - Color-coded markers: Green (Verified Emergency), Blue (Probable Tertiary), Amber (General Unverified), Red (Unmatched).
   - Dashed connector links visually tracing the perpendicular access line to the road edge.
   - Interactive popups with hospital identity, nearest junction ID, snapping distance, and access delay.
2. **Dynamic Threshold Slider**: Users can dynamically vary the snapping threshold from 500m to 5,000m and watch matched vs unmatched counts update in real time.
3. **Diagnostic Data Tabs**:
   - Matched Catalog table with sorting by distance.
   - Unmatched Facilities table highlighting suburban hospitals requiring secondary network expansion.
   - Quality audit breakdown.

---

## 7. UNIT TEST VERIFICATION (TASK 7)

All 8 tests in [tests/test_network_snapping.py](file:///b:/Ambulance%20Route%20Optimization/tests/test_network_snapping.py) passed:
- `test_point_to_segment_distance`: Equirectangular projection perpendicular distance verified.
- `test_road_node_matching`: Valid candidate intersection node IDs (`INT_xxx`) matched.
- `test_snapping_distance_accuracy`: Snapping distance strictly matches $\min(d_{\text{node}}, d_{\text{edge}})$.
- `test_maximum_snapping_threshold`: Threshold filter properly categorizes connections $> 2000\text{m}$.
- `test_unmatched_hospital_handling`: Unmatched / invalid records handled without exceptions.
- `test_hospital_to_road_identifier_consistency`: Matched node IDs exist in the 226 intersection catalog.
- `test_access_penalty_time`: Driveway access time calculation strictly positive ($\ge 1.0\text{ min}$).
- `test_connection_output_file`: `hospital_road_connections.csv` verified with all 1,084 records.
