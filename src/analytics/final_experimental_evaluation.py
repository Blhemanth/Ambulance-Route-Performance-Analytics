"""
Final Academic Experimental Evaluation Script.
Ambulance Route Optimization — Bengaluru.
Phase 6 — Task 6: Final Experimental Evaluation.

Runs a comprehensive, repeatable 6-scenario experiment across 10 canonical emergency
corridors in Greater Bengaluru (60 total experimental runs):
- Scenario A: Shortest-distance route
- Scenario B: Minimum estimated road travel-time route (Baseline Free-Flow)
- Scenario C: Minimum estimated travel-time route with Webster signal delays
- Scenario D: Moderate congestion scenario (BPR v/c ≈ 0.65)
- Scenario E: Heavy congestion scenario (TomTom benchmark v/c ≈ 1.05)
- Scenario F: Combined traffic congestion and signal delay scenario

Outputs machine-readable results to:
data/processed/final_academic_experiments.csv
"""

import os
from typing import Dict, List, Any
import pandas as pd

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

# 10 Canonical Emergency Corridors across Greater Bengaluru
CANONICAL_CORRIDORS = [
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

SCENARIOS_CONFIG = [
    ("A", "SHORTEST_DISTANCE", "Shortest Physical Distance Benchmark", PROFILE_SHORTEST_DISTANCE, "ESTIMATED_GEOMETRY"),
    ("B", "BASELINE_FREE_FLOW", "Minimum Road Travel Time (Baseline Free-Flow)", PROFILE_MINIMUM_TIME, "CALIBRATED_IRC106_FREE_FLOW"),
    ("C", "SIGNAL_AWARE", "Minimum Travel Time with Webster Signal Delays", PROFILE_TIME_PLUS_SIGNAL, "ACTUAL_WEBSTER_SIGNAL_TIMING_PDF"),
    ("D", "MODERATE_CONGESTION", "Moderate Congestion Scenario (v/c ≈ 0.65)", PROFILE_MODERATE_CONGESTION, "ESTIMATED_BPR_MODERATE_CONGESTION"),
    ("E", "HEAVY_CONGESTION", "Heavy Rush-Hour Congestion (TomTom 13.9 km/h Benchmark)", PROFILE_HEAVY_CONGESTION, "ESTIMATED_TOMTOM_BENCHMARK_HEAVY_CONGESTION"),
    ("F", "COMBINED_TRAFFIC_SIGNAL", "Combined Congestion Slowdown + Terminal Signal Delay", PROFILE_COMBINED_TRAFFIC_SIGNAL, "COMBINED_BPR_AND_WEBSTER_PDF")
]


def run_final_experimental_evaluation(
    output_csv_path: str = "data/processed/final_academic_experiments.csv"
) -> pd.DataFrame:
    """Executes the 6-scenario evaluation across all 10 corridors."""
    g_multi, g_di = get_ambulance_road_graphs(force_rebuild=True)
    router = AmbulanceRouter(g_multi, g_di)

    records = []

    for c_idx, (orig_id, dest_id, corridor_label) in enumerate(CANONICAL_CORRIDORS, 1):
        # Obtain baseline B first to compute relative changes
        res_b = router.find_shortest_path(orig_id, dest_id, profile=PROFILE_MINIMUM_TIME)
        base_nodes = res_b["path_nodes"]
        base_time = res_b["total_time_min"]
        base_dist = res_b["total_distance_km"]

        for sc_code, sc_name, sc_desc, prof, prov in SCENARIOS_CONFIG:
            res = router.find_shortest_path(orig_id, dest_id, profile=prof)
            if res["status"] != "OPTIMAL":
                continue

            curr_nodes = res["path_nodes"]
            is_diverged = (curr_nodes != base_nodes)

            # Identify divergence point
            div_node = "Identical"
            if is_diverged:
                for di in range(min(len(base_nodes), len(curr_nodes))):
                    if base_nodes[di] != curr_nodes[di]:
                        d_id = base_nodes[di - 1] if di > 0 else base_nodes[0]
                        div_node = f"{d_id} ({g_di.nodes.get(d_id, {}).get('name', d_id)})"
                        break

            tot_time = res["total_time_min"]
            pct_change_time = round(((tot_time - base_time) / base_time * 100.0) if base_time > 0 else 0.0, 1)

            rec = {
                "experiment_id": f"EXP_{c_idx:02d}_{sc_code}",
                "corridor_index": c_idx,
                "corridor_label": corridor_label,
                "origin_id": orig_id,
                "origin_name": res["origin_name"],
                "destination_id": dest_id,
                "destination_name": res["destination_name"],
                "scenario_code": sc_code,
                "scenario_name": sc_name,
                "scenario_description": sc_desc,
                "routing_profile": prof,
                "selected_route_nodes": " -> ".join(curr_nodes),
                "num_road_segments": res["num_segments"],
                "total_distance_km": res["total_distance_km"],
                "delta_distance_km": round(res["total_distance_km"] - base_dist, 3),
                "total_travel_time_min": tot_time,
                "free_flow_time_min": res["free_flow_time_min"],
                "traffic_delay_min": res["total_traffic_delay_min"],
                "signal_delay_min": res["total_signal_delay_min"],
                "average_speed_kmh": res["average_speed_kmh"],
                "signals_encountered": res["num_signals_encountered"],
                "route_diverged_from_baseline": is_diverged,
                "divergence_junction": div_node,
                "pct_change_vs_baseline_time": pct_change_time,
                "data_provenance": prov
            }
            records.append(rec)

    df_out = pd.DataFrame(records)
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
    df_out.to_csv(output_csv_path, index=False)
    return df_out


if __name__ == "__main__":
    df_res = run_final_experimental_evaluation()
    print(f"Executed {len(df_res)} final academic experimental runs.")
    print("Scenario breakdown:")
    print(df_res.groupby("scenario_name")[["total_travel_time_min", "total_distance_km", "route_diverged_from_baseline"]].mean())
