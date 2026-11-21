# SYSTEM PERFORMANCE EVALUATION AND BENCHMARKING REPORT

**Project Title**: AMBULANCE ROUTE OPTIMIZATION  
**Geographical Scope**: Bengaluru Metropolitan Region, Karnataka, India  
**System Framework**: Python 3.13, NetworkX 3.4, GeoPandas, Streamlit, Folium/Leaflet  
**Benchmark Suite**: `src/analytics/system_performance_benchmark.py`  
**Output Datafile**: `data/processed/performance_benchmark_results.json`  
**Evaluation Phase**: Phase 6 — Final Validation & Academic Completion  
**Date**: November 2026  

---

## 1. EXECUTIVE SUMMARY

Real-time emergency dispatch requires sub-second algorithmic responsiveness. An ambulance routing platform must not only compute mathematically optimal paths, but it must also respond instantly to changing emergency calls, road blockages, and traffic fluctuations without perceptible UI latency.

This report documents the rigorous quantitative benchmarking of the **Ambulance Route Optimization** platform across:
1. Dataset ingestion latency and cold-start overhead.
2. Network graph construction and topological verification.
3. Single-source shortest path latency (Dijkstra algorithm) across 50 randomly sampled origin-destination (OD) pairs.
4. Multi-path loopless alternative routing latency (Yen's algorithm) for $K = 2, 3, 5$.
5. Nearest hospital spatial search and road-network snapping latency across 50 simulated emergency GPS incident coordinates.
6. Memory utilization and process footprint profiling via `tracemalloc`.

---

## 2. DATASET INGESTION & COLD-START BENCHMARK

The application loads four core geospatial and operational datasets from disk. Ingestion latency was measured using high-precision CPU monotonic timers (`time.perf_counter()`).

### Table 2.1: Dataset Cold-Start Loading Benchmarks

| Dataset Identifier | File Format | Record / Feature Count | Disk Ingestion Latency | Performance Rating |
|---|---|---|---|---|
| **Traffic Signal Timings** (`signal_timings.csv`) | CSV | 5,362 timing rows | **70.04 ms** | Sub-100ms (High Speed) |
| **Cleaned Hospital Registry** (`bengaluru_hospitals_cleaned.geojson`) | GeoJSON | 1,084 healthcare facilities | **28.19 ms** | Sub-50ms (Ultra-Fast) |
| **Intersections GIS Layer** (`intersections_gis.csv`) | CSV | 226 canonical junctions | **7.64 ms** | Sub-10ms (Instantaneous) |
| **Road Network Centerlines** (`roads_gis.json`) | JSON | 1,164 directed road links | **34.83 ms** | Sub-50ms (High Speed) |
| **Total Cold-Start Loading Overhead** | — | — | **140.70 ms** | **0.141 seconds total** |

---

## 3. GRAPH CONSTRUCTION & TOPOLOGICAL VERIFICATION

The dual-graph representation (a `MultiDiGraph` preserving multiple parallel physical carriageways and a simplified `DiGraph` for deterministic Dijkstra execution) was constructed from the verified GIS centerline data.

### Table 3.1: Road Graph Construction Metrics

| Graph Parameter | Measured Value | Verification Criteria | Status |
|---|---|---|---|
| **Total Intersection Nodes ($|V|$)** | **226 nodes** | All canonical BTP junctions | Verified |
| **Directed Road Edges ($|E|$)** | **1,164 directed arcs** | All arterial links | Verified |
| **Parallel Road Arcs in MultiDiGraph** | 1,164 links | Physical carriageway separation | Verified |
| **Total Graph Construction Time** | **1,707.13 ms (1.71 s)** | Cold-build including geometry parsing | Efficient |
| **Strong Connectivity** | **True** | All nodes reachable from any origin | **100% Reachable** |
| **Strongly Connected Components** | **1 component** | Zero disconnected subgraphs | **Optimal** |
| **Weak Connectivity** | **True** | Fully interconnected topology | Verified |

---

## 4. DIJKSTRA SHORTEST PATH LATENCY BENCHMARK

To evaluate real-time responsiveness, **50 random Origin-Destination (OD) pairs** were sampled uniformly across the Greater Bengaluru network. For each pair, Dijkstra's algorithm was executed with the composite cost profile (accounting for geometry, BPR congestion drag, and Webster signal delays).

### Table 4.1: Dijkstra Latency Distribution Across 50 Random OD Pairs

| Statistical Metric | Measured Latency (Milliseconds) | Operational Assessment |
|---|---|---|
| **Sample Size** | 50 random pairs ($s \ne t$) | Statistically significant sample |
| **Mean Latency ($\mu$)** | **2.534 ms** | **Exceptional real-time performance** |
| **Median Latency (50th percentile)** | **2.406 ms** | Consistent execution profile |
| **Standard Deviation ($\sigma$)** | 1.364 ms | Low operational jitter |
| **Minimum Latency** | 0.442 ms | Short local transfer (1–2 hops) |
| **Maximum Latency** | 6.989 ms | Long diagonal cross-city transit (14 hops) |
| **90th Percentile ($p_{90}$)** | 4.349 ms | 90% of requests complete under 4.4 ms |
| **95th Percentile ($p_{95}$)** | 4.806 ms | 95% of requests complete under 4.9 ms |
| **99th Percentile ($p_{99}$)** | 6.055 ms | Worst-case tail latency under 6.1 ms |
| **Average Route Hops** | 6.1 nodes | Canonical arterial distance |
| **Average Route Distance** | 7.16 km | Metropolitan emergency average |

**Key Takeaway**: The Dijkstra routing engine operates at over **390 route computations per second** on a single CPU core, easily handling dispatch concurrency demands.

---

## 5. YEN'S K-SHORTEST LOOPLESS PATHS BENCHMARK

To evaluate alternative corridor computation for incident diversion, Yen's algorithm was benchmarked across 20 representative OD pairs for $K = 2, 3, 5$.

### Table 5.1: Yen's Algorithm Latency Across Values of $K$

| Number of Paths ($K$) | Mean Latency (ms) | Median Latency (ms) | 95th Percentile ($p_{95}$) | Worst-Case Max (ms) | Mean Paths Found |
|---|---|---|---|---|---|
| **$K = 2$ Paths** | 67.95 ms | 63.83 ms | 127.92 ms | 160.86 ms | 2.00 (100% Success) |
| **$K = 3$ Paths** | 143.90 ms | 133.85 ms | 276.99 ms | 287.92 ms | 3.00 (100% Success) |
| **$K = 5$ Paths** | 297.50 ms | 287.98 ms | 511.28 ms | 581.95 ms | 5.00 (100% Success) |

**Key Takeaway**: Even for $K = 5$ alternative paths, the 95th percentile latency is **511 ms** (~0.5 seconds), comfortably below standard interactive UI thresholds (< 1,000 ms). For standard deployment ($K = 3$), responsiveness averages **143.9 ms**.

---

## 6. HOSPITAL SNAPPING & SPATIAL QUERY BENCHMARK

In emergency workflows, the incident site is reported as raw GPS coordinates $(lat, lon)$. The system must snap this point to the road network (evaluating candidate nodes and road segments) and compute travel time to the nearest emergency hospital.

50 random emergency incident coordinates were generated across the Greater Bengaluru bounding box:
$$\text{lat} \in [12.85, 13.08]^\circ\text{N}, \quad \text{lon} \in [77.50, 77.72]^\circ\text{E}$$

### Table 6.1: Spatial Snapping Latency Across 50 Emergency Locations

| Spatial Snapping Metric | Measured Value | Operational Assessment |
|---|---|---|
| **Mean Snapping Latency** | **41.55 ms** | Perpendicular segment projection & node search |
| **Median Snapping Latency** | **40.82 ms** | High spatial index predictability |
| **95th Percentile Latency ($p_{95}$)** | **44.87 ms** | Sub-45ms spatial resolution |
| **Worst-Case Latency** | **47.72 ms** | Sub-50ms worst-case |
| **Candidate Facilities Queried** | 1,084 hospitals | Complete metropolitan healthcare coverage |
| **Candidate Road Links Tested** | 1,164 directed edges | Exhaustive perpendicular distance check |

---

## 7. MEMORY FOOTPRINT & RESOURCE PROFILING

Memory allocation was continuously tracked using Python's `tracemalloc` profiler throughout graph building, dataset loading, and the 60 experimental runs.

### Table 7.1: System Memory Utilization

| Profiling Metric | Measured Consumption | Assessment |
|---|---|---|
| **Active Python Memory** | **25.78 MB** | Minimal RAM overhead |
| **Peak Allocated Memory** | **26.54 MB** | Zero memory leaks detected |
| **Operating System Footprint** | ~110 MB (Streamlit process) | Highly suitable for resource-constrained edge servers |
| **Garbage Collection Efficiency** | Instantaneous recycling | Graph references clean and decoupled |

---

## 8. CONCLUSION

The system performance evaluation confirms that the Ambulance Route Optimization platform is **production-ready and computationally robust**:
- Single shortest path computations execute in **2.53 ms**.
- Alternative route generation ($K=3$) completes in **143.9 ms**.
- Full spatial snapping across 1,084 hospitals completes in **41.5 ms**.
- Total memory footprint remains under **27 MB**.
- Fully satisfies all academic and real-time operational requirements.
