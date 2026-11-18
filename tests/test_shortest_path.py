import unittest
import networkx as nx
from src.network.shortest_path import ShortestPathOptimizer

class TestShortestPath(unittest.TestCase):
    def setUp(self):
        # Create test corridor:
        # A -> B (cost 4), A -> C (cost 2)
        # B -> D (cost 5), C -> B (cost 1), C -> D (cost 8)
        self.G = nx.DiGraph()
        for n in ["A", "B", "C", "D"]:
            self.G.add_node(n, name=f"Junction {n}")

        self.G.add_edge("A", "B", cost=4.0, length_m=1000.0, free_flow_time_min=3.0, signal_delay_min=1.0)
        self.G.add_edge("A", "C", cost=2.0, length_m=600.0, free_flow_time_min=1.5, signal_delay_min=0.5)
        self.G.add_edge("B", "D", cost=5.0, length_m=1200.0, free_flow_time_min=3.5, signal_delay_min=1.5)
        self.G.add_edge("C", "B", cost=1.0, length_m=300.0, free_flow_time_min=0.8, signal_delay_min=0.2)
        self.G.add_edge("C", "D", cost=8.0, length_m=2000.0, free_flow_time_min=6.0, signal_delay_min=2.0)

        self.optimizer = ShortestPathOptimizer(self.G)

    def test_dijkstra_shortest_path(self):
        res = self.optimizer.find_shortest_path("A", "D", weight_metric="cost")
        self.assertEqual(res["status"], "OPTIMAL")
        # Optimal path should be A -> C -> B -> D with cost 2 + 1 + 5 = 8.0
        self.assertEqual(res["path_nodes"], ["A", "C", "B", "D"])
        self.assertAlmostEqual(res["total_path_cost"], 8.0)

    def test_route_comparison(self):
        # Create optimized graph with lower signal delay on A -> B -> D
        G_opt = self.G.copy()
        G_opt["A"]["B"]["signal_delay_min"] = 0.2
        G_opt["A"]["B"]["cost"] = G_opt["A"]["B"]["free_flow_time_min"] + 0.2 # 3.0 + 0.2 = 3.2
        G_opt["B"]["D"]["signal_delay_min"] = 0.3
        G_opt["B"]["D"]["cost"] = G_opt["B"]["D"]["free_flow_time_min"] + 0.3 # 3.5 + 0.3 = 3.8

        comp = self.optimizer.compare_routes("A", "D", self.G, G_opt)
        self.assertEqual(comp["status"], "SUCCESS")
        self.assertGreater(comp["time_savings_min"], 0.0)
        self.assertGreater(comp["percentage_time_savings"], 0.0)

if __name__ == "__main__":
    unittest.main()
