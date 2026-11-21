"""
Deterministic Reference Graph & Algorithm Validation Test Suite.
Ambulance Route Optimization — Bengaluru.
Phase 6 — Task 3: Mathematical & Algorithmic Validation.

Validates:
1. Binary Shortest Path Integer Programming Flow Conservation.
2. Optimality of Dijkstra's algorithm against deterministic reference graphs with known optima.
3. Strict enforcement of directed one-way restrictions.
4. Parallel edge resolution (minimum travel-time selection).
5. Unreachable destination handling.
6. Path reconstruction continuity.
"""

import unittest
import networkx as nx
from typing import Dict, List, Any

from src.network.ambulance_graph import get_ambulance_road_graphs
from src.network.ambulance_router import (
    AmbulanceRouter,
    PROFILE_MINIMUM_TIME,
    PROFILE_SHORTEST_DISTANCE
)


class TestReferenceGraphOptimality(unittest.TestCase):
    """Rigorous mathematical tests against reference benchmark graphs."""

    def test_01_deterministic_diamond_graph_optimality(self):
        r"""
        Validates Dijkstra against a canonical diamond reference graph:
        
             B (cost = 2.0)
            / \
           /   \
          A     D
           \   /
            \ /
             C (cost = 5.0)
             
        Path A -> B -> D: cost = 2.0 + 3.0 = 5.0
        Path A -> C -> D: cost = 1.0 + 6.0 = 7.0
        Optimal path must be A -> B -> D with total cost 5.0.
        """
        G = nx.DiGraph()
        G.add_node("A", name="Node A", lat=12.97, lon=77.59)
        G.add_node("B", name="Node B", lat=12.98, lon=77.59)
        G.add_node("C", name="Node C", lat=12.96, lon=77.59)
        G.add_node("D", name="Node D", lat=12.97, lon=77.60)

        G.add_edge("A", "B", travel_time_sec=120.0, length_m=1000.0, speed_kmh=30.0)
        G.add_edge("B", "D", travel_time_sec=180.0, length_m=1500.0, speed_kmh=30.0)
        G.add_edge("A", "C", travel_time_sec=60.0, length_m=500.0, speed_kmh=30.0)
        G.add_edge("C", "D", travel_time_sec=360.0, length_m=3000.0, speed_kmh=30.0)

        router = AmbulanceRouter(graph_di=G)
        res = router.find_shortest_path("A", "D", profile=PROFILE_MINIMUM_TIME)

        self.assertEqual(res["status"], "OPTIMAL")
        self.assertEqual(res["path_nodes"], ["A", "B", "D"])
        self.assertEqual(res["total_time_sec"], 300.0)
        self.assertEqual(res["total_time_min"], 5.0)

    def test_02_directed_one_way_restrictions(self):
        """
        Validates that directed one-way restrictions are strictly enforced.
        If link B -> A does not exist, routing from B to A cannot traverse A <- B directly.
        """
        G = nx.DiGraph()
        G.add_node("A", lat=12.97, lon=77.59)
        G.add_node("B", lat=12.98, lon=77.59)
        G.add_node("C", lat=12.97, lon=77.60)

        # One-way cycle: A -> B -> C -> A
        G.add_edge("A", "B", travel_time_sec=60.0, length_m=500.0, speed_kmh=30.0)
        G.add_edge("B", "C", travel_time_sec=60.0, length_m=500.0, speed_kmh=30.0)
        G.add_edge("C", "A", travel_time_sec=60.0, length_m=500.0, speed_kmh=30.0)

        router = AmbulanceRouter(graph_di=G)
        
        # A to B is direct
        res_ab = router.find_shortest_path("A", "B", profile=PROFILE_MINIMUM_TIME)
        self.assertEqual(res_ab["path_nodes"], ["A", "B"])

        # B to A must route through C due to one-way restriction
        res_ba = router.find_shortest_path("B", "A", profile=PROFILE_MINIMUM_TIME)
        self.assertEqual(res_ba["path_nodes"], ["B", "C", "A"])
        self.assertEqual(res_ba["total_time_sec"], 120.0)

    def test_03_parallel_edge_resolution(self):
        """
        Validates that parallel road links (e.g. flyover vs surface road)
        retain the lower travel-time segment in canonical DiGraph.
        """
        g_multi, g_di = get_ambulance_road_graphs()
        # In Bengaluru network, for any edge (u, v) in g_di, weight must be <= any parallel edge in g_multi
        for u, v in list(g_di.edges())[:50]:
            di_time = g_di[u][v]["travel_time_sec"]
            if g_multi.has_edge(u, v):
                multi_edges = g_multi[u][v]
                min_multi = min(e_data["travel_time_sec"] for e_data in multi_edges.values())
                self.assertAlmostEqual(di_time, min_multi, places=1)

    def test_04_flow_conservation_law_verification(self):
        """
        Verifies that on an optimal Dijkstra path P*, flow conservation holds exactly:
        - Source node s has net divergence = +1
        - Target node t has net divergence = -1
        - Every intermediate junction has net divergence = 0
        """
        g_multi, g_di = get_ambulance_road_graphs()
        router = AmbulanceRouter(g_multi, g_di)
        s = "INT_001_RAJARAJESHWARI_JUNCTION"
        t = "INT_103_ANANDRAO_JUNCTION"

        res = router.find_shortest_path(s, t)
        self.assertEqual(res["status"], "OPTIMAL")
        p = res["path_nodes"]

        # Build path edge indicator x_ij
        path_edges = set(zip(p[:-1], p[1:]))

        # Check conservation for every node in graph
        for node in g_di.nodes():
            outgoing = sum(1 for _, v in path_edges if _ == node)
            incoming = sum(1 for u, _ in path_edges if _ == node)
            divergence = outgoing - incoming

            if node == s:
                self.assertEqual(divergence, 1, f"Source node {s} must have net divergence +1")
            elif node == t:
                self.assertEqual(divergence, -1, f"Destination node {t} must have net divergence -1")
            elif node in p:
                self.assertEqual(divergence, 0, f"Intermediate path node {node} must have net divergence 0")
            else:
                self.assertEqual(divergence, 0, f"Unvisited node {node} must have net divergence 0")

    def test_05_unreachable_destination_handling(self):
        """
        Verifies that when a destination is unreachable, router gracefully returns
        NO_PATH_EXISTS without throwing uncaught exceptions.
        """
        G = nx.DiGraph()
        G.add_node("A", lat=12.97, lon=77.59)
        G.add_node("B", lat=12.98, lon=77.59)
        G.add_node("ISOLATED", lat=12.95, lon=77.55)
        G.add_edge("A", "B", travel_time_sec=60.0, length_m=500.0, speed_kmh=30.0)

        router = AmbulanceRouter(graph_di=G)
        res = router.find_shortest_path("A", "ISOLATED", profile=PROFILE_MINIMUM_TIME)
        self.assertEqual(res["status"], "NO_PATH_EXISTS")
        self.assertEqual(res["total_time_min"], float("inf"))
        self.assertEqual(res["path_nodes"], [])

    def test_06_path_continuity_and_geometry_assembly(self):
        """
        Verifies that the reconstructed path edges form an unbroken chain:
        edge[k].to_node == edge[k+1].from_node for all k.
        """
        g_multi, g_di = get_ambulance_road_graphs()
        router = AmbulanceRouter(g_multi, g_di)
        res = router.find_shortest_path("INT_001_RAJARAJESHWARI_JUNCTION", "INT_003_ADUGODI_JUNCTION")
        edges = res["path_edges"]

        self.assertGreater(len(edges), 1)
        for i in range(len(edges) - 1):
            curr_to = edges[i]["to_node"]
            next_from = edges[i + 1]["from_node"]
            self.assertEqual(curr_to, next_from, f"Broken chain at step {i}: {curr_to} != {next_from}")


if __name__ == "__main__":
    unittest.main()
