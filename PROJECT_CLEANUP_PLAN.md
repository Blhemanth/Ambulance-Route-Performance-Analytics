# PROJECT CLEANUP PLAN & ARCHITECTURAL REALIGNMENT
## PHASE 2A: DECOUPLING LEGACY TRAFFIC OPTIMIZER CODE & ARCHIVING OBSOLETE ASSETS
### Project: Ambulance Route Optimization — Bengaluru, Karnataka

**Document Version:** 1.0.0 (Phase 2A Cleanup Plan)  
**Date:** 2026-11-20  
**Author:** Senior Python Developer, Operations Research Specialist & Software Testing Engineer  
**Workspace:** `b:\Ambulance Route Optimization`  
**Archive Target:** `archive/legacy_traffic_optimizer/`  

---

## 1. OBJECTIVE & RATIONALE

The duplicated repository at `b:\Ambulance Route Optimization` originally contained the full application codebase for *Bengaluru Smart Traffic Optimizer* (focusing on multi-intersection signal green-split linear programming, Dinic maximum network flow, and multicommodity minimum cost flow).

The officially approved academic project is **Ambulance Route Optimization**, whose primary Operations Research technique is **Dijkstra's Shortest Path Algorithm** with **Yen's K-Shortest Loopless Paths Algorithm** for alternative routing.

To maintain a focused, maintainable, and professionally structured codebase:
1. Obsolete traffic optimization pages, tests, and documentation are moved into a local structured archive (`archive/legacy_traffic_optimizer/`).
2. No files are permanently deleted.
3. All original datasets (`Bengaluru road network dataset/`, `hospital dataset/`, `traffic datasets/`, and `data/processed/`) are strictly preserved.
4. Active imports and Streamlit navigation are updated to eliminate broken links.

---

## 2. FULL FILE CLASSIFICATION (TASK 1)

Every file and directory across the workspace has been audited and classified into 6 categories:

### Category 1: REQUIRED FOR AMBULANCE PROJECT
- `app.py`: Application portal & executive entry point.
- `src/network/ambulance_graph.py`: Directed road graph builder, IRC:106 speeds, travel-time weights.
- `src/network/ambulance_router.py`: Core Dijkstra travel-time solver, Yen's K-shortest paths, cost profiles, hospital integration.
- `src/network/gis_network.py`: GIS road curvature manager, haversine calculations, polyline distances.
- `src/network/graph_builder.py`: Base Level 1 macro-graph builder (226 nodes, 1,164 directed edges).
- `src/network/hospital_snapper.py`: Spatial access matching, perpendicular polyline projection, driveway delay modeling.
- `src/data_processing/hospital_processor.py`: Overpass GeoJSON ingestion, triage classification, deduplication.
- `components/gis_map.py`: Reusable Folium/Leaflet multi-layer map rendering component.
- `components/ui_helpers.py`: Dark theme, KPI metric cards, caching, navigation drawer.
- `pages/3_Network_Visualization.py`: Bengaluru road network topology viewer.
- `pages/6_Shortest_Path.py`: Core shortest path routing interface (retained for adaptation).
- `pages/11_Hospital_Validation.py`: Interactive hospital snapping & spatial validation view.
- `pages/1_Overview.py` & `pages/2_Dataset_Explorer.py` & `pages/10_Methodology.py`: Retained for phased adaptation.
- `tests/test_ambulance_routing_engine.py`: 15-point Phase 2 Dijkstra and Yen routing test suite.
- `tests/test_hospital_ingestion.py`: Phase 1 GeoJSON & classification tests.
- `tests/test_network_snapping.py`: Phase 1 spatial snapping & threshold tests.
- `tests/test_gis_foundation.py`: GIS schema & polyline geometry tests.
- `tests/test_dataset_audit.py`: 118 PDF dataset audit tests.
- `tests/test_text_cleaner.py` & `tests/test_extraction.py`: PDF table parsing tests.
- `requirements.txt`: Python package dependency list.

### Category 2: REUSABLE WITH MODIFICATION
- `src/data_processing/pdf_extractor.py`, `table_extractor.py`, `ocr_processor.py`: Reusable for Phase 4 signal delay extraction.
- `src/network/network_analyzer.py`: Topological centrality metrics for road intersections.

### Category 3: CONFIRMED OBSOLETE TRAFFIC OPTIMIZATION CODE (TO ARCHIVE)
- `pages/4_Maximum_Flow.py`: Dinic / Ford-Fulkerson maximum network flow solver.
- `pages/5_Minimum_Cost_Flow.py`: Network Simplex multicommodity flow allocation.
- `pages/7_Signal_Optimization.py`: HiGHS LP signal green-split optimization.
- `pages/8_Simulation_Centre.py`: General vehicular meso-queue simulation.
- `src/network/maximum_flow.py`: Standalone Max-Flow solver.
- `src/network/minimum_cost_flow.py`: Standalone Min-Cost-Flow solver.
- `src/network/network_integrator.py`: Coupled feedback loop solver.
- `src/optimization/signal_optimizer.py`: HiGHS LP formulation.
- `src/optimization/sensitivity_analysis.py`: Legacy capacity sensitivity.
- `src/simulation/traffic_simulator.py`: Legacy traffic queue simulator.
- `tests/test_max_flow.py`: Unit tests for Max-Flow.
- `tests/test_min_cost_flow.py`: Unit tests for Min-Cost-Flow.
- `tests/test_signal_optimizer.py`: Unit tests for HiGHS LP signal optimizer.
- `tests/test_integration.py`: Unit tests for coupled traffic feedback loops.

### Category 4: CONFIRMED OBSOLETE TRAFFIC DOCUMENTATION (TO ARCHIVE)
- `APPLICATION_AUDIT_REPORT.md`: Pre-migration audit of the traffic signal optimizer.
- `BENGALURU_SMART_TRAFFIC_OPTIMIZER_COMPREHENSIVE_RESEARCH_REPORT.md`: Legacy research paper draft.
- `EXPERIMENTAL_RESULTS.md`: Max-flow and signal timing benchmark tables.
- `MATHEMATICAL_MODEL.md`: Formulations for Models 1, 2, and 4 (Max Flow, Min Cost Flow, Signal LP).
- `NETWORK_MODEL_DOCUMENTATION.md`: Documentation for 4-model coupled feedback architecture.
- `PRESENTATION_SLIDES_GUIDE.md`: Slide deck outline for traffic optimizer defense.
- `GIS_IMPLEMENTATION_REPORT.md` & `GIS_TESTING_REPORT.md`: Historical Phase 1 GIS foundation logs.
- `TESTING_REPORT.md`: Legacy 23-test report.

### Category 5: ORIGINAL DATASETS THAT MUST BE PRESERVED
- `Bengaluru road network dataset/southern-zone-261119.osm.pbf` (534.02 MB)
- `hospital dataset/export.geojson` (617.46 KB)
- `traffic datasets/*.pdf` (118 PDF files, 6.26 MB)
- `data/processed/*.csv`, `data/processed/*.json`

### Category 6: UNCERTAIN / RETAINED FOR PHASED REPLACEMENT
- `pages/9_Analytics.py`: Retained temporarily; to be replaced by Route Performance Analytics in Phase 5.

---

## 3. PROPOSED FILE MOVES & ARCHIVE STRUCTURE

```text
archive/legacy_traffic_optimizer/
├── pages/
│   ├── 4_Maximum_Flow.py
│   ├── 5_Minimum_Cost_Flow.py
│   ├── 7_Signal_Optimization.py
│   └── 8_Simulation_Centre.py
├── tests/
│   ├── test_max_flow.py
│   ├── test_min_cost_flow.py
│   ├── test_signal_optimizer.py
│   └── test_integration.py
├── src/
│   ├── maximum_flow.py
│   ├── minimum_cost_flow.py
│   ├── network_integrator.py
│   ├── signal_optimizer.py
│   ├── sensitivity_analysis.py
│   └── traffic_simulator.py
└── docs/
    ├── APPLICATION_AUDIT_REPORT.md
    ├── BENGALURU_SMART_TRAFFIC_OPTIMIZER_COMPREHENSIVE_RESEARCH_REPORT.md
    ├── EXPERIMENTAL_RESULTS.md
    ├── GIS_IMPLEMENTATION_REPORT.md
    ├── GIS_TESTING_REPORT.md
    ├── MATHEMATICAL_MODEL.md
    ├── NETWORK_MODEL_DOCUMENTATION.md
    ├── PRESENTATION_SLIDES_GUIDE.md
    └── TESTING_REPORT.md
```

---

## 4. DEPENDENCY AUDIT & IMPORT REFACTORING

1. **`tests/test_gis_foundation.py`**:
   - *Previous state*: Imported `MaximumFlowOptimizer` and `MinimumCostFlowOptimizer` to test that GIS enrichment did not alter capacity fields.
   - *Refactoring*: Update the test methods to validate `ShortestPathOptimizer` and `AmbulanceRouter` on GIS-enriched graphs, removing all dependencies on archived modules.
2. **`pages/6_Shortest_Path.py`**:
   - *Previous state*: Contained an unused import of `NetworkIntegrator`.
   - *Refactoring*: Removed unused import.
3. **`components/ui_helpers.py`**:
   - *Previous state*: Rendered navigation links to pages 4, 5, 7, and 8.
   - *Refactoring*: Updated `render_sidebar_navigation()` to show only active ambulance project pages:
     - 01. Corpus Architecture (`pages/1_Overview.py`)
     - 02. Signal Plan Explorer (`pages/2_Dataset_Explorer.py`)
     - 03. Network Topology Map (`pages/3_Network_Visualization.py`)
     - 04. Model 3: Dijkstra Shortest Path (`pages/6_Shortest_Path.py`)
     - 05. Hospital Network Snapping Map (`pages/11_Hospital_Validation.py`)
     - 06. Formulations & Proofs (`pages/10_Methodology.py`)
4. **`app.py`**:
   - *Previous state*: Contained direct page links to pages 4, 5, and 7.
   - *Refactoring*: Updated executive portal cards to point to active ambulance modules.

---

## 5. SAFETY & REVERSIBILITY GUARANTEES

- **Zero deletion**: Files are moved via `os.rename` into `archive/legacy_traffic_optimizer/`.
- **Easy restore**: Any archived file can be restored instantly if required in a future phase.
- **Test coverage**: Active test suite continues to execute with 100% pass rate.
