"""
Traffic Demand Management Module for Bengaluru Smart Traffic Optimizer.
Supports Actual traffic surveys, manual vehicle entry, external open data,
and explicitly classified synthetic demand benchmarks with strict provenance tagging:
- ACTUAL
- EXTERNAL
- MEASURED
- ESTIMATED
- SYNTHETIC
"""

import os
import pandas as pd
from typing import Dict, List, Any, Optional

class TrafficDemandManager:
    PROVENANCE_LEVELS = ["ACTUAL", "EXTERNAL", "MEASURED", "ESTIMATED", "SYNTHETIC"]

    def __init__(self, synthetic_dir: str = "data/synthetic"):
        self.synthetic_dir = synthetic_dir
        os.makedirs(self.synthetic_dir, exist_ok=True)

    def generate_synthetic_profile(
        self,
        graph_nodes: List[str],
        profile_type: str = "MORNING_PEAK",
        base_volume: float = 1200.0
    ) -> Dict[str, Any]:
        """
        Generates controlled synthetic demand distributions across network nodes.
        Strictly tagged as SYNTHETIC.
        """
        if not graph_nodes:
            return {"demands": {}, "provenance": "SYNTHETIC"}

        # Define peak factors
        multiplier = 1.0
        if profile_type == "MORNING_PEAK":
            multiplier = 1.25
        elif profile_type == "EVENING_PEAK":
            multiplier = 1.30
        elif profile_type == "OFF_PEAK":
            multiplier = 0.70
        elif profile_type == "WEEKEND":
            multiplier = 0.85

        scaled_volume = base_volume * multiplier

        # Set origin (source), destination (sink), and intermediate transshipment
        supplies_demands = {n: 0.0 for n in graph_nodes}
        source_node = graph_nodes[0]
        target_node = graph_nodes[-1] if len(graph_nodes) > 1 else graph_nodes[0]

        supplies_demands[source_node] = round(scaled_volume, 1)
        supplies_demands[target_node] = -round(scaled_volume, 1)

        demand_records = []
        for n, val in supplies_demands.items():
            demand_records.append({
                "node_id": n,
                "net_flow_volume": val,
                "flow_role": "ORIGIN_SUPPLY" if val > 0 else ("DESTINATION_DEMAND" if val < 0 else "INTERMEDIATE_TRANSSHIPMENT"),
                "profile_type": profile_type,
                "data_provenance": "SYNTHETIC"
            })

        # Save synthetic benchmark to data/synthetic/
        df_demands = pd.DataFrame(demand_records)
        save_path = os.path.join(self.synthetic_dir, f"demand_profile_{profile_type.lower()}.csv")
        df_demands.to_csv(save_path, index=False)

        return {
            "profile_type": profile_type,
            "hourly_volume_pcu": scaled_volume,
            "supplies_demands": supplies_demands,
            "records": demand_records,
            "data_provenance": "SYNTHETIC",
            "saved_file": save_path
        }

    def load_demand_csv(self, file_path: str, provenance: str = "EXTERNAL") -> Dict[str, Any]:
        """Loads and validates a user-uploaded or external CSV demand matrix."""
        if provenance not in self.PROVENANCE_LEVELS:
            provenance = "EXTERNAL"

        df = pd.read_csv(file_path)
        required_cols = {"node_id", "net_flow_volume"}
        if not required_cols.issubset(df.columns):
            raise ValueError(f"Uploaded demand CSV must contain columns: {required_cols}")

        supplies_demands = dict(zip(df["node_id"], df["net_flow_volume"]))
        balance = sum(supplies_demands.values())

        return {
            "supplies_demands": supplies_demands,
            "total_supply": sum(v for v in supplies_demands.values() if v > 0),
            "total_demand": abs(sum(v for v in supplies_demands.values() if v < 0)),
            "mass_balance_error": round(balance, 2),
            "is_balanced": abs(balance) < 1e-3,
            "data_provenance": provenance
        }

    def create_custom_manual_demand(
        self,
        origin_node: str,
        destination_node: str,
        volume_pcu_hr: float,
        provenance: str = "MEASURED"
    ) -> Dict[str, Any]:
        """Creates a custom user-entered origin-destination demand vector."""
        if provenance not in self.PROVENANCE_LEVELS:
            provenance = "MEASURED"

        supplies_demands = {
            origin_node: float(volume_pcu_hr),
            destination_node: -float(volume_pcu_hr)
        }

        return {
            "supplies_demands": supplies_demands,
            "origin": origin_node,
            "destination": destination_node,
            "volume_pcu_hr": volume_pcu_hr,
            "is_balanced": True,
            "data_provenance": provenance
        }
