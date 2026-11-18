# NETWORK MODEL DOCUMENTATION: GRAPH ARCHITECTURE & CORRIDORS
## Bengaluru Smart Traffic Optimizer

---

## 1. Network Hierarchy: Two-Level Graph Representation

The road network is modeled using NetworkX across two distinct topological levels:

### 1.1 Level 1: Macro-Junction Graph $G_{\text{macro}} = (V_{\text{macro}}, E_{\text{macro}})$
- **Nodes $V_{\text{macro}}$**: Physical signalized intersections across Bengaluru (e.g., Adugodi Junction, Aishwarya Junction, Dairy Circle, Sony World Junction).
- **Edges $E_{\text{macro}}$**: Directed arterial and collector road links connecting adjacent intersections.
- **Attributes on $V_{\text{macro}}$**:
  - `name`: Official intersection title.
  - `police_station`: Police station jurisdiction.
  - `control_type`: Signal controller mode (`FIXED`, `VAC`, `SYNC`).
  - `cycle_time`: Operating cycle duration (s).
  - `pos`: Coordinate tuple $(x, y)$ or $(\text{longitude}, \text{latitude})$ for spatial projection.
- **Attributes on $E_{\text{macro}}$**:
  - `road_name`: Connecting corridor name (e.g., Hosur Road, 100 Ft Road, Mysore Road).
  - `lanes`: Lane count in the travel direction.
  - `length_m`: Distance in meters between the intersection centers.
  - `free_flow_speed`: Urban arterial design speed (km/h).
  - `physical_capacity`: Saturation flow limit of the road cross-section (PCU/hr).
  - `effective_capacity`: Signal-gated capacity $u_{ij}^{\text{eff}}$ dictated by downstream green allocation.
  - `cost`: Generalized travel time / impedance $c_{ij}$ in minutes.

### 1.2 Level 2: Micro-Movement Turning Graph $G_{\text{micro}} = (V_{\text{micro}}, E_{\text{micro}})$
- **Nodes $V_{\text{micro}}$**: Approach lanes and internal intersection conflict points.
- **Edges $E_{\text{micro}}$**: Permitted directional turning movements:
  - Left-turn slip / movement ($L$)
  - Through / Straight movement ($S$)
  - Right-turn movement ($R$)
  - U-turn movement ($U$)
- **Signal Control Mapping**:
  - Each micro-edge $e \in E_{\text{micro}}$ is linked to its controlling signal phase $p \in P_j$ from `signal_phases.csv`.
  - Conflicting movements (e.g., opposing right turns and through flows) are governed by non-overlapping phase sequences.

---

## 2. Selected Bengaluru Arterial Corridors

To ensure academic and practical realism without creating false arbitrary links between disparate parts of the city, the system models real contiguous Bengaluru corridors documented in the 118 PDFs:

### 2.1 Corridor 1: Koramangala – Adugodi – Wilson Garden (South-Central Corridor)
- **Anchor Intersections**:
  1. `Adugodi Junction` (Hosur Laskar Rd $\times$ New Mico Rd)
  2. `Aishwarya Junction` (7th Main, 1st Block Koramangala)
  3. `Jaipuria Junction` (Madiwala / BDA Jn $\times$ Sony World $\times$ 8th Main)
  4. `Dairy Circle Junction` (Mico Layout / Wilson Garden connector)
  5. `BMTC Junction (K.H. Road)` (Wilson Garden PS)
- **Network Role**: Major arterial connecting South Bengaluru IT corridor (Electronic City / Koramangala) with Central Business District (CBD). Characterized by high directional tidal flow during peak hours.

### 2.2 Corridor 2: Indiranagar – Old Madras Road (East Corridor)
- **Anchor Intersections**:
  1. `B.M. Shri Junction` (CMH Road $\times$ 100 Ft Road)
  2. `CMH Road - Double Road Junction` (Adarsha $\times$ BM Shree $\times$ ESI)
  3. `Old Madras Road & Double Road (PS Junction)`
  4. `BEML Gate Junction` (Suranjan Das Road)
  5. `Big Bazaar Junction` (Pharmed Factory Jn)
- **Network Role**: Critical east-west arterial linking CBD, Indiranagar commercial hub, and KR Puram / Whitefield.

### 2.3 Corridor 3: Mysore Road – Byatarayanapura (West Corridor)
- **Anchor Intersections**:
  1. `Rajarajeshwari Junction` (Bangalore University $\times$ BHEL)
  2. `Satellite Bus Stand Junction` (Mysore Road $\times$ Majestic/Market)
  3. `Nayandahalli / Ring Road Junction`
- **Network Role**: Heavy inter-city transit and bus corridor connecting Southwest Karnataka into Bengaluru City Market and Majestic transit terminals.

### 2.4 Corridor 4: Outer Ring Road – KR Puram – Marathahalli (IT Corridor)
- **Anchor Intersections**:
  1. `Doddanekundi Junction` (Doddanekundi $\times$ Ring Road)
  2. `Marathahalli Multiplex / Bridge Junction`
  3. `Garudacharpalya Junction`
- **Network Role**: Multi-lane circumferential expressway with severe weaving and bottleneck congestion.

---

## 3. Geographical Road Verification Rules

To satisfy Section 5 guidelines:
1. **No Phantom Connectivity**: Two junctions appearing in the same PDF sheet are evaluated for physical proximity; they are NOT automatically connected unless an actual roadway links them.
2. **True Distance Calibration**: Road segment distances $L_{ij}$ are calibrated using OpenStreetMap road network geometry across Bengaluru.
3. **Capacity Standardization (IRC:106-1990)**:
   - 2-lane two-way urban road: ~1,500 PCU/hr total.
   - 4-lane divided urban arterial: ~1,200 PCU/hr/lane (2,400 PCU/hr per direction).
   - 6-lane divided urban arterial: ~1,200 PCU/hr/lane (3,600 PCU/hr per direction).
   - Approach lane saturation flow $s_{ij}$: 1,800 PCU/hr of green per lane.
