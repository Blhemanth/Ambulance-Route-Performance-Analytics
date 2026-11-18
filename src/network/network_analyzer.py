"""
Network Analyzer Module for Bengaluru Road Network.
Calculates topological graph metrics, degree distributions, betweenness centrality,
strongly connected components, and network density to evaluate arterial critical hubs.
"""

import networkx as nx
import pandas as pd
from typing import Dict, List, Any

class NetworkAnalyzer:
    def __init__(self, graph: nx.DiGraph):
        self.graph = graph

    def compute_summary_metrics(self) -> Dict[str, Any]:
        """Calculates global structural metrics of the road network."""
        num_nodes = self.graph.number_of_nodes()
        num_edges = self.graph.number_of_edges()

        if num_nodes == 0:
            return {}

        density = nx.density(self.graph)
        num_scc = nx.number_strongly_connected_components(self.graph)
        num_wcc = nx.number_weakly_connected_components(self.graph)

        # Average degree
        in_degrees = dict(self.graph.in_degree())
        out_degrees = dict(self.graph.out_degree())
        avg_degree = sum(out_degrees.values()) / float(num_nodes)

        # Betweenness centrality (critical routing nodes)
        betweenness = nx.betweenness_centrality(self.graph, weight="cost")
        degree_centrality = nx.degree_centrality(self.graph)

        # Top 5 most critical hub intersections
        top_hubs = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:5]
        hub_records = []
        for nid, score in top_hubs:
            hub_records.append({
                "intersection_id": nid,
                "name": self.graph.nodes[nid].get("name", nid),
                "police_station": self.graph.nodes[nid].get("police_station", "BTP"),
                "betweenness_centrality": round(score, 4),
                "in_degree": in_degrees.get(nid, 0),
                "out_degree": out_degrees.get(nid, 0)
            })

        return {
            "total_nodes": num_nodes,
            "total_edges": num_edges,
            "graph_density": round(density, 4),
            "strongly_connected_components": num_scc,
            "weakly_connected_components": num_wcc,
            "average_degree": round(avg_degree, 2),
            "top_critical_hubs": hub_records
        }

    def compute_all_metrics(self) -> Dict[str, Any]:
        """Calculates extended topological metrics including clustering and density."""
        metrics = self.compute_summary_metrics()
        metrics["density"] = metrics.get("graph_density", 0.0)
        metrics["num_strongly_connected_components"] = metrics.get("strongly_connected_components", 1)
        metrics["num_weakly_connected_components"] = metrics.get("weakly_connected_components", 1)
        try:
            metrics["average_clustering"] = round(nx.average_clustering(self.graph.to_undirected()), 4)
        except Exception:
            metrics["average_clustering"] = 0.0
        return metrics
