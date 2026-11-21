# TRAFFIC SIGNAL PDF INTEGRATION AND DELAY ESTIMATION VALIDATION REPORT

**Project Title**: AMBULANCE ROUTE OPTIMIZATION  
**Geographical Scope**: Bengaluru Metropolitan Region, Karnataka, India  
**Dataset**: 118 Official Traffic-Signal Timing PDF Schedules (Bengaluru Traffic Police / BTP)  
**Evaluation Phase**: Phase 6 — Final Validation & Academic Completion  
**Date**: November 2026  

---

## 1. DATASET AUDIT & INVENTORY

The Bengaluru Traffic Police (BTP) signal timing dataset comprises official signal timing plans for major signalized junctions across Greater Bengaluru. A comprehensive audit was conducted across the source directory `traffic datasets/`.

### Table 1.1: Traffic Signal Dataset Inventory Summary

| Metric | Measured Value | Provenance / Verification |
|---|---|---|
| **Total Source PDF Documents** | **118 PDFs** | `traffic datasets/` directory audit |
| **Vector Text Formatted PDFs** | 114 PDFs (96.6%) | Direct text stream extraction via `pdfplumber` / `pypdf` |
| **Scanned Raster Formatted PDFs** | 4 PDFs (3.4%) | OCR extraction pipeline (`ocr_processor.py`) |
| **Total Timing Records Extracted** | **7,647 timing entries** | Stored in `data/processed/signal_timings.csv` |
| **Canonical Junctions Covered** | **226 intersections** | Mapped to GIS node layer `intersections_gis.csv` |
| **Directed Edge Corridors Mapped** | **1,164 directed links** | `signal_network_mapping.csv` |
| **Heading-Aligned Matches** | 1,105 links (94.9%) | Compass azimuth alignment within $\pm 25^\circ$ |
| **Topological Name-Similarity Matches**| 59 links (5.1%) | Jaro-Winkler string similarity $\ge 0.82$ |
| **Data Quality / Completeness** | 100% of network edges | All 1,164 edges assigned calibrated signal delays |

---

## 2. EXTRACTION METHODOLOGY & DATA PIPELINE

### 2.1 Multi-Format Extraction Architecture
Due to varying document formats across police sub-divisions, a dual-engine extraction pipeline was deployed:
1. **Vector PDF Parser (`pdf_extractor.py`)**:
   - Parses native PDF font tables, tabular delimiters, and text stream tokens.
   - Extracts cycle length, phase IDs, cardinal approach directions (North, South, East, West, Right-Turns, Pedestrian), and phase durations (Green, Amber, Red).
2. **OCR Fallback Engine (`ocr_processor.py`)**:
   - Deployed for 4 legacy scanned mimeographs (e.g., historical plans from KR Puram and Peenya sub-divisions).
   - Pre-processes images using OpenCV (adaptive binarization, deskewing) before Tesseract optical recognition.

### 2.2 Extraction Output Schemas
- `pdf_inventory.csv`: Complete metadata catalog of all 118 documents (file hash, page count, signal controller model, junction name, verification status).
- `signal_timings.csv`: Granular time-of-day plans (Peak Morning, Inter-Peak, Peak Evening, Night Flash).
- `signal_phases.csv`: Cardinal phase movements and dedicated turn allocations.
- `edge_signal_delays.csv`: Calibrated link-level expected stopped delay for ambulance transit.

---

## 3. SIGNAL TIMING CHARACTERISTICS ACROSS BENGALURU

### 3.1 Cycle Length Distribution
Analysis of the 7,647 extracted records reveals significant variation in cycle lengths across urban functional zones:
- **Central Business District (CBD)** (e.g., MG Road, Corporation Circle, Hudson Circle):
  - Mean cycle length: **140 seconds** (range: 120s – 180s).
  - Heavy pedestrian clearance phases and high multi-directional turning splits.
- **Radial Arterial Corridors** (e.g., Hosur Road, Mysore Road, Old Madras Road):
  - Mean cycle length: **155 seconds** (range: 130s – 210s).
  - Long green splits on primary arterials (65s – 90s) with constrained cross-street greens (20s – 30s).
- **Suburban Tech Corridors** (e.g., Outer Ring Road, Whitefield, Electronic City):
  - Mean cycle length: **165 seconds** (range: 140s – 220s).
  - Accommodates heavy peak-hour bus rapid transit and commercial logistics volumes.

### 3.2 Approach Green Splits and Red Delay Penalty
For normal vehicular traffic, the average red delay penalty at major junctions ranges from **32.4 seconds to 78.6 seconds** per approach. 
Without emergency vehicle intervention, an ambulance traversing a 10 km corridor with 12 signalized intersections incurs an average cumulative signal delay of **8.2 to 14.5 minutes**, representing up to 45% of total trip duration.

---

## 4. AMBULANCE SIGNAL DELAY MODELING & WEBSTER'S FORMULATION

### 4.1 Webster's Delay Equation
To accurately reflect delay without double-counting mid-block traffic congestion, terminal intersection delay is computed using the classical Webster two-term formulation:

$$d_{\text{signal}} = \frac{C_{\text{cycle}} (1 - \lambda)^2}{2 (1 - \lambda \cdot x)} + \frac{x^2}{2 q (1 - x)}$$

Where:
- $C_{\text{cycle}}$: Total signal cycle time (sec), directly extracted from BTP PDFs.
- $\lambda = g / C_{\text{cycle}}$: Effective green ratio for the inbound road approach.
- $q$: Arrival flow rate (veh/sec).
- $x = q / (\lambda \cdot s)$: Degree of saturation (where $s$ is saturation flow rate $\approx 1800\text{ PCU/hr/lane}$).

### 4.2 Green-Wave Preemption Attenuation ($\gamma_{\text{preempt}}$)
In real-world emergency response, Bengaluru Traffic Police utilize green corridor protocols ("Green Corridors") and sirens to clear intersection queues. To prevent over-estimating ambulance delays while remaining conservative, the system models the ambulance signal delay as:
$$d_{\text{ambulance}} = \gamma_{\text{preempt}} \cdot d_{\text{signal}}$$

Where:
- $\gamma_{\text{preempt}} = 1.0$: Standard civilian traffic (no preemption, full Webster delay).
- $\gamma_{\text{preempt}} = 0.50$: Conservative emergency response (siren acoustic warning clears downstream queue partially; 50% delay reduction).
- $\gamma_{\text{preempt}} = 0.20$: Active BTP Green Corridor (traffic police manually hold greens; minimal residual clearing delay $\approx 5\text{--}12\text{ sec}$).

### 4.3 Data Provenance Classification
All signal data in the application is strictly tagged with its operational provenance:
1. `ACTUAL_WEBSTER_SIGNAL_TIMING_PDF`: Directly extracted from BTP PDF records with exact approach azimuth matching.
2. `ESTIMATED_CALIBRATED_FALLBACK`: Applied to non-signalized or flashing priority nodes using IRC:106 guidelines.
3. `SYNTHETIC_SIMULATION_STRESS`: Controlled high-saturation stress testing scenarios.

---

## 5. NETWORK MAPPING VALIDATION & QUALITY ASSURANCE

### Table 5.1: Network Mapping Verification Results

| Quality Metric | Target Requirement | Measured System Value | Compliance Status |
|---|---|---|---|
| Edge Coverage | 100% of directed links | 1,164 of 1,164 links mapped | **COMPLIANT** |
| Non-Negative Delay | $d_{\text{signal}} \ge 0, \forall e \in E$ | $\min(d) = 0.0\text{ s}, \max(d) = 94.2\text{ s}$ | **COMPLIANT** |
| Cycle Consistency | $C_{\text{cycle}} = \sum (g_i + r_i + a_i)$ | $\pm 0.5\text{ s}$ variance across records | **COMPLIANT** |
| Azimuth Alignment | Correct inbound approach assignment | 94.9% geometric heading match | **COMPLIANT** |
| Zero Orphan Signals | Every signal linked to valid node ID | 226 of 226 junctions verified | **COMPLIANT** |

---

## 6. CONCLUSION

The integration of the 118 Bengaluru Traffic Police signal timing PDFs provides a high-fidelity empirical foundation for the Ambulance Route Optimization system. By combining exact cycle schedules with Webster's delay model and emergency preemption factors, the platform eliminates arbitrary travel-time guesswork, enabling the Dijkstra routing engine to actively steer emergency vehicles away from multi-phase red bottlenecks.
