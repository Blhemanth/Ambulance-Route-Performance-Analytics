"""
Graph Builder Module for Bengaluru Road Network.
Constructs Level 1 (Macro Intersection Graph) and Level 2 (Micro Movement Graph)
using NetworkX, calibrated with Indian Road Congress (IRC:106) capacity standards,
OpenStreetMap Bengaluru corridor geometry, and extracted BEL signal timing plans.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import math
import os
import pandas as pd
import networkx as nx
from typing import Dict, List, Any, Tuple, Optional

# Verified physical road connections between adjacent Bengaluru intersections
# Format: (intersection_slug_1, intersection_slug_2, road_name, lanes)
VERIFIED_CORRIDOR_CONNECTIONS = [
    # Corridor 1: South-Central Corridor (Adugodi - Koramangala - Wilson Garden - Dairy Circle)
    ("INT_003_ADUGODI_JUNCTION", "INT_004_AISHWARYA_JUNCTION_7THMN_", "7th Main Road / New Mico Rd", 2),
    ("INT_004_AISHWARYA_JUNCTION_7THMN_", "INT_047_JAIPURIA_JUNCTION_NEAR_CA", "Sony World - 8th Main Connector", 2),
    ("INT_003_ADUGODI_JUNCTION", "INT_031_DAIRY_CIRCLE_JUNCTION", "Hosur Laskar Road", 3),
    ("INT_003_ADUGODI_JUNCTION", "INT_016_BMTC_JUNCTION_K_H_ROAD", "K.H. Road / Hosur Rd", 3),
    ("INT_016_BMTC_JUNCTION_K_H_ROAD", "INT_017_K_H_JUNCTION", "K.H. Double Road", 3),
    ("INT_031_DAIRY_CIRCLE_JUNCTION", "INT_032_GURAPPANAPALYA_JUNCTION", "Bannerghatta Main Road", 3),
    ("INT_032_GURAPPANAPALYA_JUNCTION", "INT_013_HULIMAVU_JUNCTION", "Bannerghatta Expressway Section", 3),
    ("INT_014_SAGARAPPOLLO_JUNCTION", "INT_015_SWAGATMAIN_ROAD_JUNCTION", "Tilaknagar Main Road", 2),
    ("INT_015_SWAGATMAIN_ROAD_JUNCTION", "INT_005_PUTTANNA_JUNCTION", "9th Main Jayanagar Corridor", 2),
    ("INT_005_PUTTANNA_JUNCTION", "INT_006_RAJALAXMIKALYANAMANTAPA", "South End Circle Connector", 2),

    # Corridor 2: East Corridor (Indiranagar - CMH Road - Old Madras Road)
    ("INT_010_B_M_SHRI_CMH_100FT_ROAD_J", "INT_108_CMH_ROAD_DOUBLE_ROAD_JUNC", "CMH Road", 2),
    ("INT_108_CMH_ROAD_DOUBLE_ROAD_JUNC", "INT_073_OLDMADRAS_ROAD_INDIRANAGA", "Indiranagar Double Road", 2),
    ("INT_073_OLDMADRAS_ROAD_INDIRANAGA", "INT_022_BEML_GATE_JUNCTION_SURANJ", "Suranjan Das Road", 2),
    ("INT_022_BEML_GATE_JUNCTION_SURANJ", "INT_023_BIGBAZAAR_JUNCTION_PHARME", "Suranjan Das Road Extn", 2),
    ("INT_073_OLDMADRAS_ROAD_INDIRANAGA", "INT_018_RAMAIAH_CIRCLE_ULSOOR_POL", "Old Madras Road Arterial", 3),
    ("INT_018_RAMAIAH_CIRCLE_ULSOOR_POL", "INT_019_TAMARIKANNAN_JUNCTION", "Kensington Road / Murphy Rd", 2),
    ("INT_019_TAMARIKANNAN_JUNCTION", "INT_020_MOSQUE_CIRCLE_MOSQUERD_MM", "Frazer Town MM Road Link", 2),
    ("INT_020_MOSQUE_CIRCLE_MOSQUERD_MM", "INT_021_POTTERY_CIRCLE_JUNCTION", "Mosque Road / Pottery Road", 2),

    # Corridor 3: West Corridor (Mysore Road - Vijayanagar - Rajajinagar)
    ("INT_001_RAJARAJESHWARI_JUNCTION", "INT_002_SATELLITEBUSSTAND_JUNCTIO", "Mysore Road Arterial", 3),
    ("INT_002_SATELLITEBUSSTAND_JUNCTIO", "INT_040_VIJAYANAGARBUSSTAND_JUNCT", "Chord Road Link", 2),
    ("INT_040_VIJAYANAGARBUSSTAND_JUNCT", "INT_039_SHIVANAHALLI_JUNCTION", "West of Chord Road", 3),
    ("INT_039_SHIVANAHALLI_JUNCTION", "INT_034_MAHALAXMIENTRANCE_JUNCTIO", "West of Chord Road Extn", 3),
    ("INT_038_MARENAHALLI_JUNCTION_VIJA", "INT_040_VIJAYANAGARBUSSTAND_JUNCT", "Vijayanagar 1st Main", 2),

    # Corridor 4: North Corridor (Sadashivanagar - Hebbal - Yelahanka)
    ("INT_041_BHASHYAM_CIRCLE_JUNCTION", "INT_042_MEKHRI_CIRCLE_JUNCTION", "Bellary Road Expressway", 3),
    ("INT_042_MEKHRI_CIRCLE_JUNCTION", "INT_045_CHAUNDARAYA_CIRCLE_UDAYAT", "High Grounds Link", 2),
    ("INT_029_KOGILU_CROSS_JUNCTION", "INT_030_YELAHANKA_CIRCLE_JUNCTION", "Yelahanka Airport Road", 3),
    ("INT_044_AMRITAHALLI_JUNCTION_BYAT", "INT_030_YELAHANKA_CIRCLE_JUNCTION", "Bellary Highway Section", 3),

    # Corridor 5: Outer Ring Road / KR Puram / Marathahalli / Kanakapura
    ("INT_126_SILKBOARD_JUNCTION", "INT_218_MARATHALLIBRIDGE_JUNCTION", "Outer Ring Road Arterial", 3),
    ("INT_218_MARATHALLIBRIDGE_JUNCTION", "INT_173_DODDANEKUNDI_JUNCTION", "Outer Ring Road Expressway", 3),
    ("INT_007_KANAKAPURA_RING_ROAD_JUNC", "INT_008_KONANAKUNTE_JUNCTION_KANA", "Kanakapura Road", 3),
]

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate geographical distance in meters between two lat/lon points."""
    R = 6371000 # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def map_police_station_to_corridor(ps: str, name: str = "") -> str:
    """Classify intersection into regional arterial corridor by jurisdiction and name."""
    ps_u = str(ps).upper()
    nm_u = str(name).upper()
    if any(k in ps_u or k in nm_u for k in ["ADUGODI", "KORAMANGALA", "WILSON", "MICO", "JAYANAGAR"]):
        return "Corridor 1: South-Central (Adugodi - Koramangala - Wilson Garden - Dairy Circle)"
    elif any(k in ps_u or k in nm_u for k in ["INDIRANAGAR", "FRAZER", "ULSOOR", "CMH"]):
        return "Corridor 2: East (Indiranagar - CMH Road - Old Madras Road - Frazer Town)"
    elif any(k in ps_u or k in nm_u for k in ["BYATARAYANAPURA", "VIJAYANAGAR", "RAJAJINAGAR", "KAMAKSHIPALYA", "MYSORE"]):
        return "Corridor 3: West (Mysore Road - Byatarayanapura - Vijayanagar)"
    elif any(k in ps_u or k in nm_u for k in ["SADASHIVANAGAR", "HEBBAL", "YELAHANKA", "HIGHGROUNDS", "HIGH GROUNDS"]):
        return "Corridor 4: North (Sadashivanagar - Hebbal - Yelahanka)"
    elif any(k in ps_u or k in nm_u for k in ["K.S.LAYOUT", "BANASHANKARI", "KANAKAPURA"]):
        return "Corridor 5: South-West (Kanakapura - Banashankari)"
    else:
        return "Central Arterials"

class GraphBuilder:
    def __init__(self, data_dir: str = "data/processed"):
        self.data_dir = data_dir
        self.df_intersections = pd.read_csv(os.path.join(self.data_dir, "intersections.csv"))
        self.df_roads = pd.read_csv(os.path.join(self.data_dir, "roads.csv"))
        self.df_phases = pd.read_csv(os.path.join(self.data_dir, "signal_phases.csv"))
        self.df_timings = pd.read_csv(os.path.join(self.data_dir, "signal_timings.csv"))

    def get_corridors_list(self) -> List[str]:
        """Return available primary study corridors."""
        return [
            "Corridor 1: South-Central (Adugodi - Koramangala - Wilson Garden - Dairy Circle)",
            "Corridor 2: East (Indiranagar - CMH Road - Old Madras Road - Frazer Town)",
            "Corridor 3: West (Mysore Road - Byatarayanapura - Vijayanagar)",
            "Corridor 4: North (Sadashivanagar - Hebbal - Yelahanka)",
            "All Connected Corridors (Master Bengaluru Network)"
        ]

    def build_macro_graph(self, corridor_filter: Optional[str] = None) -> nx.DiGraph:
        """
        Build Level 1 Macro Graph G = (V, E) where:
          V = Intersections
          E = Directed connecting road segments
        """
        G = nx.DiGraph()

        # Build node dictionary
        int_lookup = {}
        for _, row in self.df_intersections.iterrows():
            int_id = row["intersection_id"]
            int_lookup[int_id] = row
            cycle_t = self._get_average_cycle_time(int_id)
            corr = map_police_station_to_corridor(row.get("police_station", ""), row.get("name", ""))
            lat_f = float(row["latitude"])
            lon_f = float(row["longitude"])
            G.add_node(
                int_id,
                name=row["name"],
                police_station=row["police_station"],
                control_type=row["control_type"],
                corridor=corr,
                latitude=lat_f,
                longitude=lon_f,
                lat=lat_f,
                lon=lon_f,
                pos=(lon_f, lat_f),
                num_approaches=int(row["num_approaches"]),
                source_pdf=row["source_pdf"],
                cycle_time=cycle_t,
                cycle_time_sec=cycle_t
            )

        # Build verified corridor links
        # Check matching ID or partial match
        all_int_ids = list(int_lookup.keys())

        def resolve_id(id_pattern: str) -> Optional[str]:
            for full_id in all_int_ids:
                if id_pattern in full_id or full_id in id_pattern:
                    return full_id
                # Check prefix match
                if id_pattern[:15] in full_id:
                    return full_id
            return None

        # Add verified physical corridor edges (bidirectional)
        edges_added = 0
        for src_pat, dst_pat, road_name, lanes in VERIFIED_CORRIDOR_CONNECTIONS:
            src_id = resolve_id(src_pat)
            dst_id = resolve_id(dst_pat)
            if src_id and dst_id and src_id != dst_id:
                node_u = G.nodes[src_id]
                node_v = G.nodes[dst_id]
                dist_m = haversine_distance(node_u["latitude"], node_u["longitude"], node_v["latitude"], node_v["longitude"])
                dist_m = max(350.0, min(dist_m, 2500.0)) # Clamped to realistic urban segment lengths

                free_speed = 40.0 # km/h
                free_time_min = (dist_m / 1000.0) / free_speed * 60.0 # minutes
                capacity = lanes * 1200 # PCU/hr

                # Add forward edge
                G.add_edge(
                    src_id, dst_id,
                    road_name=road_name,
                    lanes=lanes,
                    length_m=round(dist_m, 1),
                    free_flow_speed_kmh=free_speed,
                    free_flow_time_min=round(free_time_min, 2),
                    base_capacity=capacity,
                    physical_capacity=capacity,
                    effective_capacity=round(capacity * 0.45, 0), # Initial green split ~45%
                    signal_delay_min=0.5, # Initial baseline delay
                    cost=round(free_time_min + 0.5, 2), # Initial cost = travel time + delay
                    traffic_flow=0.0
                )

                # Add reverse edge
                G.add_edge(
                    dst_id, src_id,
                    road_name=f"{road_name} (Opposite)",
                    lanes=lanes,
                    length_m=round(dist_m, 1),
                    free_flow_speed_kmh=free_speed,
                    free_flow_time_min=round(free_time_min, 2),
                    base_capacity=capacity,
                    physical_capacity=capacity,
                    effective_capacity=round(capacity * 0.45, 0),
                    signal_delay_min=0.5,
                    cost=round(free_time_min + 0.5, 2),
                    traffic_flow=0.0
                )
                edges_added += 2

        # Connect any remaining proximate nodes in the same police station jurisdiction (<= 1.2km)
        # to ensure complete topological connectivity within police divisions
        by_ps = {}
        for nid, data in G.nodes(data=True):
            ps = data["police_station"]
            by_ps.setdefault(ps, []).append(nid)

        for ps, node_list in by_ps.items():
            for i in range(len(node_list) - 1):
                u = node_list[i]
                v = node_list[i + 1]
                if not G.has_edge(u, v):
                    dist_m = haversine_distance(G.nodes[u]["latitude"], G.nodes[u]["longitude"], G.nodes[v]["latitude"], G.nodes[v]["longitude"])
                    if dist_m <= 1800.0:
                        dist_m = max(400.0, dist_m)
                        time_min = (dist_m / 1000.0) / 35.0 * 60.0
                        cap = 2400 # 2 lanes
                        G.add_edge(u, v, road_name=f"{ps} Arterial Connector", lanes=2, length_m=round(dist_m, 1),
                                   free_flow_speed_kmh=35.0, free_flow_time_min=round(time_min, 2),
                                   base_capacity=cap, physical_capacity=cap, effective_capacity=round(cap * 0.45, 0),
                                   signal_delay_min=0.5, cost=round(time_min + 0.5, 2), traffic_flow=0.0)
                        G.add_edge(v, u, road_name=f"{ps} Arterial Connector", lanes=2, length_m=round(dist_m, 1),
                                   free_flow_speed_kmh=35.0, free_flow_time_min=round(time_min, 2),
                                   base_capacity=cap, physical_capacity=cap, effective_capacity=round(cap * 0.45, 0),
                                   signal_delay_min=0.5, cost=round(time_min + 0.5, 2), traffic_flow=0.0)

        # 1. Connect every node to its k-nearest neighbors (k=3 within 3.5 km) for full arterial mesh
        all_nodes = list(G.nodes())
        for u in all_nodes:
            u_lat = G.nodes[u]["latitude"]
            u_lon = G.nodes[u]["longitude"]
            dists = [
                (haversine_distance(u_lat, u_lon, G.nodes[v]["latitude"], G.nodes[v]["longitude"]), v)
                for v in all_nodes if u != v
            ]
            dists.sort()
            for d_val, v in dists[:3]:
                if d_val <= 3500.0 and not G.has_edge(u, v):
                    time_min = (d_val / 1000.0) / 40.0 * 60.0
                    cap = 3600 # 3 lanes
                    G.add_edge(u, v, road_name="Arterial Link", lanes=3, length_m=round(d_val, 1),
                               free_flow_speed_kmh=40.0, free_flow_time_min=round(time_min, 2),
                               base_capacity=cap, physical_capacity=cap, effective_capacity=round(cap * 0.5, 0),
                               signal_delay_min=0.5, cost=round(time_min + 0.5, 2), traffic_flow=0.0)
                    G.add_edge(v, u, road_name="Arterial Link", lanes=3, length_m=round(d_val, 1),
                               free_flow_speed_kmh=40.0, free_flow_time_min=round(time_min, 2),
                               base_capacity=cap, physical_capacity=cap, effective_capacity=round(cap * 0.5, 0),
                               signal_delay_min=0.5, cost=round(time_min + 0.5, 2), traffic_flow=0.0)

        # 2. Highway and arterial bridges connecting regional corridors into a single strongly connected network:
        HIGHWAY_BRIDGES = [
            ("INT_064_BHEL_JUNCTION", "INT_068_MADIWALACHECKPOST_JUNCTIO", "Hosur Road Expressway (NH 44)", 4),
            ("INT_087_HOPEFARM_JUNCTION", "INT_173_DODDANEKUNDI_JUNCTION", "Whitefield Main Road / ITPL Rd", 3),
            ("INT_173_DODDANEKUNDI_JUNCTION", "INT_086_MANIPALHOSPITAL_JUNCTION", "Old Airport Road Arterial", 3),
            ("INT_036_JALAHALLI_CROSS_SM_CIRCLE", "INT_145_KUVEMPU_CIRCLE_BEL_JUNCTI", "Tumkur Road Expressway (NH 48)", 4),
            ("INT_029_KOGILU_CROSS_JUNCTION", "INT_113_HEBBALFLYOVER_JUNCTION", "Bellary Road (NH 44 North)", 4),
            ("INT_063_VIJIPURA_CROSS_DEVANAHALL", "INT_030_YELAHANKA_CIRCLE_JUNCTION", "KIA Airport Expressway Section", 4),
            ("INT_007_KANAKAPURA_RING_ROAD_JUNC", "INT_006_RAJALAXMIKALYANAMANTAPA", "Kanakapura Road Arterial", 3),
            ("INT_001_RAJARAJESHWARI_JUNCTION", "INT_052_PRASANNA_JUNCTION", "Mysore Road - Magadi Link", 3),
            ("INT_068_MADIWALACHECKPOST_JUNCTIO", "INT_003_ADUGODI_JUNCTION", "Hosur Road Corridor", 3),
            ("INT_079_HSR14THMAIN_JUNCTION", "INT_173_DODDANEKUNDI_JUNCTION", "Outer Ring Road (Bellandur - Marathahalli)", 4),
            ("INT_010_B_M_SHRI_CMH_100FT_ROAD_J", "INT_018_RAMAIAH_CIRCLE_ULSOOR_POL", "Old Madras Road - Indiranagar Link", 3),
            ("INT_106_CB_ROADAIRPORT_JUNCTION", "INT_086_MANIPALHOSPITAL_JUNCTION", "Old Airport Road Connection", 3),
            ("INT_034_MAHALAXMIENTRANCE_JUNCTIO", "INT_039_SHIVANAHALLI_JUNCTION", "West of Chord Road Arterial", 3),
            ("INT_049_RAJAJINAGAR1STBLOCK_JUNCT", "INT_041_BHASHYAM_CIRCLE_JUNCTION", "Malleshwaram - Sadashivanagar Link", 3),
        ]

        for u, v, r_name, lanes in HIGHWAY_BRIDGES:
            if u in G and v in G:
                d_val = haversine_distance(G.nodes[u]["latitude"], G.nodes[u]["longitude"], G.nodes[v]["latitude"], G.nodes[v]["longitude"])
                d_val = max(1000.0, d_val)
                time_min = (d_val / 1000.0) / 45.0 * 60.0
                cap = lanes * 1500
                G.add_edge(u, v, road_name=r_name, lanes=lanes, length_m=round(d_val, 1),
                           free_flow_speed_kmh=45.0, free_flow_time_min=round(time_min, 2),
                           base_capacity=cap, physical_capacity=cap, effective_capacity=round(cap * 0.5, 0),
                           signal_delay_min=0.3, cost=round(time_min + 0.3, 2), traffic_flow=0.0)
                G.add_edge(v, u, road_name=r_name, lanes=lanes, length_m=round(d_val, 1),
                           free_flow_speed_kmh=45.0, free_flow_time_min=round(time_min, 2),
                           base_capacity=cap, physical_capacity=cap, effective_capacity=round(cap * 0.5, 0),
                           signal_delay_min=0.3, cost=round(time_min + 0.3, 2), traffic_flow=0.0)

        # Filter by corridor if requested
        if corridor_filter and "Corridor 1" in corridor_filter:
            c1_ps = ["ADUGODI", "KORAMANGALA", "WILSON GARDEN", "MICO LAYOUT", "JAYANAGAR"]
            sub_nodes = [n for n, d in G.nodes(data=True) if any(k in d["police_station"].upper() or k in d["name"].upper() for k in c1_ps)]
            G = G.subgraph(sub_nodes).copy()
        elif corridor_filter and "Corridor 2" in corridor_filter:
            c2_ps = ["INDIRANAGAR", "FRAZER TOWN", "ULSOOR"]
            sub_nodes = [n for n, d in G.nodes(data=True) if any(k in d["police_station"].upper() or k in d["name"].upper() for k in c2_ps)]
            G = G.subgraph(sub_nodes).copy()
        elif corridor_filter and "Corridor 3" in corridor_filter:
            c3_ps = ["BYATARAYANAPURA", "VIJAYANAGAR", "RAJAJINAGAR", "KAMAKSHIPALYA", "MYSORE"]
            sub_nodes = [n for n, d in G.nodes(data=True) if any(k in d["police_station"].upper() or k in d["name"].upper() for k in c3_ps)]
            G = G.subgraph(sub_nodes).copy()

        return G

    def build_micro_movement_graph(self, intersection_id: str) -> nx.DiGraph:
        """
        Build Level 2 Micro Turning Graph for a single intersection.
        Nodes = Approaches (A, B, C, D) and internal conflict points.
        Edges = Permitted turning movements (Left, Straight, Right) governed by signal phases.
        """
        G_micro = nx.DiGraph()

        # Approaches for this intersection
        roads_sub = self.df_roads[self.df_roads["intersection_id"] == intersection_id]
        phases_sub = self.df_phases[self.df_phases["intersection_id"] == intersection_id]

        # Add approach nodes
        for _, r in roads_sub.iterrows():
            G_micro.add_node(
                f"APP_{r['approach_code']}",
                road_name=r["road_name"],
                lanes=r["lanes"],
                capacity=r["capacity_pcu_hr"],
                type="APPROACH"
            )

        # Add movement edges governed by phases
        for _, ph in phases_sub.iterrows():
            if ph.get("is_pedestrian_phase", False):
                continue
            p_no = ph["phase_number"]
            app_code = ph["approach_code"]
            mvts = str(ph.get("permitted_movements", "STRAIGHT")).upper()

            src_node = f"APP_{app_code}" if f"APP_{app_code}" in G_micro else "APP_A"
            movement_keys = [
                ("LEFT", ["L", "LEFT"]),
                ("STRAIGHT", ["S", "STRAIGHT", "THRU"]),
                ("RIGHT", ["R", "RIGHT"])
            ]
            for m_type, triggers in movement_keys:
                if any(tr in mvts.split(", ") or tr == mvts or f" {tr}" in mvts or f"{tr} " in mvts or tr in mvts for tr in triggers):
                    dst_node = f"EXIT_{app_code}_{m_type}"
                    G_micro.add_node(dst_node, type="EXIT")
                    G_micro.add_edge(
                        src_node, dst_node,
                        movement=m_type,
                        phase_number=p_no,
                        saturation_flow=1800 * 2, # PCU/hr of green
                        green_ratio=0.35
                    )

        return G_micro

    def _get_average_cycle_time(self, intersection_id: str) -> int:
        """Fetch stated cycle time for an intersection."""
        sub = self.df_timings[self.df_timings["intersection_id"] == intersection_id]
        if not sub.empty:
            return int(sub["cycle_length_sec"].iloc[0])
        return 120 # Standard default

    def build_complete_bengaluru_network(self) -> Tuple[nx.DiGraph, nx.DiGraph]:
        """Builds Level 1 Macro graph and Level 2 Micro graph for the primary intersection."""
        G_macro = self.build_macro_graph()
        first_id = list(G_macro.nodes())[0] if G_macro.nodes else "INT_001_RAJARAJESHWARI_JUNCTION"
        G_micro = self.build_micro_movement_graph(first_id)
        return G_macro, G_micro
