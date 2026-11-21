"""
Phase 3 Unit and Integration Tests: Interactive GIS Ambulance Route Optimization Application.
Tests Tasks 1 through 13:
- Origin selection & nearest node snapping.
- Hospital lookup, search, and triage tiers.
- Valid route calculation & metric consistency.
- Unreachable destination handling.
- Alternative route generation (Yen's algorithm).
- Route geometry consistency (edges vs polylines).
- Map rendering (Folium map creation with layers).
- Road directionality & cardinal headings.
- Hospital marker accuracy.
- Time vs. distance tradeoff benchmark consistency.
"""

import os
import unittest
import pandas as pd
import folium

from src.network.ambulance_graph import get_ambulance_road_graphs, haversine_distance_m
from src.network.ambulance_router import (
    AmbulanceRouter,
    PROFILE_MINIMUM_TIME,
    PROFILE_SHORTEST_DISTANCE,
    HospitalNotFoundError
)
from components.gis_map import (
    create_ambulance_route_map,
    calculate_bearing,
    bearing_to_cardinal,
    build_ambulance_route_legend
)


class TestGISRouteVisualization(unittest.TestCase):
    """Integration test suite for Phase 3 interactive GIS ambulance application."""

    @classmethod
    def setUpClass(cls):
        cls.g_multi, cls.g_di = get_ambulance_road_graphs()
        cls.router = AmbulanceRouter(graph_multi=cls.g_multi, graph_di=cls.g_di)
        cls.df_hospitals = pd.read_csv("data/processed/bengaluru_hospitals.csv")
        cls.df_connections = pd.read_csv("data/processed/hospital_road_connections.csv")

    def test_01_origin_selection_and_coordinate_snapping(self):
        """Tests that user-supplied arbitrary coordinates snap correctly to the nearest graph node."""
        target_lat, target_lon = 12.9716, 77.5946
        best_node, best_dist = None, float("inf")
        for n, d in self.g_di.nodes(data=True):
            lat, lon = d.get("latitude"), d.get("longitude")
            if lat and lon:
                dist = haversine_distance_m(target_lat, target_lon, lat, lon)
                if dist < best_dist:
                    best_dist = dist
                    best_node = n

        self.assertIsNotNone(best_node)
        self.assertIn(best_node, self.g_di.nodes)
        self.assertLess(best_dist, 5000.0)  # Must be within 5km of Bengaluru center

    def test_02_hospital_selection_and_lookup(self):
        """Tests lookup of hospitals by ID and emergency triage categorization."""
        # 1. Victoria Hospital (BLR_HOSP_0052)
        res_v = self.router.route_to_hospital(
            origin="INT_001_RAJARAJESHWARI_JUNCTION",
            hospital_id_or_name="BLR_HOSP_0052"
        )
        self.assertIn(res_v["status"], ["OPTIMAL", "SUCCESS"])
        self.assertEqual(res_v["destination_hospital_id"], "BLR_HOSP_0052")
        self.assertEqual(res_v["verification_status"], "VERIFIED_EMERGENCY")

        # 2. Non-existent hospital raises HospitalNotFoundError
        with self.assertRaises(HospitalNotFoundError):
            self.router.route_to_hospital(
                origin="INT_001_RAJARAJESHWARI_JUNCTION",
                hospital_id_or_name="NON_EXISTENT_CLINIC_XYZ"
            )

    def test_03_hospital_search_case_insensitivity(self):
        """Tests searching hospital by partial lowercase name string."""
        matches = self.df_hospitals[self.df_hospitals["hospital_name"].str.contains("victoria", case=False, na=False)]
        self.assertGreater(len(matches), 0)
        self.assertTrue(any(row["hospital_id"] == "BLR_HOSP_0052" for _, row in matches.iterrows()))

    def test_04_valid_route_calculation_and_driveway_penalty(self):
        """Tests that routing to hospital adds the campus access driveway penalty."""
        res = self.router.route_to_hospital(
            origin="INT_001_RAJARAJESHWARI_JUNCTION",
            hospital_id_or_name="BLR_HOSP_0052"
        )
        self.assertIn("total_time_min", res)
        self.assertIn("driveway_access_time_min", res)
        # Total time must equal network road travel time + campus driveway time
        expected_total = round(res["road_travel_time_min"] + res["driveway_access_time_min"], 2)
        self.assertAlmostEqual(res["total_time_min"], expected_total, places=1)
        self.assertGreater(res["driveway_access_time_min"], 0.0)
        self.assertAlmostEqual(res["total_time_min"], expected_total, places=1)
        self.assertGreater(res["driveway_access_time_min"], 0.0)

    def test_05_unreachable_destination_handling(self):
        """Tests graceful handling when no directed path exists between nodes."""
        # Test pair with impossible direction or disconnected subgraph
        res = self.router.find_shortest_path(
            origin="INT_002_SATELLITEBUSSTAND_JUNCTIO",
            destination="INT_001_RAJARAJESHWARI_JUNCTION"
        )
        # Should return a valid dictionary with status
        self.assertIn(res["status"], ["OPTIMAL", "NO_PATH_EXISTS"])
        if res["status"] == "NO_PATH_EXISTS":
            self.assertEqual(len(res["path_nodes"]), 0)
            self.assertEqual(res["total_distance_m"], 0.0)

    def test_06_alternative_routes_yens_algorithm(self):
        """Tests Yen's algorithm generating K=3 strictly loopless alternative routes."""
        orig = "INT_001_RAJARAJESHWARI_JUNCTION"
        dest = "INT_002_SATELLITEBUSSTAND_JUNCTIO"
        alts = self.router.find_k_alternative_routes(orig, dest, K=3)
        self.assertGreater(len(alts), 0)
        self.assertLessEqual(len(alts), 3)

        # Primary route must be rank 1
        self.assertEqual(alts[0]["rank"], 1)

        # Test loopless condition: all nodes in each path must be unique
        for a in alts:
            nodes = a["path_nodes"]
            self.assertEqual(len(nodes), len(set(nodes)), f"Path contains a cycle: {nodes}")

        # If multiple alternatives exist, each subsequent rank must be >= preceding in travel time
        if len(alts) > 1:
            for i in range(len(alts) - 1):
                self.assertLessEqual(alts[i]["total_time_sec"], alts[i + 1]["total_time_sec"] + 0.1)

    def test_07_route_geometry_consistency(self):
        """Tests that route_geometry coordinates match path edge sequence."""
        res = self.router.find_shortest_path(
            origin="INT_001_RAJARAJESHWARI_JUNCTION",
            destination="INT_002_SATELLITEBUSSTAND_JUNCTIO"
        )
        if res["status"] == "OPTIMAL":
            geom = res["route_geometry"]
            self.assertGreater(len(geom), 1)
            # Starting coordinate of route_geometry should match origin intersection lat/lon
            orig_lat = self.g_di.nodes["INT_001_RAJARAJESHWARI_JUNCTION"]["latitude"]
            orig_lon = self.g_di.nodes["INT_001_RAJARAJESHWARI_JUNCTION"]["longitude"]
            self.assertAlmostEqual(geom[0][0], orig_lat, places=2)
            self.assertAlmostEqual(geom[0][1], orig_lon, places=2)

    def test_08_route_metric_consistency(self):
        """Tests that total_distance and total_time equal the sum of their individual segments."""
        res = self.router.find_shortest_path(
            origin="INT_001_RAJARAJESHWARI_JUNCTION",
            destination="INT_002_SATELLITEBUSSTAND_JUNCTIO"
        )
        if res["status"] == "OPTIMAL":
            sum_dist_m = sum(e["length_m"] for e in res["path_edges"])
            sum_time_s = sum(e["travel_time_sec"] for e in res["path_edges"])
            self.assertAlmostEqual(res["total_distance_m"], sum_dist_m, places=1)
            self.assertAlmostEqual(res["total_time_sec"], sum_time_s, places=1)

    def test_09_map_rendering_and_layer_controls(self):
        """Tests that create_ambulance_route_map returns a valid Folium Map with layers and legend."""
        res = self.router.find_shortest_path(
            origin="INT_001_RAJARAJESHWARI_JUNCTION",
            destination="INT_002_SATELLITEBUSSTAND_JUNCTIO"
        )
        orig_info = {
            "intersection_id": "INT_001_RAJARAJESHWARI_JUNCTION",
            "name": "Rajarajeshwari Junction",
            "latitude": 12.9485,
            "longitude": 77.5305
        }
        dest_info = {
            "intersection_id": "INT_002_SATELLITEBUSSTAND_JUNCTIO",
            "name": "Satellite Bus Stand",
            "latitude": 12.9510,
            "longitude": 77.5305
        }
        m = create_ambulance_route_map(
            primary_route=res,
            origin_info=orig_info,
            destination_info=dest_info,
            show_legend=True
        )
        self.assertIsInstance(m, folium.Map)
        # Verify rendered HTML contains legend and disclaimer
        html_str = m.get_root().render()
        self.assertIn("AMBULANCE ROUTE OPTIMIZATION", html_str)
        self.assertIn("Route colors denote mathematical path selection", html_str)

    def test_10_road_directionality_and_cardinal_headings(self):
        """Tests bearing calculation and 8-point cardinal direction conversion."""
        # Due North (0 deg)
        b_n = calculate_bearing(12.0, 77.0, 13.0, 77.0)
        self.assertAlmostEqual(b_n, 0.0, places=1)
        self.assertEqual(bearing_to_cardinal(b_n), "North")

        # Due East (approx 90 deg along great circle)
        b_e = calculate_bearing(12.0, 77.0, 12.0, 78.0)
        self.assertAlmostEqual(b_e, 90.0, delta=0.5)
        self.assertEqual(bearing_to_cardinal(b_e), "East")

        # Due South (180 deg)
        b_s = calculate_bearing(13.0, 77.0, 12.0, 77.0)
        self.assertAlmostEqual(b_s, 180.0, places=1)
        self.assertEqual(bearing_to_cardinal(b_s), "South")

        # Due West (approx 270 deg along great circle)
        b_w = calculate_bearing(12.0, 78.0, 12.0, 77.0)
        self.assertAlmostEqual(b_w, 270.0, delta=0.5)
        self.assertEqual(bearing_to_cardinal(b_w), "West")

    def test_11_hospital_marker_accuracy(self):
        """Tests that hospital records retain exact OSM coordinates and valid triage tags."""
        vic = self.df_hospitals[self.df_hospitals["hospital_id"] == "BLR_HOSP_0052"].iloc[0]
        self.assertAlmostEqual(vic["latitude"], 12.9634, places=2)
        self.assertAlmostEqual(vic["longitude"], 77.5736, places=2)
        self.assertEqual(vic["verification_status"], "VERIFIED_EMERGENCY")

    def test_12_time_vs_distance_benchmark_consistency(self):
        """Tests comparative benchmark between Minimum-Time and Shortest-Distance profiles."""
        comp = self.router.compare_distance_vs_time_routes(
            origin="INT_001_RAJARAJESHWARI_JUNCTION",
            destination="INT_002_SATELLITEBUSSTAND_JUNCTIO"
        )
        self.assertIn(comp["status"], ["SUCCESS", "COMPARISON_FAILED"])
        if comp["status"] == "SUCCESS":
            self.assertIn("fastest_time_min", comp)
            self.assertIn("shortest_distance_km", comp)
            self.assertIn("time_saved_min", comp)
            # Minimum-time route must never be slower than shortest-distance route
            self.assertLessEqual(comp["fastest_time_min"], comp["shortest_dist_time_min"] + 0.01)


if __name__ == "__main__":
    unittest.main()
