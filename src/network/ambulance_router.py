"""
Core Dijkstra Ambulance Routing & Alternative Path Optimization Engine.
Ambulance Route Optimization — Bengaluru.

Implements:
1. Minimum estimated travel-time Dijkstra shortest path optimization.
2. Shortest-distance benchmark comparison.
3. Yen's K-shortest loopless paths algorithm for alternative route generation.
4. Separate routing cost profiles (Distance, Time, Signal Delay interface).
5. Seamless origin and Phase 1 hospital integration with driveway access delay modeling.
"""

import os
import copy
import heapq
import math
from typing import Dict, List, Any, Tuple, Optional, Set
import pandas as pd
import networkx as nx

from src.network.ambulance_graph import (
    get_ambulance_road_graphs,
    haversine_distance_m,
    calculate_polyline_distance_m
)

# Routing Cost Profile Identifiers
PROFILE_MINIMUM_TIME = "MINIMUM_ESTIMATED_TIME"
PROFILE_SHORTEST_DISTANCE = "SHORTEST_DISTANCE"
PROFILE_TIME_PLUS_SIGNAL = "TIME_PLUS_SIGNAL_DELAY"
PROFILE_MODERATE_CONGESTION = "MODERATE_CONGESTION"
PROFILE_HEAVY_CONGESTION = "HEAVY_CONGESTION"
PROFILE_COMBINED_TRAFFIC_SIGNAL = "COMBINED_TRAFFIC_SIGNAL"

SUPPORTED_PROFILES = [
    PROFILE_MINIMUM_TIME,
    PROFILE_SHORTEST_DISTANCE,
    PROFILE_TIME_PLUS_SIGNAL,
    PROFILE_MODERATE_CONGESTION,
    PROFILE_HEAVY_CONGESTION,
    PROFILE_COMBINED_TRAFFIC_SIGNAL
]

class UnreachableDestinationError(Exception):
    """Raised when no feasible directed path exists between origin and destination."""
    pass

class HospitalNotFoundError(Exception):
    """Raised when the requested hospital ID or name cannot be found in the dataset."""
    pass

class AmbulanceRouter:
    """
    Core Operations Research router for emergency ambulance dispatch.
    Implements Tasks 4, 5, 6, 7, and 8 of Phase 2.
    """

    def __init__(
        self,
        graph_multi: Optional[nx.MultiDiGraph] = None,
        graph_di: Optional[nx.DiGraph] = None,
        hospitals_csv_path: str = "data/processed/bengaluru_hospitals.csv",
        connections_csv_path: str = "data/processed/hospital_road_connections.csv"
    ):
        if graph_multi is None and graph_di is None:
            self.graph_multi, self.graph_di = get_ambulance_road_graphs()
        elif graph_multi is None:
            self.graph_multi = nx.MultiDiGraph(graph_di)
            self.graph_di = graph_di
        elif graph_di is None:
            self.graph_multi = graph_multi
            self.graph_di = nx.DiGraph(graph_multi)
        else:
            self.graph_multi = graph_multi
            self.graph_di = graph_di

        self.hospitals_csv_path = hospitals_csv_path
        self.connections_csv_path = connections_csv_path
        
        self.df_hospitals: Optional[pd.DataFrame] = None
        self.df_connections: Optional[pd.DataFrame] = None
        self._load_hospital_catalogs()

    def _load_hospital_catalogs(self):
        """Loads hospital and snapping catalogs from Phase 1 outputs."""
        if os.path.exists(self.hospitals_csv_path):
            self.df_hospitals = pd.read_csv(self.hospitals_csv_path)
        else:
            self.df_hospitals = pd.DataFrame()

        if os.path.exists(self.connections_csv_path):
            self.df_connections = pd.read_csv(self.connections_csv_path)
        else:
            self.df_connections = pd.DataFrame()

    def get_weight_metric_for_profile(self, profile: str) -> str:
        """Maps routing cost profile to corresponding edge weight attribute."""
        if profile == PROFILE_MINIMUM_TIME:
            return "travel_time_sec"
        elif profile == PROFILE_SHORTEST_DISTANCE:
            return "length_m"
        elif profile == PROFILE_TIME_PLUS_SIGNAL:
            return "total_signal_aware_time_sec"
        elif profile == PROFILE_MODERATE_CONGESTION:
            return "time_moderate_sec"
        elif profile == PROFILE_HEAVY_CONGESTION:
            return "time_heavy_sec"
        elif profile == PROFILE_COMBINED_TRAFFIC_SIGNAL:
            return "time_combined_sec"
        else:
            raise ValueError(f"Unknown routing profile '{profile}'. Choose from {SUPPORTED_PROFILES}")

    def find_shortest_path(
        self,
        origin: str,
        destination: str,
        profile: str = PROFILE_MINIMUM_TIME
    ) -> Dict[str, Any]:
        """
        Solves Dijkstra's algorithm for minimum-cost path from origin to destination.
        Implements Task 4.
        """
        if origin not in self.graph_di:
            raise ValueError(f"Origin node '{origin}' not found in road network graph.")
        if destination not in self.graph_di:
            raise ValueError(f"Destination node '{destination}' not found in road network graph.")

        weight_metric = self.get_weight_metric_for_profile(profile)

        # 1. Path feasibility check
        if not nx.has_path(self.graph_di, origin, destination):
            return {
                "status": "NO_PATH_EXISTS",
                "origin": origin,
                "origin_name": self.graph_di.nodes[origin].get("name", origin),
                "destination": destination,
                "destination_name": self.graph_di.nodes[destination].get("name", destination),
                "profile": profile,
                "path_nodes": [],
                "path_edges": [],
                "total_time_sec": float("inf"),
                "total_time_min": float("inf"),
                "free_flow_time_sec": float("inf"),
                "free_flow_time_min": float("inf"),
                "total_traffic_delay_sec": 0.0,
                "total_traffic_delay_min": 0.0,
                "total_signal_delay_sec": 0.0,
                "total_signal_delay_min": 0.0,
                "total_combined_time_sec": float("inf"),
                "total_combined_time_min": float("inf"),
                "total_distance_m": 0.0,
                "total_distance_km": 0.0,
                "num_segments": 0,
                "average_speed_kmh": 0.0,
                "route_geometry": []
            }

        # 2. Dijkstra Execution
        path_nodes = nx.dijkstra_path(self.graph_di, origin, destination, weight=weight_metric)
        total_weight = nx.dijkstra_path_length(self.graph_di, origin, destination, weight=weight_metric)

        # 3. Path reconstruction & edge aggregation
        path_edges = []
        tot_dist_m = 0.0
        tot_time_sec = 0.0
        tot_signal_sec = 0.0
        tot_traffic_sec = 0.0
        route_coords = []

        for i in range(len(path_nodes) - 1):
            u = path_nodes[i]
            v = path_nodes[i + 1]
            e_data = self.graph_di[u][v]

            dist_m = float(e_data.get("length_m", 500.0))
            time_sec = float(e_data.get("travel_time_sec", 60.0))
            base_speed_kmh = float(e_data.get("speed_kmh", 30.0))
            sig_delay_sec = float(e_data.get("signal_delay_sec", 0.0))
            geom = e_data.get("geometry", [])

            # Congestion delays
            if profile == PROFILE_MODERATE_CONGESTION:
                traff_delay_sec = float(e_data.get("traffic_delay_moderate_sec", 0.0))
                eff_speed_kmh = float(e_data.get("effective_speed_moderate_kmh", base_speed_kmh))
            elif profile in (PROFILE_HEAVY_CONGESTION, PROFILE_COMBINED_TRAFFIC_SIGNAL):
                traff_delay_sec = float(e_data.get("traffic_delay_heavy_sec", 0.0))
                eff_speed_kmh = float(e_data.get("effective_speed_heavy_kmh", base_speed_kmh))
            else:
                traff_delay_sec = 0.0
                eff_speed_kmh = base_speed_kmh

            tot_dist_m += dist_m
            tot_time_sec += time_sec
            tot_signal_sec += sig_delay_sec
            tot_traffic_sec += traff_delay_sec

            if geom:
                if not route_coords:
                    route_coords.extend(geom)
                else:
                    route_coords.extend(geom[1:])

            edge_total_sec = time_sec + traff_delay_sec
            if profile in (PROFILE_TIME_PLUS_SIGNAL, PROFILE_COMBINED_TRAFFIC_SIGNAL):
                edge_total_sec += sig_delay_sec

            path_edges.append({
                "step": i + 1,
                "from_node": u,
                "to_node": v,
                "from_name": self.graph_di.nodes[u].get("name", u),
                "to_name": self.graph_di.nodes[v].get("name", v),
                "edge_id": e_data.get("edge_id", f"EDGE_{u}_{v}"),
                "road_name": e_data.get("road_name", "Arterial Link"),
                "length_m": round(dist_m, 1),
                "length_km": round(dist_m / 1000.0, 3),
                "speed_kmh": base_speed_kmh,
                "effective_speed_kmh": round(eff_speed_kmh, 1),
                "travel_time_sec": round(time_sec, 1),
                "travel_time_min": round(time_sec / 60.0, 2),
                "traffic_delay_sec": round(traff_delay_sec, 1),
                "traffic_delay_min": round(traff_delay_sec / 60.0, 2),
                "signal_delay_sec": round(sig_delay_sec, 1),
                "signal_delay_min": round(sig_delay_sec / 60.0, 2),
                "edge_total_time_sec": round(edge_total_sec, 1),
                "edge_total_time_min": round(edge_total_sec / 60.0, 2),
                "signal_available": e_data.get("signal_available", False),
                "signal_verification_status": e_data.get("signal_verification_status", "UNAVAILABLE"),
                "signal_reason": e_data.get("signal_reason", ""),
                "geometry": geom
            })

        tot_dist_km = round(tot_dist_m / 1000.0, 3)
        free_flow_min = round(tot_time_sec / 60.0, 2)
        tot_traff_min = round(tot_traffic_sec / 60.0, 2)
        tot_sig_min = round(tot_signal_sec / 60.0, 2)

        # Profile-specific total journey time
        if profile in (PROFILE_MINIMUM_TIME, PROFILE_SHORTEST_DISTANCE):
            journey_time_sec = tot_time_sec
        elif profile == PROFILE_TIME_PLUS_SIGNAL:
            journey_time_sec = tot_time_sec + tot_signal_sec
        elif profile == PROFILE_MODERATE_CONGESTION:
            journey_time_sec = tot_time_sec + tot_traffic_sec
        elif profile == PROFILE_HEAVY_CONGESTION:
            journey_time_sec = tot_time_sec + tot_traffic_sec
        elif profile == PROFILE_COMBINED_TRAFFIC_SIGNAL:
            journey_time_sec = tot_time_sec + tot_traffic_sec + tot_signal_sec
        else:
            journey_time_sec = tot_time_sec

        journey_time_min = round(journey_time_sec / 60.0, 2)
        tot_sig_aware_sec = round(tot_time_sec + tot_signal_sec, 1)
        tot_sig_aware_min = round(tot_sig_aware_sec / 60.0, 2)
        avg_speed_kmh = round((tot_dist_km / (journey_time_sec / 3600.0)), 1) if journey_time_sec > 0 else 0.0

        num_signals = sum(
            1 for pe in path_edges if pe.get("signal_available", False) and pe.get("signal_delay_sec", 0) > 0
        )

        return {
            "status": "OPTIMAL",
            "origin": origin,
            "origin_name": self.graph_di.nodes[origin].get("name", origin),
            "destination": destination,
            "destination_name": self.graph_di.nodes[destination].get("name", destination),
            "profile": profile,
            "path_nodes": path_nodes,
            "path_edges": path_edges,
            "num_segments": len(path_edges),
            "total_distance_m": round(tot_dist_m, 1),
            "total_distance_km": tot_dist_km,
            "free_flow_time_sec": round(tot_time_sec, 1),
            "free_flow_time_min": free_flow_min,
            "total_time_sec": round(journey_time_sec, 1),
            "total_time_min": journey_time_min,
            "total_traffic_delay_sec": round(tot_traffic_sec, 1),
            "total_traffic_delay_min": tot_traff_min,
            "total_signal_delay_sec": round(tot_signal_sec, 1),
            "total_signal_delay_min": tot_sig_min,
            "total_combined_time_sec": round(tot_time_sec + tot_traffic_sec + tot_signal_sec, 1),
            "total_combined_time_min": round((tot_time_sec + tot_traffic_sec + tot_signal_sec) / 60.0, 2),
            "total_signal_aware_time_sec": tot_sig_aware_sec,
            "total_signal_aware_time_min": tot_sig_aware_min,
            "num_signals_encountered": num_signals,
            "total_weight": round(total_weight, 2),
            "average_speed_kmh": avg_speed_kmh,
            "route_geometry": route_coords
        }

    def compare_distance_vs_time_routes(
        self,
        origin: str,
        destination: str
    ) -> Dict[str, Any]:
        """
        Compares the Minimum Travel Time route against the Shortest Distance route.
        Implements Task 5.
        """
        res_time = self.find_shortest_path(origin, destination, profile=PROFILE_MINIMUM_TIME)
        res_dist = self.find_shortest_path(origin, destination, profile=PROFILE_SHORTEST_DISTANCE)

        if res_time["status"] != "OPTIMAL" or res_dist["status"] != "OPTIMAL":
            return {
                "status": "COMPARISON_FAILED",
                "message": "One or both routing queries failed.",
                "time_route": res_time,
                "distance_route": res_dist
            }

        d_time = res_time["total_distance_km"]
        d_dist = res_dist["total_distance_km"]
        t_time = res_time["total_time_min"]
        t_dist = res_dist["total_time_min"]

        delta_dist_km = round(d_time - d_dist, 3)
        delta_time_min = round(t_dist - t_time, 2)
        time_saved_pct = round((delta_time_min / t_dist * 100.0) if t_dist > 0 else 0.0, 1)

        is_identical = (res_time["path_nodes"] == res_dist["path_nodes"])

        if is_identical:
            explanation = "Both criteria yield the identical route trajectory across the network."
        elif delta_time_min > 0:
            explanation = (
                f"The Minimum Time route saves {delta_time_min} min ({time_saved_pct}%) "
                f"by routing via higher-speed arterials, adding {delta_dist_km} km over the shortest distance path."
            )
        else:
            explanation = "Shortest distance and fastest time are equivalent within rounding tolerance."

        return {
            "status": "SUCCESS",
            "origin": origin,
            "destination": destination,
            "is_identical_path": is_identical,
            "time_route": res_time,
            "distance_route": res_dist,
            "fastest_time_min": t_time,
            "fastest_distance_km": d_time,
            "shortest_distance_km": d_dist,
            "shortest_dist_time_min": t_dist,
            "delta_distance_km": delta_dist_km,
            "time_saved_min": delta_time_min,
            "time_saved_percentage": time_saved_pct,
            "tradeoff_explanation": explanation
        }

    def compare_baseline_vs_signal_aware(
        self,
        origin: str,
        destination: str
    ) -> Dict[str, Any]:
        """
        Compares Scenario A (Baseline road travel time) against
        Scenario B (Signal-aware travel time including Webster signal delay).
        Implements Phase 4 — Task 8.
        """
        route_baseline = self.find_shortest_path(origin, destination, profile=PROFILE_MINIMUM_TIME)
        route_signal = self.find_shortest_path(origin, destination, profile=PROFILE_TIME_PLUS_SIGNAL)

        if route_baseline["status"] != "OPTIMAL" or route_signal["status"] != "OPTIMAL":
            return {
                "status": "COMPARISON_FAILED",
                "message": "One or both routing queries failed.",
                "route_baseline": route_baseline,
                "route_signal_aware": route_signal
            }

        is_identical = (route_baseline["path_nodes"] == route_signal["path_nodes"])

        dist_base_km = route_baseline["total_distance_km"]
        dist_sig_km = route_signal["total_distance_km"]
        time_base_min = route_baseline["total_time_min"]
        time_sig_min = route_signal["total_signal_aware_time_min"]
        sig_delay_base_min = route_baseline["total_signal_delay_min"]
        sig_delay_sig_min = route_signal["total_signal_delay_min"]

        delta_dist_km = round(dist_sig_km - dist_base_km, 3)
        delta_time_min = round(time_sig_min - (time_base_min + sig_delay_base_min), 2)

        # Detect divergence node
        p_base = route_baseline["path_nodes"]
        p_sig = route_signal["path_nodes"]
        div_node = None
        if not is_identical:
            for di in range(min(len(p_base), len(p_sig))):
                if p_base[di] != p_sig[di]:
                    div_node = p_base[di - 1] if di > 0 else p_base[0]
                    break

        div_name = self.graph_di.nodes.get(div_node, {}).get("name", div_node) if div_node else "None"

        if is_identical:
            desc = (
                f"Trajectory is identical across both scenarios ({len(p_base)} junctions). "
                f"Incorporating verified signal timings adds {sig_delay_base_min} min of expected signal delay, "
                f"increasing estimated journey time from {time_base_min} min to {time_sig_min} min."
            )
        else:
            desc = (
                f"Signal-aware routing diverged at {div_name} to avoid high-delay signals, "
                f"resulting in a {delta_dist_km:+.3f} km change in distance and {delta_time_min:+.2f} min "
                f"net change in total signal-aware journey time."
            )

        return {
            "status": "SUCCESS",
            "origin": origin,
            "origin_name": route_baseline["origin_name"],
            "destination": destination,
            "destination_name": route_baseline["destination_name"],
            "is_identical_route": is_identical,
            "divergence_node": div_node,
            "divergence_node_name": div_name,
            "scenario_a_baseline": {
                "distance_km": dist_base_km,
                "road_travel_time_min": time_base_min,
                "signal_delay_min": sig_delay_base_min,
                "total_signal_aware_time_min": round(time_base_min + sig_delay_base_min, 2),
                "signals_encountered": route_baseline["num_signals_encountered"],
                "path_nodes": p_base,
                "route_geometry": route_baseline["route_geometry"]
            },
            "scenario_b_signal_aware": {
                "distance_km": dist_sig_km,
                "road_travel_time_min": route_signal["total_time_min"],
                "signal_delay_min": sig_delay_sig_min,
                "total_signal_aware_time_min": time_sig_min,
                "signals_encountered": route_signal["num_signals_encountered"],
                "path_nodes": p_sig,
                "route_geometry": route_signal["route_geometry"]
            },
            "delta_distance_km": delta_dist_km,
            "delta_total_time_min": delta_time_min,
            "route_changes_description": desc,
            "academic_disclaimer": (
                "Academic Research Model — Undersaturated Fixed-Time Webster Delay. "
                "Does not reflect real-time adaptive preemption or congested spillback queues. "
                "Field validation required prior to operational emergency dispatch."
            )
        }

    def compare_traffic_scenarios(
        self,
        origin: str,
        destination: str
    ) -> Dict[str, Any]:
        """
        Runs comprehensive multi-scenario traffic routing experiments for an OD pair.
        Evaluates 5 scenarios:
        1. BASELINE_FREE_FLOW (IRC:106 free-flow speed, no traffic, no signals)
        2. SHORTEST_DISTANCE (Geodesic / road-length minimization)
        3. MODERATE_CONGESTION (Calibrated BPR v/c ≈ 0.65 link slowdowns)
        4. HEAVY_CONGESTION (Peak hour TomTom benchmark v/c ≈ 1.05 slowdowns)
        5. COMBINED_TRAFFIC_SIGNAL (Heavy congestion + Webster signal red delays)
        
        Strictly prevents double-counting by isolating link travel time, mid-link
        traffic slowdown, and terminal signal delay.
        Implements Phase 5 — Task 7.
        """
        scenarios_config = [
            ("BASELINE_FREE_FLOW", "Baseline Free-Flow (Speed Limit)", PROFILE_MINIMUM_TIME, "#2563EB"),
            ("SHORTEST_DISTANCE", "Shortest Distance Benchmark", PROFILE_SHORTEST_DISTANCE, "#10B981"),
            ("MODERATE_CONGESTION", "Moderate Congestion (Off-Peak/Inter-Peak)", PROFILE_MODERATE_CONGESTION, "#F59E0B"),
            ("HEAVY_CONGESTION", "Heavy Congestion (Peak Rush-Hour)", PROFILE_HEAVY_CONGESTION, "#DC2626"),
            ("COMBINED_TRAFFIC_SIGNAL", "Combined Congestion + Signal Delays", PROFILE_COMBINED_TRAFFIC_SIGNAL, "#7C3AED")
        ]

        scenario_results = {}
        comparison_rows = []
        baseline_nodes = None

        for sc_key, sc_label, prof, color in scenarios_config:
            res = self.find_shortest_path(origin, destination, profile=prof)
            if res["status"] != "OPTIMAL":
                return {
                    "status": "COMPARISON_FAILED",
                    "message": f"Routing failed for scenario '{sc_key}'."
                }

            if sc_key == "BASELINE_FREE_FLOW":
                baseline_nodes = res["path_nodes"]

            is_diverged = (res["path_nodes"] != baseline_nodes) if baseline_nodes else False
            div_node = None
            div_node_name = "None"
            if is_diverged and baseline_nodes:
                for di in range(min(len(baseline_nodes), len(res["path_nodes"]))):
                    if baseline_nodes[di] != res["path_nodes"][di]:
                        div_node = baseline_nodes[di - 1] if di > 0 else baseline_nodes[0]
                        div_node_name = self.graph_di.nodes.get(div_node, {}).get("name", div_node)
                        break

            # Delay breakdown
            dist_km = res["total_distance_km"]
            ff_time_min = res["free_flow_time_min"]
            traff_del_min = res["total_traffic_delay_min"]
            sig_del_min = res["total_signal_delay_min"]
            tot_time_min = res["total_time_min"]
            avg_spd = res["average_speed_kmh"]

            scenario_entry = {
                "scenario_key": sc_key,
                "label": sc_label,
                "profile": prof,
                "color": color,
                "distance_km": dist_km,
                "free_flow_time_min": ff_time_min,
                "traffic_delay_min": traff_del_min,
                "signal_delay_min": sig_del_min,
                "total_time_min": tot_time_min,
                "average_speed_kmh": avg_spd,
                "num_segments": res["num_segments"],
                "path_nodes": res["path_nodes"],
                "is_diverged_from_baseline": is_diverged,
                "divergence_node": div_node,
                "divergence_node_name": div_node_name,
                "route_geometry": res["route_geometry"],
                "raw_result": res
            }
            scenario_results[sc_key] = scenario_entry

            comparison_rows.append({
                "Scenario": sc_label,
                "Distance (km)": dist_km,
                "Free-Flow Time (min)": ff_time_min,
                "Traffic Delay (min)": traff_del_min,
                "Signal Delay (min)": sig_del_min,
                "Total Journey Time (min)": tot_time_min,
                "Avg Speed (km/h)": avg_spd,
                "Diverged Route?": "Yes" if is_diverged else "No",
                "Divergence Junction": div_node_name if is_diverged else "Identical"
            })

        df_comparison = pd.DataFrame(comparison_rows)

        base_res = scenario_results["BASELINE_FREE_FLOW"]
        hvy_res = scenario_results["HEAVY_CONGESTION"]
        comb_res = scenario_results["COMBINED_TRAFFIC_SIGNAL"]

        congestion_impact_pct = round(((hvy_res["total_time_min"] - base_res["total_time_min"]) / base_res["total_time_min"] * 100.0) if base_res["total_time_min"] > 0 else 0.0, 1)
        signal_contribution_pct = round((comb_res["signal_delay_min"] / comb_res["total_time_min"] * 100.0) if comb_res["total_time_min"] > 0 else 0.0, 1)

        summary_narrative = (
            f"Under baseline free-flow conditions, the corridor requires {base_res['total_time_min']:.2f} min ({base_res['distance_km']:.2f} km). "
            f"During heavy peak-hour congestion, travel time expands by +{congestion_impact_pct}% to {hvy_res['total_time_min']:.2f} min. "
            f"When combining peak traffic link slowdowns with verified traffic signal wait times, total emergency travel time reaches {comb_res['total_time_min']:.2f} min, "
            f"with traffic signals accounting for {signal_contribution_pct}% ({comb_res['signal_delay_min']:.2f} min) of the total transit delay."
        )

        return {
            "status": "SUCCESS",
            "origin": origin,
            "origin_name": self.graph_di.nodes.get(origin, {}).get("name", origin),
            "destination": destination,
            "destination_name": self.graph_di.nodes.get(destination, {}).get("name", destination),
            "scenarios": scenario_results,
            "comparison_table": df_comparison,
            "congestion_impact_pct": congestion_impact_pct,
            "signal_contribution_pct": signal_contribution_pct,
            "summary_narrative": summary_narrative,
            "academic_disclaimer": (
                "Academic Research Model — Traffic delay estimated using BPR link formulation calibrated to TomTom Traffic Index benchmarks. "
                "Signal delays calculated via Webster uniform delay from verified traffic signal timing PDFs. "
                "Strict non-double-counting policy: link travel time, mid-link traffic delay, and terminal junction delay are mutually decoupled."
            )
        }

    def compare_hospital_scenarios(
        self,
        origin: str,
        hospital_id_or_name: str
    ) -> Dict[str, Any]:
        """
        Runs multi-scenario traffic routing experiments towards a destination hospital facility.
        Incorporates Phase 1 hospital snapping and campus driveway access penalty.
        """
        # Resolve hospital first
        h_rec = None
        c_rec = None
        if self.df_hospitals is not None and not self.df_hospitals.empty:
            m1 = self.df_hospitals[self.df_hospitals["hospital_id"] == hospital_id_or_name]
            if not m1.empty:
                h_rec = m1.iloc[0].to_dict()
            else:
                m2 = self.df_hospitals[self.df_hospitals["hospital_name"].str.contains(hospital_id_or_name, case=False, na=False)]
                if not m2.empty:
                    h_rec = m2.iloc[0].to_dict()

        if h_rec is None:
            raise HospitalNotFoundError(f"Hospital '{hospital_id_or_name}' not found in catalog.")

        hid = h_rec["hospital_id"]
        hname = h_rec["hospital_name"]

        if self.df_connections is not None and not self.df_connections.empty:
            m_c = self.df_connections[self.df_connections["hospital_id"] == hid]
            if not m_c.empty:
                c_rec = m_c.iloc[0].to_dict()

        if c_rec is None or pd.isna(c_rec.get("nearest_intersection_id")):
            return {
                "status": "UNCONNECTED_HOSPITAL",
                "message": f"Hospital '{hname}' ({hid}) is not snapped to a network node."
            }

        target_node = c_rec["nearest_intersection_id"]
        driveway_dist_m = float(c_rec.get("snapping_distance_m", 300.0))
        driveway_time_min = float(c_rec.get("estimated_access_time_min", 2.0))

        # Run OD scenario comparison to entrance node
        od_comp = self.compare_traffic_scenarios(origin, target_node)
        if od_comp["status"] != "SUCCESS":
            return od_comp

        # Enrich each scenario with hospital campus driveway segment
        hosp_scenarios = {}
        hosp_rows = []
        for sc_key, sc_data in od_comp["scenarios"].items():
            tot_hosp_dist_km = round(sc_data["distance_km"] + (driveway_dist_m / 1000.0), 3)
            tot_hosp_time_min = round(sc_data["total_time_min"] + driveway_time_min, 2)
            h_geom = sc_data["route_geometry"] + [[h_rec["latitude"], h_rec["longitude"]]]

            hosp_entry = dict(sc_data)
            hosp_entry["hospital_id"] = hid
            hosp_entry["hospital_name"] = hname
            hosp_entry["driveway_access_distance_m"] = driveway_dist_m
            hosp_entry["driveway_access_time_min"] = driveway_time_min
            hosp_entry["total_hospital_distance_km"] = tot_hosp_dist_km
            hosp_entry["total_hospital_time_min"] = tot_hosp_time_min
            hosp_entry["route_geometry"] = h_geom
            hosp_scenarios[sc_key] = hosp_entry

            hosp_rows.append({
                "Scenario": sc_data["label"],
                "Road Dist (km)": sc_data["distance_km"],
                "Driveway (m)": driveway_dist_m,
                "Total Dist (km)": tot_hosp_dist_km,
                "Road Time (min)": sc_data["total_time_min"],
                "Driveway Delay (min)": driveway_time_min,
                "Total Emergency Time (min)": tot_hosp_time_min,
                "Traffic Delay (min)": sc_data["traffic_delay_min"],
                "Signal Delay (min)": sc_data["signal_delay_min"],
                "Diverged?": "Yes" if sc_data["is_diverged_from_baseline"] else "No"
            })

        return {
            "status": "SUCCESS",
            "origin": origin,
            "origin_name": od_comp["origin_name"],
            "hospital_id": hid,
            "hospital_name": hname,
            "verification_status": h_rec.get("verification_status", "VERIFIED"),
            "emergency_service_type": h_rec.get("emergency_service_type", "Tertiary Emergency Care"),
            "entrance_intersection_id": target_node,
            "entrance_intersection_name": od_comp["destination_name"],
            "driveway_access_distance_m": driveway_dist_m,
            "driveway_access_time_min": driveway_time_min,
            "scenarios": hosp_scenarios,
            "comparison_table": pd.DataFrame(hosp_rows),
            "summary_narrative": od_comp["summary_narrative"],
            "academic_disclaimer": od_comp["academic_disclaimer"]
        }

    def find_k_alternative_routes(
        self,
        origin: str,
        destination: str,
        K: int = 3,
        profile: str = PROFILE_MINIMUM_TIME
    ) -> List[Dict[str, Any]]:
        """
        Computes the K-shortest loopless paths using Yen's algorithm.
        Implements Task 6.
        """
        if origin not in self.graph_di or destination not in self.graph_di:
            raise ValueError(f"Origin '{origin}' or destination '{destination}' not in graph.")
        if K < 1:
            raise ValueError("K must be an integer >= 1.")

        weight_metric = self.get_weight_metric_for_profile(profile)

        # Container for K shortest paths
        A: List[List[str]] = []
        A_costs: List[float] = []

        # Find 1st shortest path using standard Dijkstra
        try:
            p0 = nx.dijkstra_path(self.graph_di, origin, destination, weight=weight_metric)
            c0 = nx.dijkstra_path_length(self.graph_di, origin, destination, weight=weight_metric)
            A.append(p0)
            A_costs.append(c0)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

        # Candidate heap B containing tuples: (cost, tiebreaker, path)
        B: List[Tuple[float, int, List[str]]] = []
        B_paths_set: Set[Tuple[str, ...]] = set()
        tie_breaker = 0

        # Yen's Algorithm main iteration
        for k in range(1, K):
            prev_path = A[k - 1]

            # The spur node ranges from the first node up to the second-to-last node of the previous path
            for i in range(len(prev_path) - 1):
                spur_node = prev_path[i]
                root_path = prev_path[:i + 1]

                # Create a temporary working copy of graph
                G_temp = self.graph_di.copy()

                # Remove edges that are part of previous paths that have the same root path
                for p in A:
                    if len(p) > i and p[:i + 1] == root_path:
                        u_rem, v_rem = p[i], p[i + 1]
                        if G_temp.has_edge(u_rem, v_rem):
                            G_temp.remove_edge(u_rem, v_rem)

                # Remove all nodes in root_path except spur_node to prevent loops
                for node in root_path[:-1]:
                    if G_temp.has_node(node):
                        G_temp.remove_node(node)

                # Calculate spur path from spur_node to destination
                try:
                    if nx.has_path(G_temp, spur_node, destination):
                        spur_path = nx.dijkstra_path(G_temp, spur_node, destination, weight=weight_metric)
                        total_candidate_path = root_path[:-1] + spur_path
                        
                        cand_tuple = tuple(total_candidate_path)
                        if cand_tuple not in B_paths_set and cand_tuple not in [tuple(p) for p in A]:
                            # Calculate true path cost on original graph
                            cand_cost = 0.0
                            for ci in range(len(total_candidate_path) - 1):
                                cu, cv = total_candidate_path[ci], total_candidate_path[ci + 1]
                                cand_cost += self.graph_di[cu][cv][weight_metric]

                            tie_breaker += 1
                            heapq.heappush(B, (cand_cost, tie_breaker, total_candidate_path))
                            B_paths_set.add(cand_tuple)
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    pass

            if not B:
                # No more feasible loopless alternative paths exist
                break

            cost_k, _, path_k = heapq.heappop(B)
            A.append(path_k)
            A_costs.append(cost_k)

        # Assemble rich structured route records for each of the K paths
        results = []
        base_time = None

        for rank_idx, path_nodes in enumerate(A):
            # Reconstruct edge details from graph_di
            path_edges = []
            tot_dist_m = 0.0
            tot_time_sec = 0.0
            tot_signal_sec = 0.0
            route_coords = []

            for i in range(len(path_nodes) - 1):
                u = path_nodes[i]
                v = path_nodes[i + 1]
                e_data = self.graph_di[u][v]

                dist_m = float(e_data.get("length_m", 500.0))
                time_sec = float(e_data.get("travel_time_sec", 60.0))
                speed_kmh = float(e_data.get("speed_kmh", 30.0))
                sig_delay_sec = float(e_data.get("signal_delay_sec", 30.0))
                geom = e_data.get("geometry", [])

                tot_dist_m += dist_m
                tot_time_sec += time_sec
                tot_signal_sec += sig_delay_sec

                if geom:
                    if not route_coords:
                        route_coords.extend(geom)
                    else:
                        route_coords.extend(geom[1:])

                path_edges.append({
                    "step": i + 1,
                    "from_node": u,
                    "to_node": v,
                    "from_name": self.graph_di.nodes[u].get("name", u),
                    "to_name": self.graph_di.nodes[v].get("name", v),
                    "road_name": e_data.get("road_name", "Arterial Link"),
                    "length_m": round(dist_m, 1),
                    "length_km": round(dist_m / 1000.0, 3),
                    "speed_kmh": speed_kmh,
                    "travel_time_sec": round(time_sec, 1),
                    "travel_time_min": round(time_sec / 60.0, 2),
                    "signal_delay_sec": round(sig_delay_sec, 1),
                    "signal_delay_min": round(sig_delay_sec / 60.0, 2),
                    "signal_available": e_data.get("signal_available", False),
                    "signal_verification_status": e_data.get("signal_verification_status", "UNAVAILABLE"),
                    "signal_reason": e_data.get("signal_reason", "")
                })

            tot_dist_km = round(tot_dist_m / 1000.0, 3)
            tot_time_min = round(tot_time_sec / 60.0, 2)
            tot_sig_aware_sec = round(tot_time_sec + tot_signal_sec, 1)
            tot_sig_aware_min = round(tot_sig_aware_sec / 60.0, 2)
            avg_speed_kmh = round((tot_dist_km / (tot_time_sec / 3600.0)), 1) if tot_time_sec > 0 else 0.0

            num_signals = sum(
                1 for pe in path_edges if pe.get("signal_available", False) and pe.get("signal_delay_sec", 0) > 0
            )

            if rank_idx == 0:
                base_time = tot_sig_aware_min if profile == PROFILE_TIME_PLUS_SIGNAL else tot_time_min
                divergence_desc = "Optimal (Rank 1) primary route."
                detour_pct = 0.0
                detour_factor = 1.0
                time_delta = 0.0
                div_name = "Origin"
            else:
                curr_metric_time = tot_sig_aware_min if profile == PROFILE_TIME_PLUS_SIGNAL else tot_time_min
                time_delta = round(curr_metric_time - (base_time or curr_metric_time), 2)
                detour_pct = round(((curr_metric_time - (base_time or curr_metric_time)) / (base_time or 1.0) * 100.0), 1) if base_time and base_time > 0 else 0.0
                detour_factor = round(curr_metric_time / base_time, 2) if base_time and base_time > 0 else 1.0
                # Detect first divergent node
                p0 = A[0]
                div_node = None
                for di in range(min(len(p0), len(path_nodes))):
                    if p0[di] != path_nodes[di]:
                        div_node = p0[di - 1] if di > 0 else path_nodes[0]
                        break
                div_name = self.graph_di.nodes.get(div_node, {}).get("name", div_node) if div_node else "mid-route"
                divergence_desc = f"Diverges at {div_name} (+{time_delta} min slower than Rank 1)."

            results.append({
                "rank": rank_idx + 1,
                "label": f"Route Option {rank_idx + 1}",
                "path_nodes": path_nodes,
                "path_edges": path_edges,
                "num_segments": len(path_edges),
                "total_distance_m": round(tot_dist_m, 1),
                "total_distance_km": tot_dist_km,
                "total_time_sec": round(tot_time_sec, 1),
                "total_time_min": tot_time_min,
                "total_signal_delay_sec": round(tot_signal_sec, 1),
                "total_signal_delay_min": round(tot_signal_sec / 60.0, 2),
                "total_signal_aware_time_sec": tot_sig_aware_sec,
                "total_signal_aware_time_min": tot_sig_aware_min,
                "num_signals_encountered": num_signals,
                "average_speed_kmh": avg_speed_kmh,
                "time_delta_from_primary_min": time_delta,
                "delta_time_min": time_delta,
                "detour_factor_pct": detour_pct,
                "detour_factor": detour_factor,
                "time_penalty_pct": detour_pct,
                "divergence_node_name": div_name,
                "divergence_description": divergence_desc,
                "route_geometry": route_coords
            })

        return results

    def route_to_hospital(
        self,
        origin: str,
        hospital_id_or_name: str,
        profile: str = PROFILE_MINIMUM_TIME
    ) -> Dict[str, Any]:
        """
        Routes from any graph origin to a hospital facility from Phase 1.
        Appends the campus driveway access penalty and exposes facility verification status.
        Implements Task 8.
        """
        # 1. Resolve Hospital record
        h_rec = None
        c_rec = None

        if self.df_hospitals is not None and not self.df_hospitals.empty:
            # Check hospital_id match
            m1 = self.df_hospitals[self.df_hospitals["hospital_id"] == hospital_id_or_name]
            if not m1.empty:
                h_rec = m1.iloc[0].to_dict()
            else:
                # Check hospital_name match (case-insensitive substring)
                m2 = self.df_hospitals[self.df_hospitals["hospital_name"].str.contains(hospital_id_or_name, case=False, na=False)]
                if not m2.empty:
                    h_rec = m2.iloc[0].to_dict()

        if h_rec is None:
            raise HospitalNotFoundError(f"Hospital '{hospital_id_or_name}' not found in catalog.")

        hid = h_rec["hospital_id"]
        hname = h_rec["hospital_name"]
        verif_status = h_rec["verification_status"]
        em_type = h_rec["emergency_service_type"]

        # 2. Resolve Snapping Road Connection
        if self.df_connections is not None and not self.df_connections.empty:
            m_c = self.df_connections[self.df_connections["hospital_id"] == hid]
            if not m_c.empty:
                c_rec = m_c.iloc[0].to_dict()

        if c_rec is None or pd.isna(c_rec.get("nearest_intersection_id")):
            return {
                "status": "UNCONNECTED_HOSPITAL",
                "message": f"Hospital '{hname}' ({hid}) is not connected to a road network node.",
                "hospital_id": hid,
                "hospital_name": hname,
                "verification_status": verif_status
            }

        target_node = c_rec["nearest_intersection_id"]
        snap_dist_m = float(c_rec.get("snapping_distance_m", 300.0))
        access_time_min = float(c_rec.get("estimated_access_time_min", 2.0))
        access_time_sec = access_time_min * 60.0

        # 3. Solve network shortest path to entry node
        res_route = self.find_shortest_path(origin, target_node, profile=profile)

        if res_route["status"] != "OPTIMAL":
            return {
                "status": "UNREACHABLE_DESTINATION",
                "message": f"No feasible route exists from origin '{origin}' to hospital entry node '{target_node}'.",
                "origin": origin,
                "hospital_id": hid,
                "hospital_name": hname,
                "verification_status": verif_status,
                "target_intersection_id": target_node
            }

        # 4. Append campus driveway access segment
        access_step = {
            "step": len(res_route["path_edges"]) + 1,
            "from_node": target_node,
            "to_node": hid,
            "from_name": self.graph_di.nodes[target_node].get("name", target_node),
            "to_name": f"{hname} Emergency Bay",
            "edge_id": f"ACCESS_{hid}",
            "road_name": "Hospital Campus Driveway / Gate Access",
            "length_m": round(snap_dist_m, 1),
            "length_km": round(snap_dist_m / 1000.0, 3),
            "speed_kmh": 15.0,
            "travel_time_sec": round(access_time_sec, 1),
            "travel_time_min": round(access_time_min, 2),
            "geometry": [[self.graph_di.nodes[target_node]["lat"], self.graph_di.nodes[target_node]["lon"]],
                         [h_rec["latitude"], h_rec["longitude"]]]
        }

        combined_edges = res_route["path_edges"] + [access_step]
        tot_dist_m = res_route["total_distance_m"] + snap_dist_m
        tot_time_sec = res_route["total_time_sec"] + access_time_sec
        tot_dist_km = round(tot_dist_m / 1000.0, 3)
        tot_time_min = round(tot_time_sec / 60.0, 2)
        avg_speed = round(tot_dist_km / (tot_time_sec / 3600.0), 1) if tot_time_sec > 0 else 0.0

        # Append hospital point to route geometry
        combined_geometry = res_route["route_geometry"] + [[h_rec["latitude"], h_rec["longitude"]]]

        return {
            "status": "OPTIMAL",
            "origin": origin,
            "origin_name": self.graph_di.nodes[origin].get("name", origin),
            "destination_hospital_id": hid,
            "destination_hospital_name": hname,
            "verification_status": verif_status,
            "emergency_service_type": em_type,
            "hospital_address": h_rec.get("address"),
            "hospital_phone": h_rec.get("phone"),
            "target_intersection_id": target_node,
            "profile": profile,
            "path_nodes": res_route["path_nodes"] + [hid],
            "path_edges": combined_edges,
            "num_segments": len(combined_edges),
            "road_travel_time_min": res_route["total_time_min"],
            "driveway_access_time_min": round(access_time_min, 2),
            "total_time_min": tot_time_min,
            "total_time_sec": round(tot_time_sec, 1),
            "road_distance_km": res_route["total_distance_km"],
            "driveway_access_distance_m": round(snap_dist_m, 1),
            "total_distance_km": tot_dist_km,
            "total_distance_m": round(tot_dist_m, 1),
            "average_speed_kmh": avg_speed,
            "route_geometry": combined_geometry
        }

    def find_hospital_route(
        self,
        origin: str,
        hospital_id_or_name: str,
        profile: str = PROFILE_MINIMUM_TIME
    ) -> Dict[str, Any]:
        """
        Calculates optimal emergency route to a hospital facility.
        Alias for route_to_hospital.
        """
        return self.route_to_hospital(origin=origin, hospital_id_or_name=hospital_id_or_name, profile=profile)

# Class-level binding alias
AmbulanceRouter.find_hospital_route = AmbulanceRouter.route_to_hospital
