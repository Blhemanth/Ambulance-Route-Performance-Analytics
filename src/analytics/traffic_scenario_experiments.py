"""
Comprehensive Traffic Scenario Routing Experiments Module.
Ambulance Route Optimization — Bengaluru.
Phase 5 — Task 7: Repeatable Route Comparison Experiments.

Systematically evaluates 10 canonical emergency corridors across 5 traffic scenarios:
1. BASELINE_FREE_FLOW (IRC:106 speed limits, zero congestion delay, zero signal delay)
2. SHORTEST_DISTANCE (Road network distance minimization benchmark)
3. MODERATE_CONGESTION (Inter-peak calibrated BPR v/c ≈ 0.65 link slowdowns)
4. HEAVY_CONGESTION (TomTom rush-hour benchmark v/c ≈ 1.05 link slowdowns)
5. COMBINED_TRAFFIC_SIGNAL (Heavy congestion + verified Webster red signal delays)

Strictly preserves non-double-counting invariants:
t_edge = t_0 (free-flow) + Delta t_traffic (mid-link slowdown) + d_signal (terminal junction delay).

Outputs:
data/processed/traffic_scenario_experiment_results.csv
"""

import os
from typing import Dict, List, Any
import pandas as pd

from src.network.ambulance_graph import get_ambulance_road_graphs
from src.network.ambulance_router import (
    AmbulanceRouter,
    PROFILE_MINIMUM_TIME,
    PROFILE_SHORTEST_DISTANCE,
    PROFILE_MODERATE_CONGESTION,
    PROFILE_HEAVY_CONGESTION,
    PROFILE_COMBINED_TRAFFIC_SIGNAL
)

EMERGENCY_CORRIDOR_PAIRS = [
    ("INT_001_RAJARAJESHWARI_JUNCTION", "INT_003_ADUGODI_JUNCTION", "South-West Arterial to Adugodi Central Hub"),
    ("INT_001_RAJARAJESHWARI_JUNCTION", "INT_103_ANANDRAO_JUNCTION", "Mysore Road to Anandrao Circle CBD Hub"),
    ("INT_103_ANANDRAO_JUNCTION", "INT_073_OLDMADRAS_ROAD_INDIRANAGA", "City Core to Indiranagar Tech Corridor"),
    ("INT_052_PRASANNA_JUNCTION", "INT_003_ADUGODI_JUNCTION", "Magadi Road Corridor to Adugodi Hub"),
    ("INT_005_PUTTANNA_JUNCTION", "INT_160_KIMCO_JUNCTION_MYSORE_ROA", "Adugodi West to Kimco Industrial Sector"),
    ("INT_055_SONYWORLD_JUNCTION_INDIRA", "INT_103_ANANDRAO_JUNCTION", "Sony World Indiranagar to Central Anandrao"),
    ("INT_055_SONYWORLD_JUNCTION_INDIRA", "INT_073_OLDMADRAS_ROAD_INDIRANAGA", "Sony World to Old Madras Rd Arterial"),
    ("INT_159_HOYSALA_CIRCLEKENGERIUPAN", "INT_103_ANANDRAO_JUNCTION", "Kengeri Satellite Town to CBD Center"),
    ("INT_002_SATELLITEBUSSTAND_JUNCTIO", "INT_003_ADUGODI_JUNCTION", "Satellite Bus Stand to South-Central"),
    ("INT_160_KIMCO_JUNCTION_MYSORE_ROA", "INT_055_SONYWORLD_JUNCTION_INDIRA", "Mysore Rd Industrial to Sony World Tech"),
]


def run_traffic_scenario_experiments(
    output_csv_path: str = "data/processed/traffic_scenario_experiment_results.csv"
) -> pd.DataFrame:
    """
    Executes the 10 corridor experiments across all 5 routing configurations
    and exports a structured comparison catalog.
    """
    g_multi, g_di = get_ambulance_road_graphs(force_rebuild=True)
    router = AmbulanceRouter(g_multi, g_di)

    records = []

    for idx, (orig, dest, label) in enumerate(EMERGENCY_CORRIDOR_PAIRS, 1):
        comp = router.compare_traffic_scenarios(orig, dest)
        if comp["status"] != "SUCCESS":
            continue

        sc = comp["scenarios"]
        base = sc["BASELINE_FREE_FLOW"]
        dist = sc["SHORTEST_DISTANCE"]
        mod = sc["MODERATE_CONGESTION"]
        hvy = sc["HEAVY_CONGESTION"]
        comb = sc["COMBINED_TRAFFIC_SIGNAL"]

        # Congestion delay ratios
        hvy_time_diff = round(hvy["total_time_min"] - base["total_time_min"], 2)
        hvy_pct_increase = round((hvy_time_diff / base["total_time_min"] * 100.0) if base["total_time_min"] > 0 else 0.0, 1)

        comb_time_diff = round(comb["total_time_min"] - base["total_time_min"], 2)
        comb_pct_increase = round((comb_time_diff / base["total_time_min"] * 100.0) if base["total_time_min"] > 0 else 0.0, 1)

        sig_delay_share_pct = round((comb["signal_delay_min"] / comb["total_time_min"] * 100.0) if comb["total_time_min"] > 0 else 0.0, 1)

        rec = {
            "experiment_id": f"EXP_SCENARIO_{idx:02d}",
            "corridor_label": label,
            "origin_id": orig,
            "origin_name": comp["origin_name"],
            "destination_id": dest,
            "destination_name": comp["destination_name"],
            # Baseline Free-Flow
            "baseline_distance_km": base["distance_km"],
            "baseline_time_min": base["total_time_min"],
            "baseline_speed_kmh": base["average_speed_kmh"],
            "baseline_hops": len(base["path_nodes"]),
            # Shortest Distance Benchmark
            "dist_benchmark_km": dist["distance_km"],
            "dist_benchmark_time_min": dist["total_time_min"],
            "dist_benchmark_hops": len(dist["path_nodes"]),
            "dist_diverged_from_baseline": dist["is_diverged_from_baseline"],
            # Moderate Congestion
            "moderate_time_min": mod["total_time_min"],
            "moderate_traffic_delay_min": mod["traffic_delay_min"],
            "moderate_speed_kmh": mod["average_speed_kmh"],
            "moderate_diverged": mod["is_diverged_from_baseline"],
            # Heavy Congestion
            "heavy_time_min": hvy["total_time_min"],
            "heavy_traffic_delay_min": hvy["traffic_delay_min"],
            "heavy_speed_kmh": hvy["average_speed_kmh"],
            "heavy_diverged": hvy["is_diverged_from_baseline"],
            "heavy_divergence_junction": hvy["divergence_node_name"],
            "heavy_vs_base_time_increase_pct": hvy_pct_increase,
            # Combined Congestion + Signal
            "combined_total_time_min": comb["total_time_min"],
            "combined_traffic_delay_min": comb["traffic_delay_min"],
            "combined_signal_delay_min": comb["signal_delay_min"],
            "combined_speed_kmh": comb["average_speed_kmh"],
            "combined_diverged": comb["is_diverged_from_baseline"],
            "combined_divergence_junction": comb["divergence_node_name"],
            "combined_vs_base_time_increase_pct": comb_pct_increase,
            "signal_share_of_total_time_pct": sig_delay_share_pct
        }
        records.append(rec)

    df_out = pd.DataFrame(records)
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
    df_out.to_csv(output_csv_path, index=False)
    return df_out


if __name__ == "__main__":
    df_results = run_traffic_scenario_experiments()
    print(f"Successfully generated {len(df_results)} scenario comparison records.")
    print("\nSummary of Scenario Comparisons:")
    cols_preview = [
        "corridor_label",
        "baseline_time_min",
        "moderate_time_min",
        "heavy_time_min",
        "combined_total_time_min",
        "combined_vs_base_time_increase_pct"
    ]
    print(df_results[cols_preview].to_string(index=False))
