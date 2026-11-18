# DATASET DOCUMENTATION: BENGALURU TRAFFIC SIGNAL PLANS
## Academic & Technical Documentation

---

## 1. Overview & Provenance
The raw dataset comprises **118 original Bengaluru traffic signal timing and intersection geometry sheets** in PDF format, compiled from official signal design plans engineered by Bharat Electronics Limited (BEL) for the Bengaluru Traffic Police (BTP).

Each document contains:
- Intersection title and Traffic Police Station (TPS) jurisdiction.
- Signal controller operating mode (`FIXED`, `VAC` - Vehicle Actuated Control, or `SYNC` - Synchronized).
- Intersection schematic diagram showing approach legs, lane markings, controller placement, pole types (cantilever, primary with extender, pedestrian).
- Phase movement matrix detailing permitted directional movements (Left, Straight, Right, Pedestrian) per approach under each active signal phase.
- Time-of-Day (TOD) signal timing schedule tables detailing start and end times, green time allocations per phase, exclusive pedestrian intervals, and total cycle duration.

---

## 2. Audit & Technical Inventory
- **Total Files**: 118 PDF files.
- **Page Distribution**: 100% single-page engineering drawings (1 page each).
- **Format Breakdown**:
  - **114 Digital Vector CAD Sheets**: Contain selectable text, vector lines, and structured tabular grids. Yielded **259 individual junction timing tables**.
  - **4 Scanned Raster Sheets (3 unique intersections + 1 duplicate)**:
    1. `28f6fc64-6839-40b2-8f94-4e19daa98781.pdf` & duplicate `28f6fc64-6839-40b2-8f94-4e19daa98781 (1).pdf`: **Jaipuria Jn - Near Canara Bank** (Adugodi TPS).
    2. `73612825-0ee9-454a-a184-e30b5155f2fe.pdf`: **CMH Road - Double Road Junction** (Indiranagar TPS).
    3. `caebd006-7600-4f9f-bed3-f14fcbbd0323.pdf`: **Doddanekundi Junction** (KR Puram TPS).

---

## 3. Police Station Jurisdictions Covered
The dataset covers primary arterial corridors across Greater Bengaluru:
1. **Adugodi & Wilson Garden**: Hosur Road, Adugodi Jn, Aishwarya Jn, Audugodi Laskar Road, Mico Bande.
2. **Indiranagar & Frazer Town**: CMH Road, 100 Ft Road, Old Madras Road, Suranjan Das Road, Mosque Road, Pottery Circle.
3. **Jayanagar & Banashankari**: South End Circle, 9th Main, 27th Cross, Delmia Jn, Bannerghatta Road, J.P. Nagar.
4. **K.S. Layout & Mysore Road**: Kanakapura Road, Konanakunte Cross, Rajarajeshwari Jn, Satellite Bus Stand Jn.
5. **Kamakshipalya, Vijayanagar & Rajajinagar**: Magadi Road, West of Chord Road, Vijayanagar, Kanteerava Studio Jn.
6. **Peenya & Hebbal**: Hesaraghatta Cross, Jalahalli Cross (SM Circle), Doddabommasandra, Vidyaranyapura.
7. **KR Puram & Outer Ring Road**: Marathahalli, Doddanekundi, Garudacharpalya, ITPL corridor.
8. **Ulsoor & Ulsoor Gate**: Town Hall, Shivaji Talkies, NR Square, Corporation Circle, Ramaiah Circle.

---

## 4. Domain Anomalies & Preprocessing Rules

### 4.1 CAD Double-Struck Character Artifacts
- **Cause**: CAD drafting software (AutoCAD) renders bolded and stroked fonts by emitting duplicate glyphs at sub-pixel coordinate offsets $(\Delta x \approx 0.5\text{ pt})$.
- **Effect**: Text extracted by PDF parsers contains duplicate characters:
  - `BBAANNGGAALLOORREE` $\rightarrow$ `BANGALORE`
  - `TTIIMMIINNGGSS DDAATTAA` $\rightarrow$ `TIMINGS DATA`
  - `DDGGPPEETTRROOLL` $\rightarrow$ `DG PETROL`
- **Normalization Rule**: If a token has $\ge 33\%$ character duplication pairs, it is normalized using adjacent pair condensation:
  $$\text{if } w[i] == w[i+1] \implies \text{keep single } w[i]$$

### 4.2 Reversed Vertical Text Strings
- **Cause**: Text strings oriented along vertical road approaches are rotated by $90^\circ$ or $270^\circ$. Some PDF text operators store them in reversed character order.
- **Effect**: Words appear mirrored:
  - `NAIRTSEDEP EVISULCXE` $\rightarrow$ `EXCLUSIVE PEDESTRIAN`
  - `ATTAHGARENNAB DAOR` $\rightarrow$ `BANNERGHATTA ROAD`
- **Normalization Rule**: Automated detection of inverted sentinel tokens (`EVISULCXE`, `NAIRTSEDEP`, `DAOR`) triggering string reversal.

---

## 5. Relational Extraction Schema

The dataset extraction pipeline normalizes the 118 raw documents into five relational CSV tables stored in `data/processed/`:

### 5.1 `intersections.csv`
Primary record for each physical intersection.
- `intersection_id` (PK, string): Normalized unique ID (e.g., `INT_ADUGODI_01`).
- `name` (string): Standardized junction name.
- `police_station` (string): Traffic police station jurisdiction.
- `control_type` (string): `FIXED`, `VAC`, `SYNC`.
- `num_approaches` (integer): Number of road approach arms.
- `source_pdf` (string): Original PDF filename.
- `page_number` (integer): Page index (1).
- `latitude` (float): Geocoded / corridor latitude in Bengaluru.
- `longitude` (float): Geocoded / corridor longitude in Bengaluru.
- `data_provenance` (string): `ACTUAL` (from BEL signal plans).

### 5.2 `roads.csv`
Directed approach and connecting road edges.
- `road_id` (PK, string): Unique approach ID (e.g., `RD_ADUGODI_UCOBANK_NB`).
- `intersection_id` (FK, string): Target intersection ID.
- `approach_code` (string): Approach letter (`A`, `B`, `C`, `D`, `E`).
- `road_name` (string): Approach origin/name (e.g., `UCO BANK`, `MICO BANDE`).
- `lanes` (integer): Number of travel lanes (IRC:106 standard or verified layout).
- `capacity_pcu_hr` (float): Link capacity in Passenger Car Units per hour.
- `free_flow_speed_kmh` (float): Design free flow speed (default 40 km/h urban arterial).
- `length_m` (float): Physical link length in meters.
- `data_provenance` (string): `ACTUAL` for names/geometry, `ESTIMATED` for capacities.

### 5.3 `signal_phases.csv`
Phase movements and permitted directional flows.
- `phase_id` (PK, string): Unique phase identifier (e.g., `PH_ADUGODI_P1`).
- `intersection_id` (FK, string): Parent intersection.
- `phase_number` (integer): Phase sequence index (1, 2, 3, 4, 5).
- `approach_code` (string): Approach arm active during phase (`A`, `B`, etc.).
- `permitted_movements` (string): Comma-separated turning movements (`LEFT`, `STRAIGHT`, `RIGHT`, `U-TURN`, `PEDESTRIAN`).
- `is_pedestrian_phase` (boolean): Flag for exclusive pedestrian intervals.
- `data_provenance` (string): `ACTUAL`.

### 5.4 `signal_timings.csv`
Time-of-Day (TOD) timing intervals and green durations.
- `timing_id` (PK, string): Unique timing plan record ID.
- `intersection_id` (FK, string): Parent intersection.
- `plan_name` (string): Schedule category (`WEEKDAY`, `SUNDAY`).
- `start_time` (string): `HH:MM` start of time period.
- `end_time` (string): `HH:MM` end of time period.
- `phase_number` (integer): Phase number.
- `green_time_sec` (integer): Allocated green duration in seconds.
- `yellow_time_sec` (integer): Clearance yellow/amber duration (default 3-4s or documented).
- `all_red_sec` (integer): Intergreen all-red clearance interval.
- `cycle_length_sec` (integer): Stated cycle time.
- `validation_status` (string): `VALID` if $\sum g_p + L = C$, else `FLAGGED_DISCREPANCY`.
- `data_provenance` (string): `ACTUAL`.

### 5.5 `extraction_errors.csv`
Integrity audit tracking for review and validation.
- `error_id` (PK, string): Error tracking ID.
- `source_pdf` (string): Filename where error was detected.
- `intersection_name` (string): Junction name involved.
- `error_category` (string): `CYCLE_MISMATCH`, `TABLE_PARSING_ERROR`, `SCANNED_FILE_OCR`, `MISSING_FIELD`.
- `discrepancy_details` (string): Detailed explanation of numerical or textual mismatch.
- `resolution_applied` (string): Corrective action taken.
- `status` (string): `REVIEWED`, `RESOLVED`, `FLAGGED`.

---

## 6. Traffic Demand Management & Provenance Protocol
Because the 118 PDF signal documents represent geometric and timing plans without vehicle counts, all traffic demand matrices satisfy Section 6 provenance policies:
- `ACTUAL`: Direct extracted timing and geometry data.
- `MEASURED`: Field traffic survey volume counts.
- `EXTERNAL`: Open-data sources (e.g., TomTom / BTP congestion reports).
- `ESTIMATED`: Engineering estimates based on IRC:106 highway capacity manual guidelines.
- `SYNTHETIC`: Generated demand distributions for controlled sensitivity experiments.
Synthetic flows are explicitly flagged and never misrepresented as empirical vehicle counts.
