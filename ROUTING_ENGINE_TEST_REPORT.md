# ROUTING ENGINE TEST & VALIDATION REPORT
## PHASE 2: UNIT, INTEGRATION, AND BENCHMARK REGRESSION TESTING
### Project: Ambulance Route Optimization — Bengaluru, Karnataka

**Document Version:** 1.0.0 (Phase 2 Engineering Test Report)  
**Date:** 2026-11-20  
**Author:** Software Testing Engineer & Operations Research Specialist  
**Workspace:** `b:\Ambulance Route Optimization`  
**Test Suite Directory:** `tests/`  
**Total Tests Executed:** **63 Unit & Integration Tests**  
**Overall Pass Rate:** **100% (63 passed, 0 failures, 0 errors in 28.69s)**  

---

## 1. TEST SUITE ARCHITECTURE & EXECUTION SUMMARY

The test harness was expanded with a dedicated 15-point specification test suite ([tests/test_ambulance_routing_engine.py](file:///b:/Ambulance%20Route%20Optimization/tests/test_ambulance_routing_engine.py)), validating both real Bengaluru arterial network instances and deterministic synthetic graphs with independently verified mathematical answers.

```text
Ran 63 tests in 28.692s

OK (100% Pass Rate, 0 Failures, 0 Errors)
```

### Breakdown by Test Module:

| Test Module | Coverage Area | Tests Ran | Result |
| :--- | :--- | :--- | :--- |
| **`tests/test_ambulance_routing_engine.py`** | **Phase 2 Core Dijkstra, Yen's Algorithm, Weights & Profiles** | **15** | **15/15 PASSED** |
| `tests/test_hospital_ingestion.py` | Phase 1 Hospital Ingestion, GeoJSON, Triage | 8 | 8/8 PASSED |
| `tests/test_network_snapping.py` | Phase 1 Hospital-to-Road Snapping & Access Delay | 8 | 8/8 PASSED |
| `tests/test_gis_foundation.py` | Phase 0 GIS Schemas, Curved Centerlines | 9 | 9/9 PASSED |
| `tests/test_shortest_path.py` | Legacy Shortest Path Compatibility | 2 | 2/2 PASSED |
| `tests/test_dataset_audit.py` | 118 PDF Dataset Inventory Audit | 3 | 3/3 PASSED |
| `tests/test_max_flow.py` | Legacy Dinic / Ford-Fulkerson Solver | 4 | 4/4 PASSED |
| `tests/test_min_cost_flow.py` | Legacy Network Simplex Solver | 3 | 3/3 PASSED |
| `tests/test_signal_optimizer.py` | Legacy HiGHS LP Green Split Solver | 3 | 3/3 PASSED |
| `tests/test_text_cleaner.py` | CAD Drafting Artifact Filters | 3 | 3/3 PASSED |
| `tests/test_extraction.py` | PDFplumber Vector Table Extraction | 3 | 3/3 PASSED |
| `tests/test_integration.py` | Cross-Module Data Coupling | 2 | 2/2 PASSED |
| **TOTAL** | **Full Regression Suite** | **63** | **63/63 PASSED (100%)** |

---

## 2. DETAILED PHASE 2 SPECIFICATION TEST RESULTS

The 15 Phase 2 required tests were executed and verified against independent manual ground truths:

### 1. `test_01_directed_road_connectivity`
- **Specification**: Verify directed graph connectivity across the 226 intersection nodes and 1,164 directed edges.
- **Assertion**: `G_di.number_of_nodes() == 226`, `G_di.number_of_edges() == 1164`, `nx.is_strongly_connected(G_di) == True`.
- **Result**: **PASSED**. The road network forms a single strongly connected component.

### 2. `test_02_one_way_restrictions`
- **Specification**: Ensure one-way forward links cannot be traversed in reverse.
- **Assertion**: For forward-only edge $(u, v)$, verify `G.has_edge(u, v)` is True and `G.has_edge(v, u)` is False.
- **Result**: **PASSED**.

### 3. `test_03_edge_travel_time_calculation`
- **Specification**: Validate mathematical formula $t_{\text{sec}} = (d_{\text{km}} / v_{\text{kmh}}) \times 3600$.
- **Assertion**: $1,000\text{m}$ at $60.0\text{ km/h} = 60.00\text{ seconds}$; $2,500\text{m}$ at $50.0\text{ km/h} = 180.00\text{ seconds}$.
- **Result**: **PASSED**.

### 4. `test_04_invalid_and_missing_speeds`
- **Specification**: Negative, zero, or NaN speeds must not cause division-by-zero or crashes.
- **Assertion**: Handled with clamp $v \ge 5.0\text{ km/h}$; NaN replaced by default urban speed ($30.0\text{ km/h}$).
- **Result**: **PASSED**. All output travel times are strictly positive and finite.

### 5. `test_05_invalid_distances`
- **Specification**: Zero or negative edge lengths must clamp to minimum positive length ($d \ge 1.0\text{ m}$).
- **Assertion**: Output $t_{\text{sec}} > 0$.
- **Result**: **PASSED**.

### 6. `test_06_dijkstra_optimality_on_known_graph`
- **Specification**: Solve Dijkstra on small deterministic diamond test graph with known costs:
  - Path 1 ($S \to A \to T$): $2,000\text{ m}$ at $60\text{ km/h} \implies 120.0\text{ seconds}$ (**Fastest**).
  - Path 2 ($S \to B \to T$): $1,000\text{ m}$ at $15\text{ km/h} \implies 240.0\text{ seconds}$ (**Shortest**).
  - Path 3 ($S \to C \to T$): $1,600\text{ m}$ at $40\text{ km/h} \implies 144.0\text{ seconds}$.
- **Assertion**: Minimum-time profile selects $S \to A \to T$ with cost exactly $120.0\text{ s}$ ($2.0\text{ min}$).
- **Result**: **PASSED**. Independently verified against manual optimality proof.

### 7. `test_07_shortest_distance_routing`
- **Specification**: Shortest-distance profile minimizes physical meters on the test graph.
- **Assertion**: Profile selects $S \to B \to T$ with distance exactly $1,000.0\text{ m}$ ($1.0\text{ km}$).
- **Result**: **PASSED**.

### 8. `test_08_minimum_time_routing_divergence_from_distance`
- **Specification**: Proves that fastest route can diverge from shortest-distance route and quantifies the tradeoff.
- **Assertion**: Minimum time route is $2.0\text{ minutes}$ faster while being $1.0\text{ km}$ longer.
- **Result**: **PASSED**.

### 9. `test_09_alternative_path_generation_yen`
- **Specification**: Yen's algorithm returns all 3 paths in strict ascending cost order ($120\text{s} \to 144\text{s} \to 240\text{s}$) with 0 repeated-node loops.
- **Assertion**: Rank 1 is $S \to A \to T$; Rank 2 is $S \to C \to T$; Rank 3 is $S \to B \to T$. Loopless condition $\text{len}(nodes) == \text{len}(\text{set}(nodes))$ verified on all paths.
- **Result**: **PASSED**.

### 10. `test_10_parallel_edge_handling`
- **Specification**: MultiDiGraph preserves distinct parallel edges (surface road vs. elevated flyover) between identical endpoints $(S, M)$.
- **Assertion**: Number of edges between $S$ and $M$ equals 2; DiGraph selects minimum travel-time edge.
- **Result**: **PASSED**.

### 11. `test_11_unreachable_destinations`
- **Specification**: Routing to disconnected node $X$ returns `NO_PATH_EXISTS` with infinite cost and empty path without crashing.
- **Assertion**: Status equals `NO_PATH_EXISTS`, total time equals $\infty$.
- **Result**: **PASSED**.

### 12. `test_12_hospital_road_connectivity`
- **Specification**: Route ambulance to Sanjay Gandhi Accident and Trauma Hospital.
- **Assertion**: Status `OPTIMAL`, verification status `VERIFIED_EMERGENCY`, emergency type `LEVEL_1_EMERGENCY_TRAUMA`. Road travel time $> 0$, driveway access time $> 0$.
- **Result**: **PASSED**.

### 13. `test_13_route_distance_calculation`
- **Specification**: Total route distance strictly equals the sum of individual road segment distances.
- **Assertion**: `res["total_distance_m"] == round(sum(e["length_m"] for e in res["path_edges"]), 1)`.
- **Result**: **PASSED**.

### 14. `test_14_route_travel_time_calculation`
- **Specification**: Total route travel time strictly equals the sum of individual road segment travel times.
- **Assertion**: `res["total_time_sec"] == round(sum(e["travel_time_sec"] for e in res["path_edges"]), 1)`.
- **Result**: **PASSED**.

### 15. `test_15_path_reconstruction_consistency`
- **Specification**: Reconstructed node chain $[v_0, v_1, \dots, v_m]$ strictly matches edge steps $(v_i, v_{i+1})$.
- **Assertion**: $\text{len}(\text{nodes}) - 1 == \text{len}(\text{edges})$ and $e_i[\text{from\_node}] == \text{nodes}[i]$, $e_i[\text{to\_node}] == \text{nodes}[i+1]$.
- **Result**: **PASSED**.
