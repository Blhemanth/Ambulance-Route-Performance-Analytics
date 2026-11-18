import unittest
import networkx as nx
from src.network.maximum_flow import MaximumFlowOptimizer

class TestMaximumFlow(unittest.TestCase):
    def setUp(self):
        # Create standard test diamond network
        # s -> A (cap 10), s -> B (cap 5)
        # A -> t (cap 8), B -> t (cap 7), A -> B (cap 3)
        self.G = nx.DiGraph()
        self.G.add_node("s", name="Source Node")
        self.G.add_node("A", name="Node A")
        self.G.add_node("B", name="Node B")
        self.G.add_node("t", name="Sink Node")

        self.G.add_edge("s", "A", effective_capacity=10.0, road_name="Link s-A")
        self.G.add_edge("s", "B", effective_capacity=5.0, road_name="Link s-B")
        self.G.add_edge("A", "t", effective_capacity=8.0, road_name="Link A-t")
        self.G.add_edge("B", "t", effective_capacity=7.0, road_name="Link B-t")
        self.G.add_edge("A", "B", effective_capacity=3.0, road_name="Link A-B")

        self.optimizer = MaximumFlowOptimizer(self.G)

    def test_max_flow_calculation(self):
        res = self.optimizer.solve("s", "t", capacity_attribute="effective_capacity")
        self.assertEqual(res["status"], "OPTIMAL")
        # Max flow is 15.0 (s->A=10 splits to A->t=8 and A->B=2; s->B=5 + A->B=2 -> B->t=7)
        self.assertEqual(res["max_flow"], 15.0)
        self.assertTrue(res["max_flow_min_cut_theorem_verified"])

    def test_capacity_constraints(self):
        res = self.optimizer.solve("s", "t", capacity_attribute="effective_capacity")
        flow_dict = res["flow_dict"]
        for u, v, d in self.G.edges(data=True):
            f = flow_dict[u][v]
            cap = d["effective_capacity"]
            self.assertLessEqual(f, cap + 1e-5, f"Flow {f} exceeds capacity {cap} on edge ({u},{v})")
            self.assertGreaterEqual(f, 0.0, f"Flow {f} is negative on edge ({u},{v})")

    def test_flow_conservation(self):
        res = self.optimizer.solve("s", "t", capacity_attribute="effective_capacity")
        flow_dict = res["flow_dict"]
        for node in ["A", "B"]: # Intermediate nodes
            in_flow = sum(flow_dict[u][node] for u in self.G.predecessors(node))
            out_flow = sum(flow_dict[node][v] for v in self.G.successors(node))
            self.assertAlmostEqual(in_flow, out_flow, places=4, msg=f"Flow not conserved at node {node}")

    def test_min_cut_bottlenecks(self):
        res = self.optimizer.solve("s", "t", capacity_attribute="effective_capacity")
        bottlenecks = res["bottleneck_edges"]
        self.assertGreater(len(bottlenecks), 0, "Should identify at least one cut edge")
        for b in bottlenecks:
            self.assertTrue(b["is_saturated"], f"Cut edge {b['from_node']}->{b['to_node']} should be saturated")

if __name__ == "__main__":
    unittest.main()
