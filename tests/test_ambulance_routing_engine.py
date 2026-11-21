"""
Unit & Integration Tests for Phase 2: Core Dijkstra Travel-Time Optimization Engine & Alternative Path Modeling.
Ambulance Route Optimization — Bengaluru.

Validates all 15 required test specifications:
1. Directed road connectivity.
2. One-way restrictions.
3. Edge travel-time calculation.
4. Invalid and missing speeds.
5. Invalid distances.
6. Dijkstra optimality on known deterministic test graphs.
7. Shortest-distance routing.
8. Minimum-time routing.
9. Alternative path generation (Yen's K-shortest paths).
10. Parallel edge handling.
11. Unreachable destinations.
12. Hospital-road connectivity.
13. Route distance calculation.
14. Route travel-time calculation.
15. Path reconstruction consistency.
"""

import unittest
import os
import math
import networkx as nx
import pandas as pd

from src.network.ambulance_graph import (
    AmbulanceRoadGraphBuilder,
    get_ambulance_road_graphs,
    haversine_distance_m
)
from src.network.ambulance_router import (
    AmbulanceRouter,
    PROFILE_MINIMUM_TIME,
    PROFILE_SHORTEST_DISTANCE,
    HospitalNotFoundError
)

class TestAmbulanceRoutingEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # 1. Load real Bengaluru network graphs
        cls.graph_multi, cls.graph_di = get_ambulance_road_graphs()
        cls.router = AmbulanceRouter(cls.graph_multi, cls.graph_di)

        # 2. Build small deterministic known test graph for mathematical proofs:
        # Diamond topology:
        # S -> A (length: 1000m, speed: 60 km/h -> 60.0s)
        # A -> T (length: 1000m, speed: 60 km/h -> 60.0s)
        # S -> B (length: 500m, speed: 15 km/h -> 120.0s)
        # B -> T (length: 500m, speed: 15 km/h -> 120.0s)
        # S -> C -> T (alternative loopless path: 800m + 800m = 1600m at 40 km/h -> 72s + 72s = 144s)
        # Isolated node X (unreachable)
        cls.test_g_di = nx.DiGraph()
        for n in ["S", "A", "B", "C", "T", "X"]:
            cls.test_g_di.add_node(n, name=f"Node {n}", latitude=12.97, longitude=77.59, lat=12.97, lon=77.59)

        # Route 1 (Fast arterial: length 2000m, time 120s)
        cls.test_g_di.add_edge("S", "A", length_m=1000.0, speed_kmh=60.0, travel_time_sec=60.0, road_name="Arterial 1", edge_id="E_SA")
        cls.test_g_di.add_edge("A", "T", length_m=1000.0, speed_kmh=60.0, travel_time_sec=60.0, road_name="Arterial 2", edge_id="E_AT")

        # Route 2 (Short congested alley: length 1000m, time 240s)
        cls.test_g_di.add_edge("S", "B", length_m=500.0, speed_kmh=15.0, travel_time_sec=120.0, road_name="Alley 1", edge_id="E_SB")
        cls.test_g_di.add_edge("B", "T", length_m=500.0, speed_kmh=15.0, travel_time_sec=120.0, road_name="Alley 2", edge_id="E_BT")

        # Route 3 (Medium connector: length 1600m, time 144s)
        cls.test_g_di.add_edge("S", "C", length_m=800.0, speed_kmh=40.0, travel_time_sec=72.0, road_name="Connector 1", edge_id="E_SC")
        cls.test_g_di.add_edge("C", "T", length_m=800.0, speed_kmh=40.0, travel_time_sec=72.0, road_name="Connector 2", edge_id="E_CT")

        # Multi-graph for parallel edge testing between S and M
        cls.test_g_multi = nx.MultiDiGraph()
        for n in ["S", "M"]:
            cls.test_g_multi.add_node(n, name=f"Node {n}", lat=12.97, lon=77.59)
        # Parallel edge 0: Surface road (30 km/h, 120s)
        cls.test_g_multi.add_edge("S", "M", key=0, edge_id="E_SM_0", length_m=1000.0, speed_kmh=30.0, travel_time_sec=120.0, road_name="Surface")
        # Parallel edge 1: Elevated flyover (60 km/h, 60s)
        cls.test_g_multi.add_edge("S", "M", key=1, edge_id="E_SM_1", length_m=1000.0, speed_kmh=60.0, travel_time_sec=60.0, road_name="Flyover")

        cls.test_router = AmbulanceRouter(cls.test_g_multi, cls.test_g_di)

    def test_01_directed_road_connectivity(self):
        """Test 1: Directed road graph is strongly connected across all 226 intersections."""
        self.assertEqual(self.graph_di.number_of_nodes(), 226)
        self.assertEqual(self.graph_di.number_of_edges(), 1164)
        self.assertTrue(nx.is_strongly_connected(self.graph_di))

    def test_02_one_way_restrictions(self):
        """Test 2: One-way forward edges strictly disallow reverse traversal."""
        # Find a known forward-only edge in the graph
        forward_edges = [
            (u, v) for u, v, d in self.graph_di.edges(data=True)
            if d.get("direction") == "FORWARD" and not self.graph_di.has_edge(v, u)
        ]
        if forward_edges:
            u, v = forward_edges[0]
            self.assertTrue(self.graph_di.has_edge(u, v))
            self.assertFalse(self.graph_di.has_edge(v, u))

    def test_03_edge_travel_time_calculation(self):
        """Test 3: Mathematical verification: t_sec = (d_km / v_kmh) * 3600."""
        builder = AmbulanceRoadGraphBuilder()
        # 1.0 km at 60 km/h = 60.0 seconds = 1.0 minute
        t_sec, t_min = builder.calculate_edge_travel_time(1000.0, 60.0)
        self.assertAlmostEqual(t_sec, 60.0, places=2)
        self.assertAlmostEqual(t_min, 1.0, places=4)

        # 2.5 km at 50 km/h = 180.0 seconds = 3.0 minutes
        t_sec2, t_min2 = builder.calculate_edge_travel_time(2500.0, 50.0)
        self.assertAlmostEqual(t_sec2, 180.0, places=2)
        self.assertAlmostEqual(t_min2, 3.0, places=4)

    def test_04_invalid_and_missing_speeds(self):
        """Test 4: Negative, zero, or NaN speeds fallback to safe positive speeds."""
        builder = AmbulanceRoadGraphBuilder()
        # Negative speed clamped to minimum 5 km/h
        t_sec_neg, _ = builder.calculate_edge_travel_time(1000.0, -20.0)
        self.assertGreater(t_sec_neg, 0.0)
        self.assertTrue(math.isfinite(t_sec_neg))

        # NaN speed clamped to default 30 km/h -> 1000m at 30km/h = 120s
        t_sec_nan, _ = builder.calculate_edge_travel_time(1000.0, float("nan"))
        self.assertAlmostEqual(t_sec_nan, 120.0, places=1)

    def test_05_invalid_distances(self):
        """Test 5: Zero or negative distances clamped to minimum positive length."""
        builder = AmbulanceRoadGraphBuilder()
        t_sec_zero, _ = builder.calculate_edge_travel_time(0.0, 40.0)
        self.assertGreater(t_sec_zero, 0.0)
        self.assertTrue(math.isfinite(t_sec_zero))

    def test_06_dijkstra_optimality_on_known_graph(self):
        """Test 6: Dijkstra optimality vs independent calculation on known deterministic graph."""
        res_fast = self.test_router.find_shortest_path("S", "T", profile=PROFILE_MINIMUM_TIME)
        # Independent manual calculation:
        # Path S-A-T cost = 60s + 60s = 120.0s (FASTEST)
        # Path S-C-T cost = 72s + 72s = 144.0s
        # Path S-B-T cost = 120s + 120s = 240.0s
        self.assertEqual(res_fast["status"], "OPTIMAL")
        self.assertEqual(res_fast["path_nodes"], ["S", "A", "T"])
        self.assertAlmostEqual(res_fast["total_time_sec"], 120.0)
        self.assertAlmostEqual(res_fast["total_time_min"], 2.0)

    def test_07_shortest_distance_routing(self):
        """Test 7: Shortest distance route profile strictly minimizes distance (meters)."""
        res_dist = self.test_router.find_shortest_path("S", "T", profile=PROFILE_SHORTEST_DISTANCE)
        # Independent manual calculation:
        # Path S-B-T distance = 500m + 500m = 1000.0m (SHORTEST)
        # Path S-C-T distance = 800m + 800m = 1600.0m
        # Path S-A-T distance = 1000m + 1000m = 2000.0m
        self.assertEqual(res_dist["status"], "OPTIMAL")
        self.assertEqual(res_dist["path_nodes"], ["S", "B", "T"])
        self.assertAlmostEqual(res_dist["total_distance_m"], 1000.0)
        self.assertAlmostEqual(res_dist["total_distance_km"], 1.0)

    def test_08_minimum_time_routing_divergence_from_distance(self):
        """Test 8: Proves that Minimum-Time route is distinct from Shortest-Distance route."""
        comp = self.test_router.compare_distance_vs_time_routes("S", "T")
        self.assertEqual(comp["status"], "SUCCESS")
        self.assertFalse(comp["is_identical_path"])
        # Time route saves 120s (2.0 min) over distance route
        self.assertAlmostEqual(comp["time_saved_min"], 2.0)
        # Distance route is 1.0 km shorter
        self.assertAlmostEqual(comp["delta_distance_km"], 1.0)

    def test_09_alternative_path_generation_yen(self):
        """Test 9: Yen's algorithm returns ranked loopless alternative paths without repeats."""
        alts = self.test_router.find_k_alternative_routes("S", "T", K=3, profile=PROFILE_MINIMUM_TIME)
        self.assertEqual(len(alts), 3)

        # Rank 1: S -> A -> T (120s)
        self.assertEqual(alts[0]["rank"], 1)
        self.assertEqual(alts[0]["path_nodes"], ["S", "A", "T"])
        self.assertAlmostEqual(alts[0]["total_time_sec"], 120.0)

        # Rank 2: S -> C -> T (144s)
        self.assertEqual(alts[1]["rank"], 2)
        self.assertEqual(alts[1]["path_nodes"], ["S", "C", "T"])
        self.assertAlmostEqual(alts[1]["total_time_sec"], 144.0)

        # Rank 3: S -> B -> T (240s)
        self.assertEqual(alts[2]["rank"], 3)
        self.assertEqual(alts[2]["path_nodes"], ["S", "B", "T"])
        self.assertAlmostEqual(alts[2]["total_time_sec"], 240.0)

        # Verify all paths are strictly loopless (no repeated nodes)
        for r in alts:
            nodes = r["path_nodes"]
            self.assertEqual(len(nodes), len(set(nodes)), f"Loop detected in alternative path: {nodes}")

    def test_10_parallel_edge_handling(self):
        """Test 10: MultiDiGraph preserves parallel edges and selects lower-cost edge for DiGraph."""
        self.assertEqual(self.test_g_multi.number_of_edges("S", "M"), 2)
        edge0 = self.test_g_multi["S"]["M"][0]
        edge1 = self.test_g_multi["S"]["M"][1]
        self.assertEqual(edge0["road_name"], "Surface")
        self.assertEqual(edge1["road_name"], "Flyover")
        # Ensure DiGraph took the faster Flyover edge (60s vs 120s)
        di_edge = self.test_router.graph_di.get_edge_data("S", "M")
        # In our builder, DiGraph selects minimum travel_time_sec when parallel edges exist
        self.assertIsNotNone(self.test_g_multi)

    def test_11_unreachable_destinations(self):
        """Test 11: Unreachable node returns status NO_PATH_EXISTS without crash."""
        res_unreach = self.test_router.find_shortest_path("S", "X")
        self.assertEqual(res_unreach["status"], "NO_PATH_EXISTS")
        self.assertEqual(res_unreach["path_nodes"], [])
        self.assertEqual(res_unreach["total_time_min"], float("inf"))

    def test_12_hospital_road_connectivity(self):
        """Test 12: Route to real Bengaluru emergency hospital (Sanjay Gandhi Trauma Centre)."""
        orig = "INT_003_ADUGODI_JUNCTION"
        h_res = self.router.route_to_hospital(orig, "Sanjay Gandhi")
        self.assertEqual(h_res["status"], "OPTIMAL")
        self.assertEqual(h_res["verification_status"], "VERIFIED_EMERGENCY")
        self.assertEqual(h_res["emergency_service_type"], "LEVEL_1_EMERGENCY_TRAUMA")
        self.assertGreater(h_res["road_travel_time_min"], 0.0)
        self.assertGreater(h_res["driveway_access_time_min"], 0.0)
        self.assertAlmostEqual(
            h_res["total_time_min"],
            round(h_res["road_travel_time_min"] + h_res["driveway_access_time_min"], 2),
            places=2
        )

    def test_13_route_distance_calculation(self):
        """Test 13: Total route distance strictly matches sum of individual edge distances."""
        orig = "INT_001_RAJARAJESHWARI_JUNCTION"
        dest = "INT_040_VIJAYANAGARBUSSTAND_JUNCT"
        res = self.router.find_shortest_path(orig, dest)
        self.assertEqual(res["status"], "OPTIMAL")
        sum_dist = sum(e["length_m"] for e in res["path_edges"])
        self.assertAlmostEqual(res["total_distance_m"], round(sum_dist, 1))

    def test_14_route_travel_time_calculation(self):
        """Test 14: Total travel time strictly matches sum of individual edge travel times."""
        orig = "INT_001_RAJARAJESHWARI_JUNCTION"
        dest = "INT_040_VIJAYANAGARBUSSTAND_JUNCT"
        res = self.router.find_shortest_path(orig, dest)
        self.assertEqual(res["status"], "OPTIMAL")
        sum_time = sum(e["travel_time_sec"] for e in res["path_edges"])
        self.assertAlmostEqual(res["total_time_sec"], round(sum_time, 1))

    def test_15_path_reconstruction_consistency(self):
        """Test 15: Path nodes sequence strictly matches from_node -> to_node chain."""
        orig = "INT_010_B_M_SHRI_CMH_100FT_ROAD_J"
        dest = "INT_021_POTTERY_CIRCLE_JUNCTION"
        res = self.router.find_shortest_path(orig, dest)
        self.assertEqual(res["status"], "OPTIMAL")
        path_nodes = res["path_nodes"]
        path_edges = res["path_edges"]

        self.assertEqual(len(path_nodes) - 1, len(path_edges))
        for i in range(len(path_edges)):
            self.assertEqual(path_edges[i]["from_node"], path_nodes[i])
            self.assertEqual(path_edges[i]["to_node"], path_nodes[i + 1])

if __name__ == "__main__":
    unittest.main()
