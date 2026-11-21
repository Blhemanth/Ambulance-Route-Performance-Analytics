"""
Signal-Aware vs Baseline Route Comparison Experiment Module.
Phase 4 — Task 8: Systematic Route Comparison Experiment.

Compares identical OD pairs across Greater Bengaluru:
- Scenario A: Minimum estimated road travel time without signal delays (PROFILE_MINIMUM_TIME)
- Scenario B: Minimum estimated travel time with applicable signal delays (PROFILE_TIME_PLUS_SIGNAL)

Outputs: data/processed/signal_route_comparison_results.csv
"""

import os
from typing import Dict, List, Any
import pandas as pd

from src.network.ambulance_graph import get_ambulance_road_graphs
from src.network.ambulance_router import (
    AmbulanceRouter,
    PROFILE_MINIMUM_TIME,
    PROFILE_TIME_PLUS_SIGNAL
)

OD_EXPERIMENT_PAIRS = [
    ("INT_001_RAJARAJESHWARI_JUNCTION", "INT_003_ADUGODI_JUNCTION", "Mysore Road to Adugodi Central"),
    ("INT_001_RAJARAJESHWARI_JUNCTION", "INT_103_ANANDRAO_JUNCTION", "South-West to Central Anandrao Circle"),
    ("INT_103_ANANDRAO_JUNCTION", "INT_073_OLDMADRAS_ROAD_INDIRANAGA", "City Center to Indiranagar Arterial"),
    ("INT_052_PRASANNA_JUNCTION", "INT_003_ADUGODI_JUNCTION", "Magadi Road Corridor to Adugodi"),
    ("INT_005_PUTTANNA_JUNCTION", "INT_160_KIMCO_JUNCTION_MYSORE_ROA", "Adugodi West to Kimco Industrial"),
    ("INT_055_SONYWORLD_JUNCTION_INDIRA", "INT_103_ANANDRAO_JUNCTION", "Sony World Indiranagar to City Center"),
    ("INT_055_SONYWORLD_JUNCTION_INDIRA", "INT_073_OLDMADRAS_ROAD_INDIRANAGA", "Sony World to Old Madras Rd Indiranagar"),
    ("INT_159_HOYSALA_CIRCLEKENGERIUPAN", "INT_103_ANANDRAO_JUNCTION", "Kengeri Satellite Town to Anandrao Circle"),
    ("INT_002_SATELLITEBUSSTAND_JUNCTIO", "INT_003_ADUGODI_JUNCTION", "Satellite Bus Stand to South-Central"),
    ("INT_160_KIMCO_JUNCTION_MYSORE_ROA", "INT_055_SONYWORLD_JUNCTION_INDIRA", "Mysore Rd Industrial to Sony World"),
]


def run_route_comparison_experiment(
    output_csv_path: str = "data/processed/signal_route_comparison_results.csv"
) -> pd.DataFrame:
    """Executes the 10 OD route comparison experiments and exports the results."""
    g_multi, g_di = get_ambulance_road_graphs(force_rebuild=True)
    router = AmbulanceRouter(g_multi, g_di)

    rows = []

    for idx, (orig, dest, label) in enumerate(OD_EXPERIMENT_PAIRS, 1):
        comp = router.compare_baseline_vs_signal_aware(orig, dest)
        if comp["status"] != "SUCCESS":
            continue

        a = comp["scenario_a_baseline"]
        b = comp["scenario_b_signal_aware"]

        rows.append({
            "experiment_id": f"EXP_{idx:02d}",
            "corridor_label": label,
            "origin_id": orig,
            "origin_name": comp["origin_name"],
            "destination_id": dest,
            "destination_name": comp["destination_name"],
            # Scenario A
            "scenario_a_distance_km": a["distance_km"],
            "scenario_a_road_time_min": a["road_travel_time_min"],
            "scenario_a_signal_delay_min": a["signal_delay_min"],
            "scenario_a_total_time_min": a["total_signal_aware_time_min"],
            "scenario_a_signals_encountered": a["signals_encountered"],
            "scenario_a_hops": len(a["path_nodes"]),
            # Scenario B
            "scenario_b_distance_km": b["distance_km"],
            "scenario_b_road_time_min": b["road_travel_time_min"],
            "scenario_b_signal_delay_min": b["signal_delay_min"],
            "scenario_b_total_time_min": b["total_signal_aware_time_min"],
            "scenario_b_signals_encountered": b["signals_encountered"],
            "scenario_b_hops": len(b["path_nodes"]),
            # Deltas & Comparison
            "is_route_divergent": not comp["is_identical_route"],
            "divergence_node_name": comp["divergence_node_name"],
            "delta_distance_km": comp["delta_distance_km"],
            "delta_total_time_min": comp["delta_total_time_min"],
            "description": comp["route_changes_description"]
        })

    df_res = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
    df_res.to_csv(output_csv_path, index=False)
    return df_res


if __name__ == "__main__":
    df_exp = run_route_comparison_experiment()
    print(f"Executed {len(df_exp)} OD comparison experiments.")
    print("Divergent Routes Count:", df_exp["is_route_divergent"].sum(), f"/ {len(df_exp)}")
    print(df_exp[["corridor_label", "scenario_a_total_time_min", "scenario_b_total_time_min", "delta_total_time_min", "is_route_divergent"]])
