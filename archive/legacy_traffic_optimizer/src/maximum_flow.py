"""
Model 1: Maximum Flow Optimization Module.
Formulates and solves the Maximum Flow network optimization problem to determine
maximum sustainable vehicular throughput, saturated cut-edges, and critical
corridor bottlenecks across the Bengaluru road network using NetworkX.
"""

import networkx as nx
from typing import Dict, List, Any, Tuple, Optional

class MaximumFlowOptimizer:
    def __init__(self, graph: nx.DiGraph):
        self.graph = graph

    def solve(
        self,
        source: str,
        target: str,
        capacity_attribute: str = "effective_capacity",
        flow_func: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Solves Maximum Flow from source to target.
        Applies Ford-Fulkerson / Edmonds-Karp via NetworkX.
        Returns maximum throughput, edge flow assignments, saturated bottlenecks,
        and minimum cut partition.
        """
        if source not in self.graph:
            raise ValueError(f"Source node '{source}' not found in network.")
        if target not in self.graph:
            raise ValueError(f"Target node '{target}' not found in network.")
        if source == target:
            raise ValueError("Source and target nodes must be distinct.")

        # Ensure positive integer/float capacities on graph edges
        H = self.graph.copy()
        for u, v, d in H.edges(data=True):
            cap = d.get(capacity_attribute, d.get("physical_capacity", 2400))
            H[u][v]["capacity"] = max(1.0, float(cap))

        # Check path existence
        if not nx.has_path(H, source, target):
            return {
                "max_flow": 0.0,
                "flow_dict": {},
                "bottleneck_edges": [],
                "min_cut_capacity": 0.0,
                "cut_nodes_source": [],
                "cut_nodes_target": [],
                "saturated_edge_count": 0,
                "edge_utilizations": {},
                "status": "DISCONNECTED_NO_PATH"
            }

        # Resolve algorithm function
        selected_flow_func = None
        if isinstance(flow_func, str):
            flow_str = flow_func.lower().strip()
            if flow_str == "boykov_kolmogorov":
                selected_flow_func = nx.algorithms.flow.boykov_kolmogorov
            elif flow_str == "edmonds_karp":
                selected_flow_func = nx.algorithms.flow.edmonds_karp
            elif flow_str == "shortest_augmenting_path":
                selected_flow_func = nx.algorithms.flow.shortest_augmenting_path
            elif flow_str in ["dinitz", "dinic"]:
                selected_flow_func = nx.algorithms.flow.dinitz
        elif callable(flow_func):
            selected_flow_func = flow_func

        # Solve Max Flow and Min Cut
        cut_kwargs = {"capacity": "capacity"}
        flow_kwargs = {"capacity": "capacity"}
        if selected_flow_func is not None:
            cut_kwargs["flow_func"] = selected_flow_func
            flow_kwargs["flow_func"] = selected_flow_func

        cut_value, partition = nx.minimum_cut(H, source, target, **cut_kwargs)
        flow_value, flow_dict = nx.maximum_flow(H, source, target, **flow_kwargs)

        # Partition S (source side) and T (target side)
        reachable, non_reachable = partition

        # Identify saturated cut edges (Bottlenecks)
        bottleneck_edges = []
        edge_utilizations = {}
        for u, v, d in H.edges(data=True):
            cap = d["capacity"]
            assigned_flow = flow_dict.get(u, {}).get(v, 0.0)
            utilization = (assigned_flow / cap) * 100.0 if cap > 0 else 0.0
            edge_utilizations[(u, v)] = {
                "flow": round(assigned_flow, 1),
                "capacity": round(cap, 1),
                "utilization_pct": round(utilization, 1),
                "is_saturated": (assigned_flow >= cap * 0.999),
                "road_name": d.get("road_name", "Arterial Link")
            }

            # Check if edge crosses the cut from reachable to non_reachable
            if u in reachable and v in non_reachable:
                bottleneck_edges.append({
                    "from_node": u,
                    "to_node": v,
                    "from_name": H.nodes[u].get("name", u),
                    "to_name": H.nodes[v].get("name", v),
                    "road_name": d.get("road_name", "Arterial Link"),
                    "capacity": round(cap, 1),
                    "capacity_pcu_hr": round(cap, 1),
                    "flow": round(assigned_flow, 1),
                    "flow_pcu_hr": round(assigned_flow, 1),
                    "is_saturated": (assigned_flow >= cap * 0.999)
                })

        return {
            "max_flow": round(flow_value, 1),
            "min_cut_capacity": round(cut_value, 1),
            "max_flow_min_cut_theorem_verified": (abs(flow_value - cut_value) < 1e-3),
            "flow_dict": flow_dict,
            "bottleneck_edges": bottleneck_edges,
            "cut_nodes_source": list(reachable),
            "cut_nodes_target": list(non_reachable),
            "saturated_edge_count": sum(1 for e in edge_utilizations.values() if e["is_saturated"]),
            "edge_utilizations": edge_utilizations,
            "status": "OPTIMAL"
        }
