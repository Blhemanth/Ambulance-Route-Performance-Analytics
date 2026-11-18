"""
Model 2: Minimum Cost Flow Optimization Module.
Formulates and solves the Minimum Cost Flow network optimization problem to determine
optimal vehicular traffic flow allocation that minimizes total system transportation cost
(travel time and generalized delay) under capacity bounds and mass balance constraints.
"""

import networkx as nx
from typing import Dict, List, Any, Tuple, Optional

class MinimumCostFlowOptimizer:
    def __init__(self, graph: nx.DiGraph):
        self.graph = graph

    def solve(
        self,
        supplies_and_demands: Dict[str, float],
        capacity_attribute: str = "effective_capacity",
        cost_attribute: str = "cost"
    ) -> Dict[str, Any]:
        """
        Solves Minimum Cost Flow on the network.
        supplies_and_demands: dict mapping node_id to net balance b_i:
          b_i > 0: Origin traffic supply (vehicles/hr)
          b_i < 0: Destination traffic demand (vehicles/hr)
          b_i = 0: Intermediate transshipment intersection
        Requires sum(b_i) == 0 for balanced network feasibility.
        """
        # 1. Validate Mass Balance Feasibility
        total_balance = sum(supplies_and_demands.values())
        if abs(total_balance) > 1e-3:
            raise ValueError(
                f"Supply-Demand Mass Balance Infeasible: Sum of b_i = {total_balance:.2f} != 0. "
                "Total origin traffic supply must equal total destination demand."
            )

        # 2. Build Working Graph with Demands, Capacities, and Integer-scaled Costs
        H = self.graph.copy()
        for n in H.nodes():
            b_val = supplies_and_demands.get(n, 0.0)
            # In NetworkX min_cost_flow, positive 'demand' means node needs flow (sink),
            # while negative 'demand' means node produces flow (source).
            # b_i in OR literature: positive is supply (source), negative is demand (sink).
            # Therefore: demand = -b_i
            H.nodes[n]["demand"] = int(round(-b_val))

        for u, v, d in H.edges(data=True):
            cap = d.get(capacity_attribute, d.get("physical_capacity", 2400))
            cost_val = d.get(cost_attribute, 1.0)
            H[u][v]["capacity"] = int(round(max(1.0, float(cap))))
            # Cost in NetworkX min_cost_flow should be non-negative integer (e.g. seconds or scaled minutes)
            H[u][v]["weight"] = int(round(max(0.1, float(cost_val)) * 100)) # Scaled by 100 for precision

        # 3. Solve Minimum Cost Flow via Network Simplex
        try:
            flow_cost_scaled, flow_dict = nx.network_simplex(H)
            total_cost_min = flow_cost_scaled / 100.0 # Rescale to travel minutes
        except nx.NetworkXUnfeasible as e:
            return {
                "status": "INFEASIBLE",
                "message": "Network capacities cannot satisfy the requested supply-demand matrix without congestion spillover.",
                "error_message": "Network capacities cannot satisfy the requested supply-demand matrix without congestion spillover.",
                "total_cost": 0.0,
                "total_system_cost_veh_min": 0.0,
                "flow_dict": {},
                "edge_flows": [],
                "flow_records": []
            }

        # 4. Analyze Road Utilization and Congested Segments
        edge_flows = []
        total_flow_volume = 0.0
        congested_edges = []

        for u, v, d in H.edges(data=True):
            flow = flow_dict.get(u, {}).get(v, 0)
            cap = d["capacity"]
            unit_cost = d["weight"] / 100.0
            utilization = (flow / cap) * 100.0 if cap > 0 else 0.0
            is_congested = (utilization >= 85.0)

            total_flow_volume += flow

            record = {
                "from_node": u,
                "to_node": v,
                "from_name": H.nodes[u].get("name", u),
                "to_name": H.nodes[v].get("name", v),
                "road_name": d.get("road_name", "Arterial Link"),
                "allocated_flow": flow,
                "flow_pcu_hr": flow,
                "capacity": cap,
                "capacity_pcu_hr": cap,
                "unit_cost_min": round(unit_cost, 2),
                "unit_cost": round(unit_cost, 2),
                "total_edge_cost_min": round(flow * unit_cost, 2),
                "total_link_cost": round(flow * unit_cost, 2),
                "utilization_pct": round(utilization, 1),
                "is_congested": is_congested
            }
            edge_flows.append(record)
            if is_congested:
                congested_edges.append(record)

        # Average travel cost per vehicle
        origin_total = sum(v for v in supplies_and_demands.values() if v > 0)
        avg_travel_time = (total_cost_min / origin_total) if origin_total > 0 else 0.0

        return {
            "status": "OPTIMAL",
            "total_system_cost_veh_min": round(total_cost_min, 1),
            "total_system_cost_veh_hours": round(total_cost_min / 60.0, 2),
            "average_travel_time_min": round(avg_travel_time, 2),
            "total_flow_volume": round(total_flow_volume, 1),
            "flow_dict": flow_dict,
            "edge_flows": edge_flows,
            "flow_records": edge_flows,
            "congested_edges": congested_edges,
            "congested_edge_count": len(congested_edges),
            "max_utilization_pct": max((e["utilization_pct"] for e in edge_flows), default=0.0)
        }
