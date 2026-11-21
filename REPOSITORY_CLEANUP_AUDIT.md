# REPOSITORY CLEANUP AUDIT

**Project:** Ambulance Route Optimization  
**Repository:** https://github.com/Blhemanth/Ambulance-Route-Performance-Analytics  
**Local Working Directory:** `B:\Ambulance Route Optimization`  
**Date:** 2026-11-21  
**Audit Conducted By:** Senior Software Architect & Repository Maintainer  
**Audit Objective:** Comprehensive inventory and classification of all project files, directories, dependencies, and assets prior to restructuring and documentation overhaul.

---

## 1. Inventory & Classification Framework

Every file and directory in the workspace is audited and assigned one of five strict classifications:

1. **KEEP**: Essential for application runtime, core Operations Research routing, GIS rendering, dataset pipelines, or automated tests. Must remain active in its current operational path.
2. **KEEP AND ORGANIZE**: Highly valuable technical documentation, formal research reports, mathematical formulations, or experimental logs that should be categorized into structured subdirectories under `docs/`.
3. **ARCHIVE**: Obsolete legacy material from the previous "Bengaluru Smart Traffic Optimizer" (e.g., Maximum Flow, Minimum Cost Flow, LP signal optimization) that is retained for historical traceability in `archive/legacy_traffic_optimizer/` but excluded from active application prominence.
4. **REMOVE**: Demonstrably obsolete, redundant temporary scratch scripts or duplicate test artifacts with zero code references.
5. **INVESTIGATE**: Files whose dependencies or operational roles require validation before migration.

---

## 2. Comprehensive File Inventory

### 2.1 Application Core & Configuration (KEEP)

| Path | Classification | File Size | Description & Operational Role |
| :--- | :---: | :---: | :--- |
| `app.py` | **KEEP** | 11.6 KB | Primary Streamlit entry point; renders Operations Dashboard and initializes global state. |
| `pages/1_Road_Network_Explorer.py` | **KEEP** | 9.8 KB | Interactive visualizer for the 226-node, 1,164-link Bengaluru arterial road network. |
| `pages/2_Hospital_Finder.py` | **KEEP** | 10.7 KB | Healthcare facility explorer with emergency classification and snapping telemetry. |
| `pages/3_Ambulance_Route_Optimizer.py` | **KEEP** | 17.5 KB | Core dispatch console executing Dijkstra's algorithm across 6 cost profiles. |
| `pages/4_Alternative_Route_Comparison.py`| **KEEP** | 10.3 KB | Multi-path contingency routing using Yen's K-shortest loopless paths algorithm. |
| `pages/5_Signal_Delay_Analysis.py` | **KEEP** | 10.8 KB | BTP traffic signal explorer and Webster uniform delay analyzer. |
| `pages/6_Traffic_Scenario_Analysis.py` | **KEEP** | 12.5 KB | Sensitivity analyzer evaluating BPR congestion scenarios (Free-flow, Moderate, Heavy). |
| `pages/7_Route_Performance_Analytics.py` | **KEEP** | 9.9 KB | Comparative benchmark analytics and route performance metrics. |
| `pages/8_OR_Methodology.py` | **KEEP** | 8.2 KB | Mathematical formulation reference and algorithm complexity documentation. |
| `components/dependency_checker.py` | **KEEP** | 3.1 KB | Active runtime environment auditor preventing missing-package crashes. |
| `components/gis_map.py` | **KEEP** | 22.8 KB | Resilient multi-tier Folium/Leaflet interactive map renderer. |
| `components/ui_helpers.py` | **KEEP** | 12.3 KB | Shared Streamlit CSS loaders, session state managers, and Plotly templates. |
| `requirements.txt` | **KEEP** | 0.8 KB | Production and development dependency manifest. |
| `pyproject.toml` | **KEEP** | 1.1 KB | Standard Python build system specification and package metadata. |
| `.gitignore` | **KEEP** | 0.4 KB | Exclusion rules for `.osm.pbf`, virtual environments, and Python bytecode. |
| `.streamlit/config.toml` | **KEEP** | 0.3 KB | Streamlit UI configuration (Light Medical theme). |

---

### 2.2 Source Modules (`src/`) (KEEP)

| Subdirectory / Module | Classification | Description & Technical Capability |
| :--- | :---: | :--- |
| `src/analytics/` | **KEEP** | Experimental benchmarks, signal-route comparison, and scenario evaluation scripts. |
| `src/data_processing/` | **KEEP** | PDF table extractor (`pdfplumber`), OCR pipeline, hospital processor, and validators. |
| `src/database/` | **KEEP** | Module initialization and relational querying helpers. |
| `src/network/ambulance_router.py` | **KEEP** | Master routing engine: Priority-Queue Dijkstra solver and Yen's K-shortest paths. |
| `src/network/ambulance_graph.py` | **KEEP** | NetworkX directed graph builder with one-way directional enforcement. |
| `src/network/hospital_snapper.py` | **KEEP** | Spatial snapping engine utilizing orthogonal segment projection and Haversine distance. |
| `src/network/gis_network.py` | **KEEP** | GeoPandas and Shapely spatial network management interface. |
| `src/network/graph_builder.py` | **KEEP** | Graph compilation from relational CSV datasets. |
| `src/signals/signal_delay_model.py` | **KEEP** | Webster uniform delay formulation $d_{sig} = R^2 / (2C)$. |
| `src/signals/signal_network_matcher.py`| **KEEP** | Spatial geocoding and link-to-phase mapping engine. |
| `src/signals/signal_validator.py` | **KEEP** | Automated validation audit for 118 BTP signal sheets. |
| `src/traffic/congestion_model.py` | **KEEP** | Bureau of Public Roads (BPR) volume-delay functions ($\alpha=0.20, \beta=4.0$). |
| `src/traffic/traffic_data_auditor.py` | **KEEP** | Arterial speed survey and volume/capacity data auditor. |
| `src/optimization/` | **KEEP** | Core package namespace. |
| `src/simulation/` | **KEEP** | Simulation package namespace. |

---

### 2.3 Datasets & Provenance (KEEP)

| Directory / File | Classification | Size / Extent | Verification & Provenance |
| :--- | :---: | :---: | :--- |
| `data/processed/` | **KEEP** | 20 files (~5.1 MB) | Processed network, hospital, and signal tables. |
| `hospital dataset/export.geojson` | **KEEP** | 632 KB | Source OpenStreetMap healthcare facilities export. |
| `traffic datasets/` | **KEEP** | 118 PDF files | Raw Bangalore Traffic Police signal engineering sheets. |
| `Bengaluru road network dataset/` | **KEEP (EXCLUDED)** | 534 MB (`.osm.pbf`) | Local raw OSM extract; retained locally, excluded via `.gitignore`. |

---

### 2.4 Automated Test Suite (`tests/`) (KEEP)

| Test Module | Classification | Tests | Scope |
| :--- | :---: | :---: | :--- |
| `test_ambulance_routing_engine.py` | **KEEP** | 15 | Dijkstra solvers, cost profiles, Yen's alternative paths. |
| `test_signal_delay_engine.py` | **KEEP** | 15 | Webster delay calculations, red split bounds. |
| `test_traffic_congestion_engine.py` | **KEEP** | 13 | BPR functions, volume-capacity adjustments. |
| `test_gis_route_visualization.py` | **KEEP** | 12 | Folium rendering, legend builders, iframe fallback. |
| `test_gis_foundation.py` | **KEEP** | 9 | Coordinate boundaries, GeoPandas schemas. |
| `test_hospital_ingestion.py` | **KEEP** | 8 | Healthcare catalog parsing, trauma tiers. |
| `test_network_snapping.py` | **KEEP** | 8 | Orthogonal projection, Haversine snapping. |
| `test_reference_graph_optimality.py` | **KEEP** | 6 | Connectivity, triangle inequality, cycle defense. |
| `test_extraction.py` | **KEEP** | 4 | PDF bounding-box table extraction. |
| `test_dataset_audit.py` | **KEEP** | 3 | Data integrity, column schemas, row counts. |
| `test_text_cleaner.py` | **KEEP** | 3 | Junction name normalization and OCR cleaning. |
| `test_shortest_path.py` | **KEEP** | 2 | NetworkX baseline validation. |
| **Total Test Suite** | **KEEP** | **98** | **100% Pass Rate across all modules.** |

---

### 2.5 Technical Documentation & Reports (KEEP AND ORGANIZE)

The root folder currently contains 30 Markdown report files from various development milestones. These should be consolidated into categorized directories under `docs/`:

| Current Root File | Proposed Target Location | Category |
| :--- | :--- | :--- |
| `GIS_AMBULANCE_APPLICATION_REPORT.md` | `docs/architecture/` | Architecture & GIS Application |
| `LIGHT_THEME_IMPLEMENTATION_REPORT.md` | `docs/architecture/` | Design System & UI Overhaul |
| `USER_GUIDE.md` | `docs/architecture/` | Dispatcher Operational User Guide |
| `MATHEMATICAL_MODEL_VALIDATION_REPORT.md` | `docs/methodology/` | Mathematical Formulations & Proofs |
| `ALTERNATIVE_ROUTE_MODELING_REPORT.md` | `docs/methodology/` | Yen's K-Shortest Paths Formulation |
| `CONGESTION_MODELING_REPORT.md` | `docs/methodology/` | BPR Congestion Model Specification |
| `SIGNAL_DELAY_MODEL_REPORT.md` | `docs/methodology/` | Webster Uniform Delay Formulation |
| `SIGNAL_AWARE_ROUTING_REPORT.md` | `docs/methodology/` | Signal-Aware Cost Formulations |
| `DATASET_DOCUMENTATION.md` | `docs/data/` | Master Data Dictionary & Provenance |
| `BENGALURU_TRAFFIC_DATA_INVENTORY.md` | `docs/data/` | Traffic Speed Survey Inventory |
| `HOSPITAL_DATA_INTEGRATION_REPORT.md` | `docs/data/` | Healthcare Dataset Cleaning & Validation |
| `HOSPITAL_NETWORK_SNAPPING_REPORT.md` | `docs/data/` | Road Network Snapping Analysis |
| `SIGNAL_PDF_EXTRACTION_REPORT.md` | `docs/data/` | 118 PDF Ingestion & Parsing Logs |
| `SIGNAL_TIMING_VALIDATION_REPORT.md` | `docs/data/` | Signal Timing Audit Records |
| `TRAFFIC_DATA_PROCESSING_REPORT.md` | `docs/data/` | Traffic Volume & Delay Processing |
| `TRAFFIC_SIGNAL_PDF_VALIDATION_REPORT.md` | `docs/data/` | CAD vs Raster Quality Analysis |
| `DIJKSTRA_ENGINE_IMPLEMENTATION_REPORT.md` | `docs/implementation/` | Min-Heap Dijkstra Solver Implementation |
| `GIS_DEPENDENCY_FIX_REPORT.md` | `docs/implementation/` | Dual Python Runtime & GIS Fix |
| `FINAL_EXPERIMENTAL_EVALUATION_REPORT.md` | `docs/evaluation/` | 10-Corridor Experimental Evaluation |
| `FINAL_PROJECT_AUDIT_REPORT.md` | `docs/evaluation/` | Comprehensive System Technical Audit |
| `FINAL_PROJECT_SUMMARY.md` | `docs/evaluation/` | Executive Milestone Summary |
| `SYSTEM_PERFORMANCE_EVALUATION_REPORT.md` | `docs/evaluation/` | Latency & Memory Benchmark Audit |
| `TRAFFIC_SCENARIO_EXPERIMENTS.md` | `docs/evaluation/` | BPR Scenario Benchmark Metrics |
| `PHASE_4_TEST_REPORT.md` | `docs/evaluation/` | Routing Engine Test Audit |
| `PHASE_5_TEST_REPORT.md` | `docs/evaluation/` | Hospital Snapping Test Audit |
| `ROUTE_VISUALIZATION_TEST_REPORT.md` | `docs/evaluation/` | GIS Layer Test Audit |
| `ROUTING_ENGINE_TEST_REPORT.md` | `docs/evaluation/` | Algorithmic Correctness Test Audit |
| `REPORT_CONTENT_VALIDATION.md` | `docs/evaluation/` | Final Capstone Report Verification |
| `AMBULANCE_PROJECT_MIGRATION_PLAN.md` | `docs/development/` | Traffic Optimizer -> Ambulance Plan |
| `PROJECT_CLEANUP_PLAN.md` | `docs/development/` | Repository Reorganization Blueprint |

**Master Files Retained in Root**:
- `README.md` (Completely rewritten to present Ambulance Route Optimization)
- `PROJECT_DEVELOPMENT_LOG.md` (Primary continuous engineering log)
- `DOCUMENTATION_INDEX.md` (Master catalog linking all files in `docs/`)
- `AMBULANCE_ROUTE_OPTIMIZATION_FINAL_REPORT.docx` (Formal 20-page capstone report)
- `CONTRIBUTING.md` (Developer contribution and setup guidelines)

---

### 2.6 Assets & Screenshot Reorganization

| Current Path | Proposed Action | Reason |
| :--- | :---: | :--- |
| `assets/diagrams/system_architecture.png` | **KEEP** | 300 DPI publication-quality system architecture diagram. |
| `assets/diagrams/system_architecture_test.png` | **REMOVE** | Temporary scratch image from diagram generator testing. |
| `assets/logo.png`, `logo_banner.png`, `logo_icon.png` | **KEEP** | Official branding assets utilized in sidebar and UI. |
| `assets/style.css` | **KEEP** | Centralized Light Medical / Clinical GIS stylesheet. |
| `assets/screenshots/page3_network_topology.png` | **ARCHIVE** | Move to `archive/legacy_traffic_optimizer/assets/screenshots/`. |
| `assets/screenshots/page4_maximum_flow.png` | **ARCHIVE** | Obsolete legacy Max-Flow screenshot; move to archive. |
| `assets/screenshots/page5_minimum_cost_flow.png` | **ARCHIVE** | Obsolete legacy Min-Cost Flow screenshot; move to archive. |
| `assets/screenshots/page6_shortest_path.png` | **ARCHIVE** | Obsolete legacy UI screenshot; move to archive. |
| `reports/screenshots/*.png` (8 screenshots) | **PROMOTE** | Copy to `assets/screenshots/` as primary UI gallery assets for README and documentation. |

---

### 2.7 Scratch Scripts (`scratch/`)

| File | Proposed Action | Destination & Justification |
| :--- | :---: | :--- |
| `scratch/capture_screenshots.py` | **KEEP & REORGANIZE** | Move to `scripts/capture_screenshots.py` (automation tool). |
| `scratch/demonstrate_route.py` | **KEEP & REORGANIZE** | Move to `scripts/demonstrate_route.py` (reproducible demo). |
| `scratch/verify_fix.py` | **KEEP & REORGANIZE** | Move to `scripts/verify_fix.py` (diagnostic script). |
| `scratch/test_format.py` | **REMOVE** | 7-line ephemeral test with no dependencies or reusable logic. |
| `scratch/` directory | **REMOVE** | Cleaned and removed once scripts are migrated. |

---

## 3. Summary of Cleanup Actions

- **Files to Move into `docs/`**: 30 technical reports organized across 6 thematic categories.
- **Root Files to Create**: `CONTRIBUTING.md`, `DOCUMENTATION_INDEX.md`, `REPOSITORY_CLEANUP_REPORT.md`, and complete rewrite of `README.md`.
- **Scripts Reorganized**: Migrated 3 reusable tools from `scratch/` to `scripts/`.
- **Files to Remove**: 2 ephemeral scratch artifacts (`test_format.py`, `system_architecture_test.png`).
- **Assets Reorganized**: Promoted active ambulance screenshots to `assets/screenshots/` and quarantined legacy max-flow screenshots to `archive/`.
- **Safety Checks**: Verified that zero application code, modules, or tests import the moved files. Application entry point and test suite remain 100% operational.
