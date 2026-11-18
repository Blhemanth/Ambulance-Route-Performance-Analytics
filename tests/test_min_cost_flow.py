import unittest
import networkx as nx
from src.network.minimum_cost_flow import MinimumCostFlowOptimizer

class TestMinimumCostFlow(unittest.TestCase):
    def setUp(self):
        # Create standard test transshipment network
        # 1 (Supply 20) -> 2 (cap 15, cost 2), 1 -> 3 (cap 10, cost 5)
        # 2 -> 4 (cap 10, cost 3), 3 -> 4 (cap 15, cost 1), 2 -> 3 (cap 5, cost 1)
        # 4 (Demand 20)
        self.G = nx.DiGraph()
        self.G.add_node("1", name="Origin 1")
        self.G.add_node("2", name="Hub 2")
        self.G.add_node("3", name="Hub 3")
        self.G.add_node("4", name="Destination 4")

        self.G.add_edge("1", "2", effective_capacity=15.0, cost=2.0, road_name="Link 1-2")
        self.G.add_edge("1", "3", effective_capacity=10.0, cost=5.0, road_name="Link 1-3")
        self.G.add_edge("2", "4", effective_capacity=10.0, cost=3.0, road_name="Link 2-4")
        self.G.add_edge("3", "4", effective_capacity=15.0, cost=1.0, road_name="Link 3-4")
        self.G.add_edge("2", "3", effective_capacity=5.0, cost=1.0, road_name="Link 2-3")

        self.optimizer = MinimumCostFlowOptimizer(self.G)

    def test_mass_balance_validation(self):
        # Unbalanced demand should raise ValueError
        unbalanced = {"1": 20.0, "2": 0.0, "3": 0.0, "4": -15.0}
        with self.assertRaises(ValueError):
            self.optimizer.solve(unbalanced)

    def test_min_cost_flow_optimality(self):
        balanced = {"1": 20.0, "2": 0.0, "3": 0.0, "4": -20.0}
        res = self.optimizer.solve(balanced)
        self.assertEqual(res["status"], "OPTIMAL")
        self.assertGreater(res["total_system_cost_veh_min"], 0.0)
        self.assertEqual(res["total_flow_volume"], 45.0) # Sum of link flows across all transshipment edges

    def test_capacity_and_conservation(self):
        balanced = {"1": 20.0, "2": 0.0, "3": 0.0, "4": -20.0}
        res = self.optimizer.solve(balanced)
        flow_dict = res["flow_dict"]

        # Check edge capacity bounds
        for u, v, d in self.G.edges(data=True):
            f = flow_dict[u][v]
            cap = d["effective_capacity"]
            self.assertLessEqual(f, cap)
            self.assertGreaterEqual(f, 0)

        # Check node mass balance at transshipment node 2 (b_2 = 0)
        net_flow_2 = sum(flow_dict[u]["2"] for u in self.G.predecessors("2")) - sum(flow_dict["2"][v] for v in self.G.successors("2"))
        self.assertEqual(net_flow_2, 0)

if __name__ == "__main__":
    unittest.main()
