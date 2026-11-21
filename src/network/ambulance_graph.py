"""
Ambulance Directed Road Graph Module.
Ambulance Route Optimization — Bengaluru.

Constructs and manages the directed multi-graph representation of the Bengaluru
road network with IRC:106 speed calibrations, robust travel-time weights,
one-way restrictions, parallel edge preservation, and separate data provenance tracking.
"""

import os
import json
import math
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd
import networkx as nx

# Canonical Bengaluru Center coordinates
BENGALURU_LAT = 12.9716
BENGALURU_LON = 77.5946

# IRC:106-1990 Speed Classification Guidelines for Urban Roads (km/h)
IRC_SPEED_LIMITS = {
    "EXPRESSWAY": 50.0,
    "ARTERIAL": 40.0,
    "SUB_ARTERIAL": 35.0,
    "COLLECTOR": 30.0,
    "LOCAL_DRIVEWAY": 15.0,
    "DEFAULT_URBAN": 30.0
}

def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two lat/lon coordinates in meters."""
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def calculate_polyline_distance_m(coords: List[List[float]]) -> float:
    """Computes total polyline length along a sequence of [lat, lon] waypoints."""
    if not coords or len(coords) < 2:
        return 0.0
    tot = 0.0
    for i in range(len(coords) - 1):
        tot += haversine_distance_m(coords[i][0], coords[i][1], coords[i+1][0], coords[i+1][1])
    return tot

def infer_road_speed_kmh(road_name: str, lanes: int = 2) -> Tuple[float, str]:
    """
    Infers documented, realistic urban ambulance travel speed based on road classification
    and Indian Road Congress (IRC:106) guidelines.
    Returns: (speed_kmh, speed_provenance)
    """
    nm = str(road_name).upper() if road_name else ""
    
    if any(k in nm for k in ["EXPRESSWAY", "HIGHWAY", "NH44", "NH7", "FLYOVER", "BELLARY ROAD", "AIRPORT ROAD"]):
        return IRC_SPEED_LIMITS["EXPRESSWAY"], "ESTIMATED_IRC106_EXPRESSWAY"
    elif any(k in nm for k in ["RING ROAD", "OUTER RING", "ORR", "ARTERIAL", "DOUBLE ROAD", "100FT", "80FT", "MYSORE ROAD", "HOSUR ROAD"]):
        return IRC_SPEED_LIMITS["ARTERIAL"], "ESTIMATED_IRC106_ARTERIAL"
    elif any(k in nm for k in ["MAIN ROAD", "CHORD ROAD", "BANNERGHATTA", "CMH ROAD", "KORAMANGALA"]):
        return IRC_SPEED_LIMITS["SUB_ARTERIAL"], "ESTIMATED_IRC106_SUB_ARTERIAL"
    elif any(k in nm for k in ["LINK", "CONNECTOR", "CROSS", "STREET", "LAYOUT"]):
        return IRC_SPEED_LIMITS["COLLECTOR"], "ESTIMATED_IRC106_COLLECTOR"
    elif lanes >= 3:
        return IRC_SPEED_LIMITS["ARTERIAL"], "ESTIMATED_IRC106_BY_LANES"
    elif lanes == 2:
        return IRC_SPEED_LIMITS["SUB_ARTERIAL"], "ESTIMATED_IRC106_BY_LANES"
    else:
        return IRC_SPEED_LIMITS["DEFAULT_URBAN"], "FALLBACK_DEFAULT_URBAN"

class AmbulanceRoadGraphBuilder:
    """
    Constructs and validates the directed road graph (MultiDiGraph and DiGraph)
    for ambulance shortest-path routing.
    Implements Task 2 and Task 3 of Phase 2.
    """

    def __init__(
        self,
        intersections_path: str = "data/processed/intersections_gis.csv",
        roads_gis_path: str = "data/processed/roads_gis.json",
        edge_delays_path: str = "data/processed/edge_signal_delays.csv",
        congestion_path: str = "data/processed/network_congestion_scenarios.csv"
    ):
        self.intersections_path = intersections_path
        self.roads_gis_path = roads_gis_path
        self.edge_delays_path = edge_delays_path
        self.congestion_path = congestion_path
        
        self.df_intersections: Optional[pd.DataFrame] = None
        self.raw_roads: List[Dict[str, Any]] = []
        self.edge_delays_map: Dict[str, Dict[str, Any]] = {}
        self.congestion_map: Dict[Tuple[str, str], Dict[str, Any]] = {}
        
        self.graph_multi: Optional[nx.MultiDiGraph] = None
        self.graph_di: Optional[nx.DiGraph] = None
        self._load_source_data()

    def _load_source_data(self):
        """Loads and verifies source intersections, road catalog, signal delays, and congestion scenarios."""
        if not os.path.exists(self.intersections_path):
            raise FileNotFoundError(f"Missing intersections GIS file: {self.intersections_path}")
        self.df_intersections = pd.read_csv(self.intersections_path)

        if not os.path.exists(self.roads_gis_path):
            raise FileNotFoundError(f"Missing roads GIS file: {self.roads_gis_path}")
        with open(self.roads_gis_path, "r", encoding="utf-8") as f:
            self.raw_roads = json.load(f)

        if os.path.exists(self.edge_delays_path):
            df_d = pd.read_csv(self.edge_delays_path)
            for _, r in df_d.iterrows():
                self.edge_delays_map[str(r["edge_id"])] = r.to_dict()

        if os.path.exists(self.congestion_path):
            df_c = pd.read_csv(self.congestion_path)
            for _, r in df_c.iterrows():
                key = (str(r["edge_id"]), str(r["scenario"]))
                self.congestion_map[key] = r.to_dict()

    def calculate_edge_travel_time(
        self,
        length_m: float,
        speed_kmh: float
    ) -> Tuple[float, float]:
        """
        Calculates travel time in seconds and minutes.
        t_sec = (length_km / speed_kmh) * 3600.
        All weights are guaranteed to be finite, nonnegative, and non-zero.
        """
        valid_length_m = max(1.0, float(length_m)) if (length_m is not None and not math.isnan(length_m)) else 500.0
        valid_speed_kmh = max(5.0, min(120.0, float(speed_kmh))) if (speed_kmh is not None and not math.isnan(speed_kmh)) else 30.0
        
        length_km = valid_length_m / 1000.0
        time_sec = (length_km / valid_speed_kmh) * 3600.0
        time_min = time_sec / 60.0
        
        return round(time_sec, 2), round(time_min, 4)

    def build_directed_graphs(self) -> Tuple[nx.MultiDiGraph, nx.DiGraph]:
        """
        Builds both nx.MultiDiGraph (preserving parallel edges) and nx.DiGraph
        (canonical simplified representation), enriched with robust travel-time weights.
        """
        G_multi = nx.MultiDiGraph(name="Bengaluru Ambulance MultiDiGraph")
        G_di = nx.DiGraph(name="Bengaluru Ambulance DiGraph")

        # 1. Ingest Nodes
        for _, row in self.df_intersections.iterrows():
            nid = str(row["intersection_id"]).strip()
            name = str(row.get("name", row.get("intersection_name", nid))).strip()
            lat = float(row.get("latitude", BENGALURU_LAT))
            lon = float(row.get("longitude", BENGALURU_LON))
            ps = str(row.get("police_station", "Bengaluru Police"))
            ctrl = str(row.get("control_type", "Fixed Time"))
            cycle = float(row.get("cycle_time_sec", 120.0))
            verif = str(row.get("verification_status", "NEEDS_VERIFICATION"))

            node_attrs = {
                "node_id": nid,
                "name": name,
                "latitude": lat,
                "longitude": lon,
                "lat": lat,
                "lon": lon,
                "police_station": ps,
                "control_type": ctrl,
                "cycle_time_sec": cycle,
                "verification_status": verif,
                "node_type": "INTERSECTION"
            }
            G_multi.add_node(nid, **node_attrs)
            G_di.add_node(nid, **node_attrs)

        # 2. Ingest Directed Edges
        edge_key_counter: Dict[Tuple[str, str], int] = {}

        for r in self.raw_roads:
            u = str(r.get("from_node", "")).strip()
            v = str(r.get("to_node", "")).strip()

            if not u or not v:
                continue

            # Ensure endpoint nodes exist
            if u not in G_multi:
                G_multi.add_node(u, name=r.get("from_name", u), latitude=BENGALURU_LAT, longitude=BENGALURU_LON)
                G_di.add_node(u, name=r.get("from_name", u), latitude=BENGALURU_LAT, longitude=BENGALURU_LON)
            if v not in G_multi:
                G_multi.add_node(v, name=r.get("to_name", v), latitude=BENGALURU_LAT, longitude=BENGALURU_LON)
                G_di.add_node(v, name=r.get("to_name", v), latitude=BENGALURU_LAT, longitude=BENGALURU_LON)

            eid = r.get("edge_id", f"EDGE_{u}_{v}")
            rname = r.get("road_name", "Arterial Road Link")
            lanes = int(r.get("lanes", 2))
            geom = r.get("geometry", [])

            # Length validation
            raw_len = r.get("length_m")
            if raw_len is not None and not math.isnan(raw_len) and float(raw_len) > 0.0:
                length_m = float(raw_len)
            elif geom and len(geom) >= 2:
                length_m = calculate_polyline_distance_m(geom)
            else:
                u_lat, u_lon = G_multi.nodes[u]["latitude"], G_multi.nodes[u]["longitude"]
                v_lat, v_lon = G_multi.nodes[v]["latitude"], G_multi.nodes[v]["longitude"]
                length_m = haversine_distance_m(u_lat, u_lon, v_lat, v_lon)

            length_m = max(5.0, round(length_m, 1))
            length_km = round(length_m / 1000.0, 4)

            # Speed determination & validation
            raw_speed = r.get("speed_kmh", r.get("free_flow_speed_kmh"))
            if raw_speed is not None and not math.isnan(raw_speed) and float(raw_speed) > 0.0:
                speed_kmh = float(raw_speed)
                speed_prov = "CALIBRATED_IRC106"
            else:
                speed_kmh, speed_prov = infer_road_speed_kmh(rname, lanes)

            # Travel time calculation (strictly nonnegative)
            t_sec, t_min = self.calculate_edge_travel_time(length_m, speed_kmh)

            # Signal delay integration (Phase 4 Webster uniform delay model)
            delay_rec = self.edge_delays_map.get(eid)
            if delay_rec and str(delay_rec.get("is_signal_available", "")).upper() in ["TRUE", "1"]:
                sig_delay_sec = float(delay_rec.get("signal_delay_sec", 0.0))
                sig_delay_min = float(delay_rec.get("signal_delay_min", 0.0))
                sig_available = True
                sig_verif = str(delay_rec.get("verification_status", "VERIFIED"))
                sig_reason = str(delay_rec.get("reason", "Verified timing delay"))
            else:
                sig_delay_sec = 0.0
                sig_delay_min = 0.0
                sig_available = False
                sig_verif = "UNAVAILABLE"
                sig_reason = str(delay_rec.get("reason", "No verified signal delay available")) if delay_rec else "Edge not in signal catalog"

            total_sig_aware_sec = round(t_sec + sig_delay_sec, 2)
            total_sig_aware_min = round(t_min + sig_delay_min, 4)

            # Congestion scenario integration (Phase 5)
            c_mod = self.congestion_map.get((eid, "MODERATE_CONGESTION"), {})
            c_hvy = self.congestion_map.get((eid, "HEAVY_CONGESTION"), {})
            
            time_mod_sec = float(c_mod.get("total_time_sec", t_sec))
            time_hvy_sec = float(c_hvy.get("total_time_sec", t_sec))
            traffic_del_mod_sec = float(c_mod.get("traffic_delay_sec", 0.0))
            traffic_del_hvy_sec = float(c_hvy.get("traffic_delay_sec", 0.0))
            eff_spd_mod = float(c_mod.get("effective_speed_kmh", speed_kmh))
            eff_spd_hvy = float(c_hvy.get("effective_speed_kmh", speed_kmh))
            vc_mod = float(c_mod.get("vc_ratio", 0.65))
            vc_hvy = float(c_hvy.get("vc_ratio", 1.05))

            # Strictly non-double-counting combined time:
            # heavy congestion travel time + terminal junction signal delay
            time_combined_sec = round(time_hvy_sec + sig_delay_sec, 2)
            time_combined_min = round(time_combined_sec / 60.0, 4)

            edge_attrs = {
                "edge_id": eid,
                "from_node": u,
                "to_node": v,
                "from_name": G_multi.nodes[u].get("name", u),
                "to_name": G_multi.nodes[v].get("name", v),
                "road_name": rname,
                "direction": r.get("direction", "FORWARD"),
                "lanes": lanes,
                "length_m": length_m,
                "length_km": length_km,
                "speed_kmh": speed_kmh,
                "speed_provenance": speed_prov,
                "travel_time_sec": t_sec,
                "travel_time_min": t_min,
                "cost": t_min,  # Backward compatibility with existing modules
                "time_baseline_sec": t_sec,
                "time_baseline_min": t_min,
                "time_moderate_sec": time_mod_sec,
                "time_moderate_min": round(time_mod_sec / 60.0, 4),
                "time_heavy_sec": time_hvy_sec,
                "time_heavy_min": round(time_hvy_sec / 60.0, 4),
                "time_combined_sec": time_combined_sec,
                "time_combined_min": time_combined_min,
                "traffic_delay_moderate_sec": traffic_del_mod_sec,
                "traffic_delay_heavy_sec": traffic_del_hvy_sec,
                "effective_speed_moderate_kmh": eff_spd_mod,
                "effective_speed_heavy_kmh": eff_spd_hvy,
                "vc_ratio_moderate": vc_mod,
                "vc_ratio_heavy": vc_hvy,
                "signal_delay_min": sig_delay_min,
                "signal_delay_sec": sig_delay_sec,
                "total_signal_aware_time_sec": total_sig_aware_sec,
                "total_signal_aware_time_min": total_sig_aware_min,
                "signal_available": sig_available,
                "signal_verification_status": sig_verif,
                "signal_reason": sig_reason,
                "geometry": geom if geom else [[G_multi.nodes[u]["lat"], G_multi.nodes[u]["lon"]],
                                               [G_multi.nodes[v]["lat"], G_multi.nodes[v]["lon"]]],
                "geometry_source": r.get("geometry_source", "STRAIGHT_LINE_INTERPOLATION"),
                "verification_status": r.get("verification_status", "UNVERIFIED"),
                "data_provenance": r.get("data_provenance", "ESTIMATED")
            }

            # Add to MultiDiGraph preserving edge key
            curr_key = edge_key_counter.get((u, v), 0)
            edge_key_counter[(u, v)] = curr_key + 1
            G_multi.add_edge(u, v, key=curr_key, **edge_attrs)

            # Add to DiGraph (retaining the lower travel-time edge if parallel)
            if not G_di.has_edge(u, v) or G_di[u][v]["travel_time_sec"] > t_sec:
                G_di.add_edge(u, v, **edge_attrs)

        self.graph_multi = G_multi
        self.graph_di = G_di
        return G_multi, G_di

# Singleton cache to avoid rebuilding graph on repeated calls
_CACHED_BUILDER: Optional[AmbulanceRoadGraphBuilder] = None
_CACHED_GRAPHS: Optional[Tuple[nx.MultiDiGraph, nx.DiGraph]] = None

def get_ambulance_road_graphs(force_rebuild: bool = False) -> Tuple[nx.MultiDiGraph, nx.DiGraph]:
    """Retrieves cached MultiDiGraph and DiGraph instances."""
    global _CACHED_BUILDER, _CACHED_GRAPHS
    if _CACHED_GRAPHS is None or force_rebuild:
        _CACHED_BUILDER = AmbulanceRoadGraphBuilder()
        _CACHED_GRAPHS = _CACHED_BUILDER.build_directed_graphs()
    return _CACHED_GRAPHS
