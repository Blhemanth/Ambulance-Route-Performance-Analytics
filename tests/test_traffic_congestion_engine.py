"""
Unit and Integration Test Suite for Phase 5:
Traffic Data Integration, BPR Congestion Modeling, and Scenario Analysis.
Ambulance Route Optimization — Bengaluru.
"""

import os
import unittest
import pandas as pd
import networkx as nx

from src.traffic.congestion_model import calculate_bpr_travel_time, TrafficCongestionModel
from src.network.ambulance_graph import get_ambulance_road_graphs
from src.network.ambulance_router import (
    AmbulanceRouter,
    PROFILE_MINIMUM_TIME,
    PROFILE_SHORTEST_DISTANCE,
    PROFILE_TIME_PLUS_SIGNAL,
    PROFILE_MODERATE_CONGESTION,
    PROFILE_HEAVY_CONGESTION,
    PROFILE_COMBINED_TRAFFIC_SIGNAL
)
from src.analytics.traffic_scenario_experiments import run_traffic_scenario_experiments


class TestTrafficCongestionEngine(unittest.TestCase):
    """Test suite covering Phase 5 congestion modeling and scenario optimization."""

    @classmethod
    def setUpClass(cls):
        """Build graphs and router once for the test suite."""
        cls.g_multi, cls.g_di = get_ambulance_road_graphs()
        cls.router = AmbulanceRouter(cls.g_multi, cls.g_di)
        cls.sample_origin = "INT_001_RAJARAJESHWARI_JUNCTION"
        cls.sample_destination = "INT_103_ANANDRAO_JUNCTION"
        cls.sample_hospital = "BLR_HOSP_0052"

    def test_01_traffic_inventory_file_exists(self):
        """Verifies the audited traffic data inventory catalog exists and has required metadata."""
        inv_path = "data/processed/bengaluru_traffic_data_inventory.csv"
        self.assertTrue(os.path.exists(inv_path), f"Missing {inv_path}")
        df = pd.read_csv(inv_path)
        self.assertGreaterEqual(len(df), 5, "Expected at least 5 audited data sources.")
        expected_cols = ["dataset_id", "dataset_name", "source_organization", "format", "measurement_type", "suitability_assessment"]
        for col in expected_cols:
            self.assertIn(col, df.columns, f"Missing column {col} in inventory")

    def test_02_traffic_scenarios_file_exists(self):
        """Verifies the 4,656 scenario records exist across all network road links."""
        scen_path = "data/processed/network_congestion_scenarios.csv"
        self.assertTrue(os.path.exists(scen_path), f"Missing {scen_path}")
        df = pd.read_csv(scen_path)
        self.assertEqual(len(df), 4656, "Expected exactly 4,656 link scenario records (1,164 links x 4 scenarios).")
        scenarios_present = set(df["scenario"].unique())
        expected_scenarios = {"BASELINE_FREE_FLOW", "MODERATE_CONGESTION", "HEAVY_CONGESTION", "COMBINED_TRAFFIC_SIGNAL"}
        self.assertEqual(scenarios_present, expected_scenarios)

    def test_03_bpr_congestion_delay_positive_non_decreasing(self):
        """Verifies BPR volume-delay formulation is non-negative and monotonically non-decreasing with v/c."""
        t0 = 100.0  # seconds
        # Free-flow
        t_ff, d_ff, spd_ff = calculate_bpr_travel_time(t0, length_m=1000.0, free_flow_speed_kmh=36.0, vc_ratio=0.0)
        self.assertEqual(t_ff, t0)
        self.assertEqual(d_ff, 0.0)

        # Moderate congestion
        t_mod, d_mod, spd_mod = calculate_bpr_travel_time(t0, length_m=1000.0, free_flow_speed_kmh=36.0, vc_ratio=0.65)
        self.assertGreater(t_mod, t0)
        self.assertGreater(d_mod, 0.0)

        # Heavy congestion
        t_hvy, d_hvy, spd_hvy = calculate_bpr_travel_time(t0, length_m=1000.0, free_flow_speed_kmh=36.0, vc_ratio=1.05)
        self.assertGreater(t_hvy, t_mod)
        self.assertGreater(d_hvy, d_mod)

    def test_04_non_double_counting_invariant(self):
        """Verifies strictly that link travel time, traffic delay, and signal delay are decoupled and sum correctly."""
        df = pd.read_csv("data/processed/network_congestion_scenarios.csv")
        df_comb = df[df["scenario"] == "COMBINED_TRAFFIC_SIGNAL"]
        for _, row in df_comb.head(100).iterrows():
            ff = float(row["free_flow_time_sec"])
            traff = float(row["traffic_delay_sec"])
            sig = float(row["signal_delay_sec"])
            tot = float(row["total_time_sec"])
            expected = round(ff + traff + sig, 2)
            self.assertAlmostEqual(tot, expected, places=1, msg=f"Double-counting or mismatch on edge {row['edge_id']}")

    def test_05_edge_weight_non_negativity(self):
        """Confirms that all graph edge attributes for all scenarios are finite, non-negative, and strictly > 0."""
        for u, v, data in self.g_di.edges(data=True):
            for metric in ["time_baseline_sec", "time_moderate_sec", "time_heavy_sec", "time_combined_sec"]:
                val = data.get(metric)
                self.assertIsNotNone(val, f"Edge ({u}, {v}) missing {metric}")
                self.assertGreater(val, 0.0, f"Edge ({u}, {v}) has non-positive {metric}: {val}")
                self.assertFalse(pd.isna(val), f"Edge ({u}, {v}) has NaN {metric}")

    def test_06_router_supports_phase5_profiles(self):
        """Confirms router maps Phase 5 profile identifiers to the appropriate edge weight metrics."""
        self.assertEqual(self.router.get_weight_metric_for_profile(PROFILE_MODERATE_CONGESTION), "time_moderate_sec")
        self.assertEqual(self.router.get_weight_metric_for_profile(PROFILE_HEAVY_CONGESTION), "time_heavy_sec")
        self.assertEqual(self.router.get_weight_metric_for_profile(PROFILE_COMBINED_TRAFFIC_SIGNAL), "time_combined_sec")

    def test_07_dijkstra_heavy_congestion_solves(self):
        """Confirms Dijkstra shortest path executes under heavy congestion profile."""
        res = self.router.find_shortest_path(self.sample_origin, self.sample_destination, profile=PROFILE_HEAVY_CONGESTION)
        self.assertEqual(res["status"], "OPTIMAL")
        self.assertGreater(res["total_time_min"], 0.0)
        self.assertGreater(res["total_traffic_delay_sec"], 0.0)
        self.assertGreater(len(res["path_nodes"]), 1)

    def test_08_dijkstra_combined_traffic_signal_solves(self):
        """Confirms Dijkstra shortest path executes under combined traffic and signal delay profile."""
        res = self.router.find_shortest_path(self.sample_origin, self.sample_destination, profile=PROFILE_COMBINED_TRAFFIC_SIGNAL)
        self.assertEqual(res["status"], "OPTIMAL")
        self.assertGreater(res["total_time_min"], 0.0)
        self.assertGreater(len(res["path_edges"]), 0)

    def test_09_compare_traffic_scenarios_structure(self):
        """Confirms compare_traffic_scenarios returns structured results for all 5 scenarios."""
        comp = self.router.compare_traffic_scenarios(self.sample_origin, self.sample_destination)
        self.assertEqual(comp["status"], "SUCCESS")
        self.assertEqual(len(comp["scenarios"]), 5)
        for k in ["BASELINE_FREE_FLOW", "SHORTEST_DISTANCE", "MODERATE_CONGESTION", "HEAVY_CONGESTION", "COMBINED_TRAFFIC_SIGNAL"]:
            self.assertIn(k, comp["scenarios"])
        self.assertIsInstance(comp["comparison_table"], pd.DataFrame)
        self.assertEqual(len(comp["comparison_table"]), 5)

    def test_10_compare_hospital_scenarios_structure(self):
        """Confirms compare_hospital_scenarios incorporates campus driveway access delay."""
        comp = self.router.compare_hospital_scenarios(self.sample_origin, self.sample_hospital)
        self.assertEqual(comp["status"], "SUCCESS")
        self.assertEqual(comp["hospital_id"], self.sample_hospital)
        self.assertGreater(comp["driveway_access_distance_m"], 0.0)
        self.assertGreater(comp["driveway_access_time_min"], 0.0)
        self.assertEqual(len(comp["scenarios"]), 5)

    def test_11_heavy_congestion_greater_than_baseline(self):
        """Confirms that heavy peak congestion travel time is strictly greater than free-flow baseline."""
        res_base = self.router.find_shortest_path(self.sample_origin, self.sample_destination, profile=PROFILE_MINIMUM_TIME)
        res_hvy = self.router.find_shortest_path(self.sample_origin, self.sample_destination, profile=PROFILE_HEAVY_CONGESTION)
        self.assertGreater(res_hvy["total_time_min"], res_base["total_time_min"], "Heavy congestion time should exceed free flow baseline.")

    def test_12_combined_greater_than_or_equal_to_heavy(self):
        """Confirms combined (congestion + signals) travel time is >= heavy congestion alone."""
        res_hvy = self.router.find_shortest_path(self.sample_origin, self.sample_destination, profile=PROFILE_HEAVY_CONGESTION)
        res_comb = self.router.find_shortest_path(self.sample_origin, self.sample_destination, profile=PROFILE_COMBINED_TRAFFIC_SIGNAL)
        self.assertGreaterEqual(res_comb["total_time_min"], res_hvy["total_time_min"], "Combined time should be >= heavy congestion time.")

    def test_13_traffic_experiment_results_csv_exists(self):
        """Verifies traffic_scenario_experiment_results.csv exists and has 10 evaluated corridor rows."""
        csv_path = "data/processed/traffic_scenario_experiment_results.csv"
        if not os.path.exists(csv_path):
            run_traffic_scenario_experiments(csv_path)
        self.assertTrue(os.path.exists(csv_path))
        df = pd.read_csv(csv_path)
        self.assertEqual(len(df), 10)
        self.assertIn("heavy_vs_base_time_increase_pct", df.columns)
        self.assertIn("combined_total_time_min", df.columns)


if __name__ == "__main__":
    unittest.main()
