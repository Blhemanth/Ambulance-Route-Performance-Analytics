"""
Sensitivity Analysis Module (Scenario C).
Evaluates road network resilience and signal plan stability under traffic demand stress:
- Baseline Demand (1.0x)
- 10% Surge (1.1x)
- 20% Surge (1.2x)
- 30% Surge (1.3x)
"""

import pandas as pd
from typing import Dict, List, Any

from src.network.network_integrator import NetworkIntegrator

class SensitivityAnalyzer:
    def __init__(self, data_dir: Any = "data/processed"):
        if isinstance(data_dir, str):
            self.integrator = NetworkIntegrator(data_dir=data_dir)
        else:
            self.integrator = NetworkIntegrator()

    def run_stress_test(
        self,
        corridor_filter: str = "Corridor 1: South-Central (Adugodi - Koramangala - Wilson Garden - Dairy Circle)",
        multipliers: List[float] = [1.0, 1.10, 1.20, 1.30]
    ) -> Dict[str, Any]:
        """
        Executes multi-scenario sensitivity experiments across demand multipliers.
        Returns tabular summary of throughput, transportation cost, bottleneck count, and queues.
        """
        results_table = []
        detailed_runs = {}

        for mult in multipliers:
            pct_label = f"+{int(round((mult - 1.0) * 100))}%" if mult > 1.0 else "Baseline (1.0x)"
            run_res = self.integrator.run_integrated_pipeline(
                corridor_filter=corridor_filter,
                demand_scale=mult,
                provenance="SYNTHETIC_STRESS_TEST"
            )
            detailed_runs[pct_label] = run_res

            comp = run_res["comparison_matrix"]
            tp_opt = comp["max_flow_throughput_pcu_hr"]["optimized"]
            cost_opt = comp["system_transportation_cost_veh_min"]["optimized"]
            tt_opt = comp["corridor_shortest_path_time_min"]["optimized"]
            q_opt = comp["total_system_residual_queue_veh"]["optimized"]
            avg_delay_sec = round((cost_opt / max(1.0, 1200.0 * mult)) * 60.0, 1)
            num_bn = len(run_res.get("baseline_bottlenecks", []))

            results_table.append({
                "Demand Scenario": pct_label,
                "Demand Multiplier": mult,
                "demand_multiplier": mult,
                "Throughput Baseline (PCU/hr)": comp["max_flow_throughput_pcu_hr"]["baseline"],
                "Throughput Optimized (PCU/hr)": tp_opt,
                "max_throughput_pcu_hr": tp_opt,
                "Throughput Gain (%)": comp["max_flow_throughput_pcu_hr"]["percentage_change"],
                "Cost Baseline (Veh-Min)": comp["system_transportation_cost_veh_min"]["baseline"],
                "Cost Optimized (Veh-Min)": cost_opt,
                "total_system_cost_veh_min": cost_opt,
                "Cost Reduction (%)": abs(comp["system_transportation_cost_veh_min"]["percentage_change"]),
                "Corridor Travel Time Opt (min)": tt_opt,
                "Residual Queue Opt (Veh)": q_opt,
                "average_delay_per_veh_sec": avg_delay_sec,
                "num_bottleneck_edges": num_bn
            })

        df_summary = pd.DataFrame(results_table)

        return {
            "corridor": corridor_filter,
            "multipliers": multipliers,
            "summary_dataframe": df_summary,
            "summary_records": results_table,
            "detailed_runs": detailed_runs
        }
