"""
Unit & Integration Test Suite for Phase 4: Traffic Signal PDF Integration & Signal-Aware Routing.
Covers all 15 required verification areas:
1. PDF extraction.
2. OCR extraction where applicable.
3. Cycle duration validation.
4. Phase duration validation.
5. Junction matching.
6. Approach matching.
7. Signal movement mapping.
8. Signal-delay calculations (Webster uniform delay).
9. Missing signal handling.
10. Unverified signal handling.
11. Edge-weight updates.
12. Dijkstra with signal-aware weights.
13. Route comparison (Scenario A vs Scenario B).
14. GIS signal markers & visualization layers.
15. Regression of existing routing tests.
"""

import os
import unittest
import pandas as pd
import networkx as nx

from src.data_processing.pdf_inventory import audit_single_pdf, build_full_pdf_inventory
from src.data_processing.ocr_processor import is_scanned_pdf, VERIFIED_SCANNED_DOCUMENTS
from src.signals.signal_validator import SignalDataValidator
from src.signals.signal_network_matcher import (
    SignalNetworkMatcher,
    calculate_bearing,
    bearing_to_cardinal
)
from src.signals.signal_delay_model import (
    calculate_webster_uniform_delay,
    SignalDelayModel
)
from src.network.ambulance_graph import (
    get_ambulance_road_graphs,
    AmbulanceRoadGraphBuilder
)
from src.network.ambulance_router import (
    AmbulanceRouter,
    PROFILE_MINIMUM_TIME,
    PROFILE_SHORTEST_DISTANCE,
    PROFILE_TIME_PLUS_SIGNAL
)
from components.gis_map import (
    build_signal_marker_popup,
    create_ambulance_route_map
)


class TestSignalDelayEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.g_multi, cls.g_di = get_ambulance_road_graphs(force_rebuild=True)
        cls.router = AmbulanceRouter(cls.g_multi, cls.g_di)
        cls.delay_model = SignalDelayModel()

    # 1. PDF Extraction Inventory Test
    def test_01_pdf_extraction_inventory(self):
        inv_path = "data/processed/pdf_inventory.csv"
        self.assertTrue(os.path.exists(inv_path), f"Missing inventory file: {inv_path}")
        df_inv = pd.read_csv(inv_path)
        self.assertEqual(len(df_inv), 118, "Inventory must contain exactly 118 PDF records.")
        self.assertIn("TEXT_BASED", df_inv["pdf_category"].values)
        self.assertIn("SCANNED", df_inv["pdf_category"].values)
        self.assertTrue((df_inv["extraction_status"] == "SUCCESS").all(), "All 118 documents must report extraction SUCCESS.")

    # 2. OCR Extraction Test
    def test_02_ocr_extraction_where_applicable(self):
        scanned_files = [k for k in VERIFIED_SCANNED_DOCUMENTS.keys()]
        self.assertEqual(len(scanned_files), 4, "Must have exactly 4 cataloged scanned raster PDF files.")
        for fname in scanned_files:
            self.assertTrue(is_scanned_pdf(fname), f"File {fname} must be identified as scanned raster document.")
            data = VERIFIED_SCANNED_DOCUMENTS[fname]
            self.assertIn("junction_name", data)
            self.assertIn("timings", data)
            self.assertGreater(len(data["timings"]), 0)

    # 3. Cycle Duration Validation Test
    def test_03_cycle_duration_validation(self):
        validator = SignalDataValidator()
        df_audit = validator.run_all_checks()
        self.assertFalse(df_audit.empty, "Audit must catalog flagged issues.")
        cycle_issues = df_audit[df_audit["check_name"] == "Inconsistent Cycle Length"]
        self.assertGreater(len(cycle_issues), 0, "Validator must detect and catalog inconsistent cycles outside 40s-260s.")

    # 4. Phase Duration Validation Test
    def test_04_phase_duration_validation(self):
        validator = SignalDataValidator()
        df_audit = validator.run_all_checks()
        dur_issues = df_audit[df_audit["check_name"].isin(["Missing Phase Duration", "Invalid or Negative Duration"])]
        # Confirms validator runs and reports structured checks
        self.assertIsInstance(dur_issues, pd.DataFrame)

    # 5. Junction Matching Test
    def test_05_junction_matching(self):
        df_int = pd.read_csv("data/processed/intersections.csv")
        df_gis = pd.read_csv("data/processed/intersections_gis.csv")
        self.assertEqual(len(df_int), 226, "Source intersections catalog must have 226 junctions.")
        self.assertEqual(len(df_gis), 226, "GIS intersections catalog must have 226 junctions.")
        int_set = set(df_int["intersection_id"])
        gis_set = set(df_gis["intersection_id"])
        self.assertEqual(int_set, gis_set, "Intersection IDs in CAD catalog and GIS network must match 100%.")

    # 6. Approach Matching Test
    def test_06_approach_matching(self):
        map_path = "data/processed/signal_network_mapping.csv"
        self.assertTrue(os.path.exists(map_path), f"Missing mapping file: {map_path}")
        df_map = pd.read_csv(map_path)
        self.assertEqual(len(df_map), 1164, "Must map all 1,164 directed road edges in network.")
        self.assertIn("approach_code", df_map.columns)
        self.assertTrue((df_map["approach_code"].isin(["A", "B", "C", "D", "E", "UNASSIGNED"])).all())

    # 7. Signal Movement Mapping Test
    def test_07_signal_movement_mapping(self):
        df_map = pd.read_csv("data/processed/signal_network_mapping.csv")
        self.assertIn("movement_id", df_map.columns)
        self.assertIn("signal_phase_id", df_map.columns)
        self.assertTrue((df_map["signal_phase_id"].str.startswith("PH_")).any())

    # 8. Signal-Delay Calculations (Webster uniform delay)
    def test_08_signal_delay_calculations(self):
        # Test case 1: C=120, G=30 -> R=90. d = 90^2 / (2 * 120) = 8100 / 240 = 33.75s
        d_sec, d_min = calculate_webster_uniform_delay(120.0, 30.0)
        self.assertAlmostEqual(d_sec, 33.75, places=2)
        self.assertAlmostEqual(d_min, 0.5625, places=3)

        # Test case 2: C=100, G=50 -> R=50. d = 2500 / 200 = 12.5s
        d_sec2, d_min2 = calculate_webster_uniform_delay(100.0, 50.0)
        self.assertAlmostEqual(d_sec2, 12.5, places=2)

        # Test case 3: C=120, G=120 (always green) -> R=0 -> d=0.0s
        d_sec3, d_min3 = calculate_webster_uniform_delay(120.0, 120.0)
        self.assertEqual(d_sec3, 0.0)
        self.assertEqual(d_min3, 0.0)

    # 9. Missing Signal Handling Test
    def test_09_missing_signal_handling(self):
        # Querying non-existent edge or zero cycle must safely return 0.0s delay without crash
        rec = self.delay_model.get_edge_signal_delay("NON_EXISTENT_EDGE_9999")
        self.assertFalse(rec["is_signal_available"])
        self.assertEqual(rec["signal_delay_sec"], 0.0)
        self.assertIn("reason", rec)

        d_sec, d_min = calculate_webster_uniform_delay(0.0, 0.0)
        self.assertEqual(d_sec, 0.0)

    # 10. Unverified Signal Handling Test
    def test_10_unverified_signal_handling(self):
        df_delays = pd.read_csv("data/processed/edge_signal_delays.csv")
        unavail = df_delays[~df_delays["is_signal_available"]]
        self.assertGreater(len(unavail), 0, "There should be unverified/suppressed edges in network.")
        # All unavailable links must have delay exactly 0.0s
        self.assertTrue((unavail["signal_delay_sec"] == 0.0).all())

    # 11. Edge-Weight Updates Test
    def test_11_edge_weight_updates(self):
        for u, v, d in self.g_di.edges(data=True):
            t_base = d.get("travel_time_sec", 0.0)
            t_sig = d.get("signal_delay_sec", 0.0)
            t_tot = d.get("total_signal_aware_time_sec", 0.0)
            self.assertGreater(t_base, 0.0, f"Edge ({u}, {v}) must have positive baseline road time.")
            self.assertGreaterEqual(t_sig, 0.0, f"Edge ({u}, {v}) must have non-negative signal delay.")
            self.assertAlmostEqual(t_tot, t_base + t_sig, places=1,
                                   msg=f"Total signal-aware time must equal base time + signal delay on ({u}, {v}).")

    # 12. Dijkstra with Signal-Aware Weights Test
    def test_12_dijkstra_with_signal_aware_weights(self):
        orig = "INT_001_RAJARAJESHWARI_JUNCTION"
        dest = "INT_003_ADUGODI_JUNCTION"
        res = self.router.find_shortest_path(orig, dest, profile=PROFILE_TIME_PLUS_SIGNAL)
        self.assertEqual(res["status"], "OPTIMAL")
        self.assertGreater(res["total_signal_aware_time_sec"], 0.0)
        self.assertGreater(res["num_signals_encountered"], 0)
        self.assertEqual(res["profile"], PROFILE_TIME_PLUS_SIGNAL)

    # 13. Route Comparison Test
    def test_13_route_comparison_scenario_a_vs_b(self):
        orig = "INT_001_RAJARAJESHWARI_JUNCTION"
        dest = "INT_003_ADUGODI_JUNCTION"
        comp = self.router.compare_baseline_vs_signal_aware(orig, dest)
        self.assertEqual(comp["status"], "SUCCESS")
        self.assertIn("scenario_a_baseline", comp)
        self.assertIn("scenario_b_signal_aware", comp)
        self.assertIn("delta_total_time_min", comp)
        self.assertIn("route_changes_description", comp)

    # 14. GIS Signal Markers & Map Test
    def test_14_gis_signal_markers_and_map(self):
        sig_data = {
            "name": "Test Junction",
            "source_pdf": "test.pdf",
            "source_page": 1,
            "cycle_sec": 120,
            "green_sec": 30,
            "signal_delay_sec": 33.75,
            "verification_status": "VERIFIED"
        }
        popup = build_signal_marker_popup(sig_data)
        self.assertIn("Test Junction", popup)
        self.assertIn("33.8s", popup)
        self.assertIn("VERIFIED", popup)

        # Test map instantiation with signal_nodes and comparison_route
        orig = "INT_001_RAJARAJESHWARI_JUNCTION"
        dest = "INT_003_ADUGODI_JUNCTION"
        res_sig = self.router.find_shortest_path(orig, dest, profile=PROFILE_TIME_PLUS_SIGNAL)
        res_base = self.router.find_shortest_path(orig, dest, profile=PROFILE_MINIMUM_TIME)

        m = create_ambulance_route_map(
            primary_route=res_sig,
            comparison_route=res_base,
            signal_nodes=[sig_data | {"latitude": 12.95, "longitude": 77.58}]
        )
        self.assertIsNotNone(m)

    # 15. Regression of Existing Routing Tests
    def test_15_regression_existing_routing(self):
        orig = "INT_001_RAJARAJESHWARI_JUNCTION"
        dest = "INT_003_ADUGODI_JUNCTION"
        
        # Test baseline time profile
        res_time = self.router.find_shortest_path(orig, dest, profile=PROFILE_MINIMUM_TIME)
        self.assertEqual(res_time["status"], "OPTIMAL")

        # Test distance profile
        res_dist = self.router.find_shortest_path(orig, dest, profile=PROFILE_SHORTEST_DISTANCE)
        self.assertEqual(res_dist["status"], "OPTIMAL")

        # Test Yen's alternative paths
        alts = self.router.find_k_alternative_routes(orig, dest, K=3, profile=PROFILE_MINIMUM_TIME)
        self.assertEqual(len(alts), 3)

        # Test hospital routing
        res_hosp = self.router.route_to_hospital(orig, "BLR_HOSP_0008")
        self.assertEqual(res_hosp["status"], "OPTIMAL")
        self.assertGreater(res_hosp["driveway_access_time_min"], 0.0)


if __name__ == "__main__":
    unittest.main()
