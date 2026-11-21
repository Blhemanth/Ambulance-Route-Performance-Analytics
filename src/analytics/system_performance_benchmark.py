"""
System Performance Benchmark Script.
Ambulance Route Optimization — Bengaluru.
Phase 6 — Task 7: Comprehensive System Performance Benchmarking.

Benchmarks:
1. Dataset loading & memory footprint (tracemalloc).
2. Graph construction time (MultiDiGraph, DiGraph).
3. Dijkstra execution time across 50 randomly sampled OD pairs:
   - min, max, mean, median, p90, p95, p99, std dev.
4. Yen's K-Shortest Loopless Paths execution time across representative OD pairs:
   - K = 2, K = 3, K = 5.
5. Nearest Hospital spatial search & snapping latency across 50 emergency coordinates.
6. Scenario weight switching latency across all 6 routing profiles.

Outputs results to:
data/processed/performance_benchmark_results.json
"""

import sys
import os

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import json
import math
import random
import time
import tracemalloc
from typing import Dict, List, Any
import numpy as np
import pandas as pd
import networkx as nx

from src.network.ambulance_graph import get_ambulance_road_graphs
from src.network.ambulance_router import (
    AmbulanceRouter,
    PROFILE_SHORTEST_DISTANCE,
    PROFILE_MINIMUM_TIME,
    PROFILE_TIME_PLUS_SIGNAL,
    PROFILE_MODERATE_CONGESTION,
    PROFILE_HEAVY_CONGESTION,
    PROFILE_COMBINED_TRAFFIC_SIGNAL
)
from src.network.hospital_snapper import HospitalRoadSnapper, haversine_distance_m


def run_system_performance_benchmark(
    output_json_path: str = "data/processed/performance_benchmark_results.json"
) -> Dict[str, Any]:
    print("=" * 70)
    print("  AMBULANCE ROUTE OPTIMIZATION — SYSTEM PERFORMANCE BENCHMARK")
    print("  Bengaluru, Karnataka, India | Operations Research Shortest Path")
    print("=" * 70)

    tracemalloc.start()
    results: Dict[str, Any] = {
        "benchmark_metadata": {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "system_scope": "Bengaluru Metropolitan Region Road Network",
            "algorithm": "Dijkstra's Shortest Path & Yen's K-Shortest Loopless Paths",
            "framework": "Python 3.13, NetworkX, GeoPandas",
            "random_seed": 42
        }
    }
    random.seed(42)
    np.random.seed(42)

    # ---------------------------------------------------------
    # 1. Dataset Loading Latency
    # ---------------------------------------------------------
    print("\n[1/6] Measuring dataset loading times...")
    dataset_bench = {}

    # Traffic Signals Timings
    t0 = time.perf_counter()
    sig_path = os.path.join(PROJECT_ROOT, "data/processed/signal_timings.csv")
    if os.path.exists(sig_path):
        df_sig = pd.read_csv(sig_path)
        sig_load_ms = (time.perf_counter() - t0) * 1000
        dataset_bench["signal_timings_csv"] = {
            "record_count": len(df_sig),
            "load_time_ms": round(sig_load_ms, 2)
        }
    else:
        dataset_bench["signal_timings_csv"] = {"status": "not_found"}

    # Hospital Snapped GeoJSON / Cleaned GeoJSON
    t0 = time.perf_counter()
    hosp_path = os.path.join(PROJECT_ROOT, "data/processed/bengaluru_hospitals_cleaned.geojson")
    if os.path.exists(hosp_path):
        with open(hosp_path, "r", encoding="utf-8") as f:
            hosp_geo = json.load(f)
        hosp_load_ms = (time.perf_counter() - t0) * 1000
        dataset_bench["hospitals_geojson"] = {
            "feature_count": len(hosp_geo.get("features", [])),
            "load_time_ms": round(hosp_load_ms, 2)
        }
    else:
        dataset_bench["hospitals_geojson"] = {"status": "not_found"}

    # Intersections GIS CSV
    t0 = time.perf_counter()
    junc_path = os.path.join(PROJECT_ROOT, "data/processed/intersections_gis.csv")
    if os.path.exists(junc_path):
        df_junc = pd.read_csv(junc_path)
        junc_load_ms = (time.perf_counter() - t0) * 1000
        dataset_bench["intersections_gis_csv"] = {
            "record_count": len(df_junc),
            "load_time_ms": round(junc_load_ms, 2)
        }
    else:
        dataset_bench["intersections_gis_csv"] = {"status": "not_found"}

    # Roads GIS JSON
    t0 = time.perf_counter()
    roads_path = os.path.join(PROJECT_ROOT, "data/processed/roads_gis.json")
    if os.path.exists(roads_path):
        with open(roads_path, "r", encoding="utf-8") as f:
            roads_data = json.load(f)
        roads_load_ms = (time.perf_counter() - t0) * 1000
        dataset_bench["roads_gis_json"] = {
            "link_count": len(roads_data),
            "load_time_ms": round(roads_load_ms, 2)
        }
    else:
        dataset_bench["roads_gis_json"] = {"status": "not_found"}

    results["dataset_loading_latency_ms"] = dataset_bench
    for k, v in dataset_bench.items():
        print(f"  - {k}: {v.get('load_time_ms', 'N/A')} ms ({v.get('record_count', v.get('feature_count', v.get('link_count', 'N/A')))} records)")

    # ---------------------------------------------------------
    # 2. Graph Construction Benchmark
    # ---------------------------------------------------------
    print("\n[2/6] Measuring graph construction latency...")
    t0 = time.perf_counter()
    graph_multi, graph_di = get_ambulance_road_graphs(force_rebuild=False)
    graph_build_ms = (time.perf_counter() - t0) * 1000

    results["graph_construction"] = {
        "node_count": len(graph_di.nodes),
        "directed_edge_count": len(graph_di.edges),
        "multidigraph_edge_count": len(graph_multi.edges),
        "total_build_time_ms": round(graph_build_ms, 2),
        "is_strongly_connected": nx.is_strongly_connected(graph_di),
        "strongly_connected_components": nx.number_strongly_connected_components(graph_di),
        "is_weakly_connected": nx.is_weakly_connected(graph_di)
    }
    print(f"  - Nodes: {len(graph_di.nodes)}, Directed Edges: {len(graph_di.edges)}")
    print(f"  - Total Graph Build/Load Time: {graph_build_ms:.2f} ms")

    # ---------------------------------------------------------
    # 3. Dijkstra Shortest Path Latency (50 Random OD Pairs)
    # ---------------------------------------------------------
    print("\n[3/6] Benchmarking Dijkstra Shortest Path (50 random OD pairs)...")
    router = AmbulanceRouter(graph_multi=graph_multi, graph_di=graph_di)
    all_nodes = list(graph_di.nodes)

    # Sample pairs that have a valid path
    od_pairs = []
    attempts = 0
    while len(od_pairs) < 50 and attempts < 1000:
        attempts += 1
        u, v = random.sample(all_nodes, 2)
        if nx.has_path(graph_di, u, v):
            od_pairs.append((u, v))

    dijkstra_latencies_ms = []
    dijkstra_hop_counts = []
    dijkstra_distances_km = []

    for orig, dest in od_pairs:
        t0 = time.perf_counter()
        route = router.find_shortest_path(
            origin=orig,
            destination=dest,
            profile=PROFILE_COMBINED_TRAFFIC_SIGNAL
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000
        dijkstra_latencies_ms.append(elapsed_ms)
        path_nodes = route.get("path_nodes", [])
        dijkstra_hop_counts.append(max(0, len(path_nodes) - 1))
        dijkstra_distances_km.append(route.get("total_distance_km", 0.0))

    lat_arr = np.array(dijkstra_latencies_ms)
    results["dijkstra_benchmark_50_pairs"] = {
        "sample_size": len(od_pairs),
        "profile_tested": PROFILE_COMBINED_TRAFFIC_SIGNAL,
        "mean_latency_ms": round(float(np.mean(lat_arr)), 3),
        "median_latency_ms": round(float(np.median(lat_arr)), 3),
        "std_latency_ms": round(float(np.std(lat_arr)), 3),
        "min_latency_ms": round(float(np.min(lat_arr)), 3),
        "max_latency_ms": round(float(np.max(lat_arr)), 3),
        "p90_latency_ms": round(float(np.percentile(lat_arr, 90)), 3),
        "p95_latency_ms": round(float(np.percentile(lat_arr, 95)), 3),
        "p99_latency_ms": round(float(np.percentile(lat_arr, 99)), 3),
        "mean_hop_count": round(float(np.mean(dijkstra_hop_counts)), 1),
        "mean_distance_km": round(float(np.mean(dijkstra_distances_km)), 2)
    }
    print(f"  - Dijkstra Mean Latency: {np.mean(lat_arr):.3f} ms (p95: {np.percentile(lat_arr, 95):.3f} ms, max: {np.max(lat_arr):.3f} ms)")

    # ---------------------------------------------------------
    # 4. Yen's K-Shortest Loopless Paths Benchmark (K=2, 3, 5)
    # ---------------------------------------------------------
    print("\n[4/6] Benchmarking Yen's K-Shortest Loopless Paths...")
    yen_pairs = od_pairs[:20]  # Representative 20 OD pairs
    yen_benchmarks = {}

    for k_val in [2, 3, 5]:
        k_latencies = []
        k_found_counts = []
        for orig, dest in yen_pairs:
            t0 = time.perf_counter()
            alt_routes = router.find_k_alternative_routes(
                origin=orig,
                destination=dest,
                K=k_val,
                profile=PROFILE_COMBINED_TRAFFIC_SIGNAL
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            k_latencies.append(elapsed_ms)
            k_found_counts.append(len(alt_routes))

        k_arr = np.array(k_latencies)
        yen_benchmarks[f"k_{k_val}"] = {
            "requested_k": k_val,
            "sample_size": len(yen_pairs),
            "mean_latency_ms": round(float(np.mean(k_arr)), 3),
            "median_latency_ms": round(float(np.median(k_arr)), 3),
            "p95_latency_ms": round(float(np.percentile(k_arr, 95)), 3),
            "max_latency_ms": round(float(np.max(k_arr)), 3),
            "mean_paths_found": round(float(np.mean(k_found_counts)), 2)
        }
        print(f"  - Yen's K={k_val}: Mean {np.mean(k_arr):.3f} ms (p95: {np.percentile(k_arr, 95):.3f} ms)")

    results["yens_k_shortest_paths"] = yen_benchmarks

    # ---------------------------------------------------------
    # 5. Hospital Snapping & Nearest Emergency Hospital Benchmark
    # ---------------------------------------------------------
    print("\n[5/6] Benchmarking Nearest Hospital Spatial Query & Snapping...")
    snapper = HospitalRoadSnapper(
        intersections_path=os.path.join(PROJECT_ROOT, "data/processed/intersections_gis.csv"),
        roads_gis_path=os.path.join(PROJECT_ROOT, "data/processed/roads_gis.json")
    )

    # 50 simulated emergency GPS points across Greater Bengaluru bounding box
    emergency_coords = [
        (12.85 + random.random() * 0.23, 77.50 + random.random() * 0.22)
        for _ in range(50)
    ]

    snap_latencies = []
    snap_distances = []
    for idx, (lat, lon) in enumerate(emergency_coords):
        t0 = time.perf_counter()
        snap_res = snapper.snap_single_hospital(
            hosp_lat=lat,
            hosp_lon=lon,
            hosp_id=f"EMERGENCY_LOC_{idx+1:03d}",
            hosp_name=f"Incident Site #{idx+1}",
            emergency_status="ACTIVE_24x7"
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000
        snap_latencies.append(elapsed_ms)
        snap_dist = snap_res.get("snapping_distance_m", 0.0) or 0.0
        snap_distances.append(snap_dist)

    snap_arr = np.array(snap_latencies)
    results["hospital_snapping_benchmark_50_queries"] = {
        "sample_size": len(emergency_coords),
        "mean_latency_ms": round(float(np.mean(snap_arr)), 3),
        "median_latency_ms": round(float(np.median(snap_arr)), 3),
        "p95_latency_ms": round(float(np.percentile(snap_arr, 95)), 3),
        "max_latency_ms": round(float(np.max(snap_arr)), 3),
        "mean_snapping_distance_m": round(float(np.mean(snap_distances)), 1)
    }
    print(f"  - Snapping Mean Latency: {np.mean(snap_arr):.3f} ms (p95: {np.percentile(snap_arr, 95):.3f} ms)")

    # ---------------------------------------------------------
    # 6. Routing Profile Switching Latency
    # ---------------------------------------------------------
    print("\n[6/6] Benchmarking routing profile switching latency...")
    profiles = [
        PROFILE_SHORTEST_DISTANCE,
        PROFILE_MINIMUM_TIME,
        PROFILE_TIME_PLUS_SIGNAL,
        PROFILE_MODERATE_CONGESTION,
        PROFILE_HEAVY_CONGESTION,
        PROFILE_COMBINED_TRAFFIC_SIGNAL
    ]
    test_orig, test_dest = od_pairs[0]
    profile_latencies = {}
    for prof in profiles:
        prof_times = []
        for _ in range(10):
            t0 = time.perf_counter()
            r = router.find_shortest_path(origin=test_orig, destination=test_dest, profile=prof)
            prof_times.append((time.perf_counter() - t0) * 1000)
        profile_latencies[prof] = {
            "mean_ms": round(float(np.mean(prof_times)), 3),
            "distance_km": round(r.get("total_distance_km", 0.0), 2),
            "travel_time_min": round(r.get("total_time_min", 0.0), 2)
        }
    results["profile_switching_latency"] = profile_latencies

    # Memory Tracking
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    results["memory_footprint"] = {
        "current_python_memory_mb": round(current_mem / (1024 * 1024), 2),
        "peak_python_memory_mb": round(peak_mem / (1024 * 1024), 2)
    }
    print(f"\nMemory Footprint: Current={current_mem / 1024 / 1024:.2f} MB, Peak={peak_mem / 1024 / 1024:.2f} MB")

    # Save to JSON
    full_output_path = os.path.join(PROJECT_ROOT, output_json_path)
    os.makedirs(os.path.dirname(full_output_path), exist_ok=True)
    with open(full_output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n[OK] Performance benchmark completed successfully.")
    print(f"[OK] Results saved to: {full_output_path}")
    print("=" * 70)
    return results


if __name__ == "__main__":
    run_system_performance_benchmark()
