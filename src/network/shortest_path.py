"""
Model 3: Shortest Path Optimization Module.
Formulates and solves the Shortest Path network optimization problem using Dijkstra's algorithm
to compute minimum-cost vehicular routes between Bengaluru intersections under both baseline
and signal-optimized traffic network impedance conditions.
"""

import networkx as nx
from typing import Dict, List, Any, Tuple, Optional

class ShortestPathOptimizer:
    def __init__(self, graph: nx.DiGraph):
        self.graph = graph

    def find_shortest_path(
        self,
        origin: str,
        destination: str,
        weight_metric: str = "cost",
        weight: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculates shortest path from origin to destination using Dijkstra's algorithm.
        weight_metric: 'cost' (generalized travel time in minutes),
                       'free_flow_time_min', or 'length_m'.
        """
        if weight is not None:
            weight_metric = weight
        if origin not in self.graph:
            raise ValueError(f"Origin intersection '{origin}' not found in network.")
        if destination not in self.graph:
            raise ValueError(f"Destination intersection '{destination}' not found in network.")

        if not nx.has_path(self.graph, origin, destination):
            return {
                "status": "NO_PATH_EXISTS",
                "origin": origin,
                "destination": destination,
                "path_nodes": [],
                "path_edges": [],
                "total_cost": float("inf"),
                "total_distance_km": 0.0,
                "total_time_min": 0.0
            }

        # Dijkstra algorithm
        path_nodes = nx.dijkstra_path(self.graph, origin, destination, weight=weight_metric)
        total_cost = nx.dijkstra_path_length(self.graph, origin, destination, weight=weight_metric)

        # Assemble turn-by-turn route breakdown
        path_edges = []
        tot_dist_m = 0.0
        tot_free_time = 0.0
        tot_signal_delay = 0.0

        for i in range(len(path_nodes) - 1):
            u = path_nodes[i]
            v = path_nodes[i + 1]
            e_data = self.graph[u][v]

            dist = e_data.get("length_m", 500.0)
            free_t = e_data.get("free_flow_time_min", (dist / 1000.0) / 40.0 * 60.0)
            delay = e_data.get("signal_delay_min", 0.5)

            tot_dist_m += dist
            tot_free_time += free_t
            tot_signal_delay += delay

            path_edges.append({
                "step": i + 1,
                "from_id": u,
                "to_id": v,
                "from_name": self.graph.nodes[u].get("name", u),
                "to_name": self.graph.nodes[v].get("name", v),
                "road_name": e_data.get("road_name", "Arterial Link"),
                "length_m": round(dist, 1),
                "speed_kmh": e_data.get("free_flow_speed_kmh", 40.0),
                "travel_time_min": round(free_t, 2),
                "signal_delay_min": round(delay, 2),
                "segment_cost_min": round(e_data.get("cost", free_t + delay), 2)
            })

        return {
            "status": "OPTIMAL",
            "origin": origin,
            "origin_name": self.graph.nodes[origin].get("name", origin),
            "destination": destination,
            "destination_name": self.graph.nodes[destination].get("name", destination),
            "path_nodes": path_nodes,
            "path_edges": path_edges,
            "num_hops": len(path_nodes) - 1,
            "total_distance_km": round(tot_dist_m / 1000.0, 2),
            "total_free_flow_time_min": round(tot_free_time, 2),
            "total_signal_delay_min": round(tot_signal_delay, 2),
            "total_travel_time_min": round(tot_free_time + tot_signal_delay, 2),
            "total_path_cost": round(total_cost, 2)
        }

    def compare_routes(
        self,
        origin: str,
        destination: str,
        baseline_graph: nx.DiGraph,
        optimized_graph: nx.DiGraph
    ) -> Dict[str, Any]:
        """
        Compares route traversal times and intersection delay between baseline PDF timings
        and optimized signal timings.
        """
        opt_base = ShortestPathOptimizer(baseline_graph)
        opt_tuned = ShortestPathOptimizer(optimized_graph)

        res_base = opt_base.find_shortest_path(origin, destination, weight_metric="cost")
        res_opt = opt_tuned.find_shortest_path(origin, destination, weight_metric="cost")

        if res_base["status"] != "OPTIMAL" or res_opt["status"] != "OPTIMAL":
            return {
                "status": "COMPARISON_FAILED",
                "baseline": res_base,
                "optimized": res_opt
            }

        t_base = res_base["total_travel_time_min"]
        t_opt = res_opt["total_travel_time_min"]
        time_savings_min = round(t_base - t_opt, 2)
        pct_savings = round((time_savings_min / t_base * 100.0) if t_base > 0 else 0.0, 1)

        d_base = res_base["total_signal_delay_min"]
        d_opt = res_opt["total_signal_delay_min"]
        delay_reduction_min = round(d_base - d_opt, 2)

        return {
            "status": "SUCCESS",
            "origin": origin,
            "destination": destination,
            "baseline_route": res_base,
            "optimized_route": res_opt,
            "baseline_travel_time_min": t_base,
            "optimized_travel_time_min": t_opt,
            "time_savings_min": time_savings_min,
            "percentage_time_savings": pct_savings,
            "baseline_delay_min": d_base,
            "optimized_delay_min": d_opt,
            "delay_reduction_min": delay_reduction_min
        }
