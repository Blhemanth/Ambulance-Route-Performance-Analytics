"""
Unit Tests for Task 4: Hospital-to-Road Network Snapping and Spatial Access.
Ambulance Route Optimization — Bengaluru.
"""

import unittest
import os
import json
import pandas as pd
from src.network.hospital_snapper import HospitalRoadSnapper, haversine_distance_m, distance_point_to_segment_m

class TestNetworkSnapping(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.snapper = HospitalRoadSnapper(
            intersections_path="data/processed/intersections_gis.csv",
            roads_gis_path="data/processed/roads_gis.json",
            default_threshold_m=2000.0
        )
        cls.hosp_csv_path = "data/processed/bengaluru_hospitals.csv"
        cls.df_hospitals = pd.read_csv(cls.hosp_csv_path)
        cls.df_connections = cls.snapper.snap_all_hospitals(cls.df_hospitals)

    def test_point_to_segment_distance(self):
        """Test 1: Equirectangular projection perpendicular distance calculation."""
        # Horizontal road segment from (12.9700, 77.5900) to (12.9700, 77.6000)
        # Point P at (12.9710, 77.5950) -> ~110.5 meters north of midpoint
        dist, proj_lat, proj_lon = distance_point_to_segment_m(
            12.9710, 77.5950,
            12.9700, 77.5900,
            12.9700, 77.6000
        )
        self.assertAlmostEqual(dist, 110.5, delta=15.0)
        self.assertAlmostEqual(proj_lat, 12.9700, places=4)
        self.assertAlmostEqual(proj_lon, 77.5950, places=4)

    def test_road_node_matching(self):
        """Test 2: Ensure valid candidate node matching."""
        sample = self.df_connections.iloc[0]
        self.assertIsNotNone(sample["nearest_intersection_id"])
        self.assertTrue(sample["nearest_intersection_id"].startswith("INT_"))
        self.assertGreater(sample["distance_to_intersection_m"], 0.0)

    def test_snapping_distance_accuracy(self):
        """Test 3: Snapping distance must equal min(node_dist, edge_dist)."""
        for _, row in self.df_connections.dropna(subset=["snapping_distance_m"]).head(50).iterrows():
            d_node = row["distance_to_intersection_m"]
            d_edge = row["distance_to_road_edge_m"]
            d_snap = row["snapping_distance_m"]
            expected = round(min(d_node, d_edge), 1)
            self.assertAlmostEqual(d_snap, expected, delta=0.5)

    def test_maximum_snapping_threshold(self):
        """Test 4: Snapping threshold correctly tags connections > 2000m."""
        exceeds = self.df_connections[self.df_connections["exceeds_threshold"]]
        self.assertGreater(len(exceeds), 0)
        for _, row in exceeds.iterrows():
            if pd.notna(row["snapping_distance_m"]):
                self.assertGreater(row["snapping_distance_m"], 2000.0)
                self.assertEqual(row["connection_status"], "UNMATCHED_EXCEEDS_THRESHOLD")

    def test_unmatched_hospital_handling(self):
        """Test 5: Graceful handling of invalid or unmatchable coordinates."""
        res_invalid = self.snapper.snap_single_hospital(
            hosp_lat=None,
            hosp_lon=None,
            hosp_id="BLR_HOSP_TEST",
            hosp_name="Test Invalid",
            emergency_status="INCOMPLETE_OR_QUESTIONABLE"
        )
        self.assertEqual(res_invalid["connection_status"], "UNMATCHED_INVALID_GEOMETRY")
        self.assertTrue(res_invalid["exceeds_threshold"])
        self.assertIsNone(res_invalid["snapping_distance_m"])

    def test_hospital_to_road_identifier_consistency(self):
        """Test 6: Verify matched node IDs exist in intersections dataset."""
        valid_nodes = set(self.snapper.df_intersections["intersection_id"].unique())
        matched_hospitals = self.df_connections.dropna(subset=["nearest_intersection_id"])
        for _, row in matched_hospitals.iterrows():
            self.assertIn(row["nearest_intersection_id"], valid_nodes)

    def test_access_penalty_time(self):
        """Test 7: Estimated access time is positive and realistic."""
        matched = self.df_connections[~self.df_connections["exceeds_threshold"]]
        for _, row in matched.head(30).iterrows():
            t_acc = row["estimated_access_time_min"]
            self.assertIsNotNone(t_acc)
            self.assertGreaterEqual(t_acc, 1.0) # >= 1 minute minimum entrance gate delay

    def test_connection_output_file(self):
        """Test 8: hospital_road_connections.csv is exported properly."""
        out_csv = "data/processed/hospital_road_connections.csv"
        self.assertTrue(os.path.exists(out_csv))
        df_out = pd.read_csv(out_csv)
        self.assertEqual(len(df_out), 1084)
        required_cols = [
            "hospital_id", "hospital_name", "nearest_intersection_id",
            "nearest_road_edge_id", "snapping_distance_m", "connection_status",
            "estimated_access_time_min", "exceeds_threshold"
        ]
        for col in required_cols:
            self.assertIn(col, df_out.columns)

if __name__ == "__main__":
    unittest.main()
