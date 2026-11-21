# Project Documentation Index

**Project:** Ambulance Route Optimization  
**Repository:** [Ambulance-Route-Performance-Analytics](https://github.com/Blhemanth/Ambulance-Route-Performance-Analytics)  
**Study Area:** Bengaluru Metropolitan Region, Karnataka, India  
**Academic Domain:** Operations Research – Shortest Path Network Optimization  

---

## 1. Primary Repository Documents (Root)

- [**README.md**](file:///B:/Ambulance%20Route%20Optimization/README.md) — Master open-source project overview, live demo link, architecture diagram, methodology, and setup guide.
- [**CONTRIBUTING.md**](file:///B:/Ambulance%20Route%20Optimization/CONTRIBUTING.md) — Developer guidelines for code style, testing, and contribution workflows.
- [**PROJECT_DEVELOPMENT_LOG.md**](file:///B:/Ambulance%20Route%20Optimization/PROJECT_DEVELOPMENT_LOG.md) — Continuous chronological engineering log detailing all project phases, design choices, and verification milestones.
- [**AMBULANCE_ROUTE_OPTIMIZATION_FINAL_REPORT.docx**](file:///B:/Ambulance%20Route%20Optimization/AMBULANCE_ROUTE_OPTIMIZATION_FINAL_REPORT.docx) — Formal 20-page academic capstone project report formatted in Microsoft Word.
- [**REPOSITORY_CLEANUP_AUDIT.md**](file:///B:/Ambulance%20Route%20Optimization/REPOSITORY_CLEANUP_AUDIT.md) — Pre-cleanup file inventory and classification audit.
- [**REPOSITORY_CLEANUP_REPORT.md**](file:///B:/Ambulance%20Route%20Optimization/REPOSITORY_CLEANUP_REPORT.md) — Complete audit log of file migrations, validations, and repository restructuring.

---

## 2. Technical Documentation Catalog (`docs/`)

The detailed engineering documentation is organized into six functional directories:

### 2.1 Architecture & Application (`docs/architecture/`)
- [**GIS Ambulance Application Report**](file:///B:/Ambulance%20Route%20Optimization/docs/architecture/GIS_AMBULANCE_APPLICATION_REPORT.md) — In-depth technical architecture of the multi-page Streamlit GIS platform, session state, and spatial visualizers.
- [**Light Medical Theme Implementation Report**](file:///B:/Ambulance%20Route%20Optimization/docs/architecture/LIGHT_THEME_IMPLEMENTATION_REPORT.md) — Comprehensive design system specification for the Light Medical / Clinical GIS interface overhaul.
- [**Operational User Guide**](file:///B:/Ambulance%20Route%20Optimization/docs/architecture/USER_GUIDE.md) — Step-by-step user manual for dispatchers, facility selection, and corridor analysis.

### 2.2 Mathematical Methodology (`docs/methodology/`)
- [**Mathematical Model Validation Report**](file:///B:/Ambulance%20Route%20Optimization/docs/methodology/MATHEMATICAL_MODEL_VALIDATION_REPORT.md) — Formal mathematical formulations of the directed network graph $G=(V, E)$, non-negative cost criteria, and Dijkstra optimality proofs.
- [**Alternative Route Modeling Report**](file:///B:/Ambulance%20Route%20Optimization/docs/methodology/ALTERNATIVE_ROUTE_MODELING_REPORT.md) — Formulation and algorithmic implementation of Yen's K-shortest loopless paths algorithm and detour factor metrics.
- [**Congestion Modeling Report**](file:///B:/Ambulance%20Route%20Optimization/docs/methodology/CONGESTION_MODELING_REPORT.md) — Bureau of Public Roads (BPR) volume-delay calibration ($\alpha=0.20, \beta=4.0$) following Indian Roads Congress (IRC:106) standards.
- [**Signal Delay Model Report**](file:///B:/Ambulance%20Route%20Optimization/docs/methodology/SIGNAL_DELAY_MODEL_REPORT.md) — Theoretical formulation of Webster's uniform delay approximation for fixed-time urban intersections.
- [**Signal-Aware Routing Report**](file:///B:/Ambulance%20Route%20Optimization/docs/methodology/SIGNAL_AWARE_ROUTING_REPORT.md) — Analysis of synthesized signal delay penalties injected into directed graph edges.

### 2.3 Data Provenance & Ingestion (`docs/data/`)
- [**Dataset Documentation & Data Dictionary**](file:///B:/Ambulance%20Route%20Optimization/docs/data/DATASET_DOCUMENTATION.md) — Master schema, field descriptions, coordinate bounds, and licensing provenance for all ingested datasets.
- [**Bengaluru Traffic Data Inventory**](file:///B:/Ambulance%20Route%20Optimization/docs/data/BENGALURU_TRAFFIC_DATA_INVENTORY.md) — Inventory and quality audit of arterial speed surveys and historical traffic volumes.
- [**Hospital Data Integration Report**](file:///B:/Ambulance%20Route%20Optimization/docs/data/HOSPITAL_DATA_INTEGRATION_REPORT.md) — Extraction, spatial deduplication, and emergency capability classification of 1,084 healthcare facilities.
- [**Hospital Network Snapping Report**](file:///B:/Ambulance%20Route%20Optimization/docs/data/HOSPITAL_NETWORK_SNAPPING_REPORT.md) — Formulation and empirical evaluation of the orthogonal road projection and Haversine snapping engine.
- [**Signal PDF Extraction Report**](file:///B:/Ambulance%20Route%20Optimization/docs/data/SIGNAL_PDF_EXTRACTION_REPORT.md) — Automated `pdfplumber` vector stream and OCR bounding-box extraction pipeline for 118 BTP signal sheets.
- [**Signal Timing Validation Report**](file:///B:/Ambulance%20Route%20Optimization/docs/data/SIGNAL_TIMING_VALIDATION_REPORT.md) — Relational schema verification for the 259 timing tables and 5,362 extracted records.
- [**Traffic Data Processing Report**](file:///B:/Ambulance%20Route%20Optimization/docs/data/TRAFFIC_DATA_PROCESSING_REPORT.md) — Data cleaning and feature engineering methodology for network link attributes.
- [**Traffic Signal PDF Validation Report**](file:///B:/Ambulance%20Route%20Optimization/docs/data/TRAFFIC_SIGNAL_PDF_VALIDATION_REPORT.md) — Quality classification distinguishing digital CAD vector exports from scanned raster drawings.

### 2.4 Implementation & Systems (`docs/implementation/`)
- [**Dijkstra Engine Implementation Report**](file:///B:/Ambulance%20Route%20Optimization/docs/implementation/DIJKSTRA_ENGINE_IMPLEMENTATION_REPORT.md) — Binary min-heap priority-queue Dijkstra solver architecture and path reconstruction logic.
- [**GIS Dependency Fix Report**](file:///B:/Ambulance%20Route%20Optimization/docs/implementation/GIS_DEPENDENCY_FIX_REPORT.md) — Investigation, PATH collision resolution, startup diagnostic tool, and multi-tier Leaflet rendering fallbacks.

### 2.5 Evaluation & Quality Assurance (`docs/evaluation/`)
- [**Final Experimental Evaluation Report**](file:///B:/Ambulance%20Route%20Optimization/docs/evaluation/FINAL_EXPERIMENTAL_EVALUATION_REPORT.md) — Empirical evaluation across 10 validated emergency corridors under 6 operational routing profiles.
- [**System Performance Evaluation Report**](file:///B:/Ambulance%20Route%20Optimization/docs/evaluation/SYSTEM_PERFORMANCE_EVALUATION_REPORT.md) — Latency, memory, and scalability benchmarks across 50 random OD pairs (2.53 ms average solve time).
- [**Traffic Scenario Experiments**](file:///B:/Ambulance%20Route%20Optimization/docs/evaluation/TRAFFIC_SCENARIO_EXPERIMENTS.md) — Empirical analysis of BPR congestion scenarios (Free-flow, Moderate, Heavy, Peak Saturated).
- [**Final Project Audit Report**](file:///B:/Ambulance%20Route%20Optimization/docs/evaluation/FINAL_PROJECT_AUDIT_REPORT.md) — System-wide code, data, and mathematical consistency audit.
- [**Final Project Summary**](file:///B:/Ambulance%20Route%20Optimization/docs/evaluation/FINAL_PROJECT_SUMMARY.md) — Milestone achievements, deliverables, and architecture overview.
- [**Report Content Validation**](file:///B:/Ambulance%20Route%20Optimization/docs/evaluation/REPORT_CONTENT_VALIDATION.md) — Academic validation audit verifying statistics in the formal 20-page capstone report.
- [**Phase 4 Test Report**](file:///B:/Ambulance%20Route%20Optimization/docs/evaluation/PHASE_4_TEST_REPORT.md) — Algorithmic correctness test logs for the core routing engine.
- [**Phase 5 Test Report**](file:///B:/Ambulance%20Route%20Optimization/docs/evaluation/PHASE_5_TEST_REPORT.md) — Automated validation logs for the hospital snapping engine.
- [**Route Visualization Test Report**](file:///B:/Ambulance%20Route%20Optimization/docs/evaluation/ROUTE_VISUALIZATION_TEST_REPORT.md) — Folium Leaflet rendering and polyline layer verification.
- [**Routing Engine Test Report**](file:///B:/Ambulance%20Route%20Optimization/docs/evaluation/ROUTING_ENGINE_TEST_REPORT.md) — Comprehensive routing solver test suite audit.

### 2.6 Project Evolution & Planning (`docs/development/`)
- [**Ambulance Project Migration Plan**](file:///B:/Ambulance%20Route%20Optimization/docs/development/AMBULANCE_PROJECT_MIGRATION_PLAN.md) — Architectural roadmap transitioning the codebase from the legacy traffic optimizer to ambulance emergency routing.
- [**Project Cleanup Plan**](file:///B:/Ambulance%20Route%20Optimization/docs/development/PROJECT_CLEANUP_PLAN.md) — Phased workspace hygiene and technical refactoring strategy.

---

## 3. Historical Archives (`archive/`)

- [**Legacy Traffic Optimizer Archive**](file:///B:/Ambulance%20Route%20Optimization/archive/legacy_traffic_optimizer/) — Preserved source files, tests, documentation, and legacy page modules from the earlier "Bengaluru Smart Traffic Optimizer" (Maximum Flow, Minimum Cost Flow, LP Signal Optimization). Retained strictly for academic and engineering historical traceability.
