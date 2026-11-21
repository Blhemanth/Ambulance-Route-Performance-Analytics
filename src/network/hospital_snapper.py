"""
Hospital-to-Road Network Snapping and Spatial Access Module.
Ambulance Route Optimization — Bengaluru.

Maps Bengaluru hospital locations onto candidate nodes and directed edges of the
validated Bengaluru road network using configurable distance thresholds and
explicit verification tagging without fabricating straight-line ambulance routes.
"""

import os
import json
import math
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd
import networkx as nx

def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates geographical distance between two lat/lon points in meters."""
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def distance_point_to_segment_m(
    p_lat: float, p_lon: float,
    a_lat: float, a_lon: float,
    b_lat: float, b_lon: float
) -> Tuple[float, float, float]:
    """
    Computes minimum distance from point P to line segment AB,
    and returns (distance_m, projected_lat, projected_lon).
    Uses equirectangular projection approximation for local Euclidean calculations.
    """
    # Convert lat/lon degrees to local meters relative to A
    cos_lat = math.cos(math.radians((a_lat + b_lat) / 2.0))
    kx = 111320.0 * cos_lat
    ky = 110540.0

    px, py = (p_lon - a_lon) * kx, (p_lat - a_lat) * ky
    bx, by = (b_lon - a_lon) * kx, (b_lat - a_lat) * ky

    seg_len_sq = bx * bx + by * by
    if seg_len_sq <= 1e-6:
        dist = math.sqrt(px * px + py * py)
        return dist, a_lat, a_lon

    # Projection parameter t clamped to [0, 1]
    t = max(0.0, min(1.0, (px * bx + py * by) / seg_len_sq))
    proj_x = t * bx
    proj_y = t * by

    dx = px - proj_x
    dy = py - proj_y
    dist = math.sqrt(dx * dx + dy * dy)

    proj_lon = a_lon + (proj_x / kx)
    proj_lat = a_lat + (proj_y / ky)

    return dist, proj_lat, proj_lon

class HospitalRoadSnapper:
    """
    Identifies candidate road connections for hospitals against the
    Operations Research road network.
    Implements Task 4 of Phase 1.
    """

    def __init__(
        self,
        intersections_path: str = "data/processed/intersections_gis.csv",
        roads_gis_path: str = "data/processed/roads_gis.json",
        default_threshold_m: float = 2000.0
    ):
        self.intersections_path = intersections_path
        self.roads_gis_path = roads_gis_path
        self.threshold_m = default_threshold_m
        
        self.df_intersections: Optional[pd.DataFrame] = None
        self.roads_catalog: List[Dict[str, Any]] = []
        self._load_network_data()

    def _load_network_data(self):
        """Loads intersections and road GIS polyline data."""
        if not os.path.exists(self.intersections_path):
            raise FileNotFoundError(f"Missing intersections GIS file: {self.intersections_path}")
        self.df_intersections = pd.read_csv(self.intersections_path)

        if not os.path.exists(self.roads_gis_path):
            raise FileNotFoundError(f"Missing roads GIS file: {self.roads_gis_path}")
        with open(self.roads_gis_path, "r", encoding="utf-8") as f:
            self.roads_catalog = json.load(f)

    def snap_single_hospital(
        self,
        hosp_lat: Optional[float],
        hosp_lon: Optional[float],
        hosp_id: str,
        hosp_name: str,
        emergency_status: str
    ) -> Dict[str, Any]:
        """
        Calculates distance to candidate road network nodes and edges for one hospital.
        """
        if hosp_lat is None or hosp_lon is None:
            return {
                "hospital_id": hosp_id,
                "hospital_name": hosp_name,
                "emergency_status": emergency_status,
                "nearest_intersection_id": None,
                "nearest_intersection_name": None,
                "distance_to_intersection_m": None,
                "nearest_road_edge_id": None,
                "nearest_road_name": None,
                "distance_to_road_edge_m": None,
                "snapping_distance_m": None,
                "selected_connector_type": "NONE",
                "connection_status": "UNMATCHED_INVALID_GEOMETRY",
                "estimated_access_time_min": None,
                "snapped_lat": None,
                "snapped_lon": None,
                "exceeds_threshold": True
            }

        # 1. Candidate Intersection Search
        min_node_dist = float("inf")
        best_node_id = None
        best_node_name = None
        best_node_lat, best_node_lon = None, None

        for _, row in self.df_intersections.iterrows():
            nid = str(row["intersection_id"])
            nname = str(row["name"])
            nlat = float(row["latitude"])
            nlon = float(row["longitude"])
            d = haversine_distance_m(hosp_lat, hosp_lon, nlat, nlon)
            if d < min_node_dist:
                min_node_dist = d
                best_node_id = nid
                best_node_name = nname
                best_node_lat, best_node_lon = nlat, nlon

        # 2. Candidate Road Edge Search
        min_edge_dist = float("inf")
        best_edge_id = None
        best_road_name = None
        best_edge_from = None
        best_edge_to = None
        best_proj_lat, best_proj_lon = None, None

        for r in self.roads_catalog:
            eid = r.get("edge_id")
            rname = r.get("road_name", "Arterial Link")
            from_n = r.get("from_node")
            to_n = r.get("to_node")
            geom = r.get("geometry", [])

            if len(geom) >= 2:
                for i in range(len(geom) - 1):
                    a_lat, a_lon = geom[i]
                    b_lat, b_lon = geom[i + 1]
                    d_seg, p_lat, p_lon = distance_point_to_segment_m(
                        hosp_lat, hosp_lon, a_lat, a_lon, b_lat, b_lon
                    )
                    if d_seg < min_edge_dist:
                        min_edge_dist = d_seg
                        best_edge_id = eid
                        best_road_name = rname
                        best_edge_from = from_n
                        best_edge_to = to_n
                        best_proj_lat = p_lat
                        best_proj_lon = p_lon

        # Select primary connection
        # Edge snapping gives closer perpendicular street access
        if min_edge_dist <= min_node_dist:
            snap_dist = round(min_edge_dist, 1)
            connector_type = "ROAD_EDGE_POLYLINE"
            snapped_lat = round(best_proj_lat, 6) if best_proj_lat is not None else best_node_lat
            snapped_lon = round(best_proj_lon, 6) if best_proj_lon is not None else best_node_lon
        else:
            snap_dist = round(min_node_dist, 1)
            connector_type = "INTERSECTION_NODE"
            snapped_lat = best_node_lat
            snapped_lon = best_node_lon

        # Tiered Connection Status
        exceeds_threshold = snap_dist > self.threshold_m
        
        if exceeds_threshold:
            conn_status = "UNMATCHED_EXCEEDS_THRESHOLD"
        elif snap_dist <= 300.0:
            conn_status = "DIRECT_GATE_PROXIMITY"
        elif snap_dist <= 1000.0:
            conn_status = "ESTIMATED_CORRIDOR_PROXIMITY"
        else:
            conn_status = "ESTIMATED_DISTANT_ACCESS"

        # Estimated access penalty time (15 km/h local driveway + 1.0 min gate delay)
        # Only applicable if within threshold
        if not exceeds_threshold:
            access_time_min = round((snap_dist / 1000.0) / 15.0 * 60.0 + 1.0, 2)
        else:
            access_time_min = None

        return {
            "hospital_id": hosp_id,
            "hospital_name": hosp_name,
            "emergency_status": emergency_status,
            "hosp_lat": hosp_lat,
            "hosp_lon": hosp_lon,
            "nearest_intersection_id": best_node_id,
            "nearest_intersection_name": best_node_name,
            "distance_to_intersection_m": round(min_node_dist, 1),
            "nearest_road_edge_id": best_edge_id,
            "nearest_road_name": best_road_name,
            "nearest_road_from_node": best_edge_from,
            "nearest_road_to_node": best_edge_to,
            "distance_to_road_edge_m": round(min_edge_dist, 1),
            "snapping_distance_m": snap_dist,
            "selected_connector_type": connector_type,
            "connection_status": conn_status,
            "estimated_access_time_min": access_time_min,
            "snapped_lat": snapped_lat,
            "snapped_lon": snapped_lon,
            "exceeds_threshold": exceeds_threshold
        }

    def snap_all_hospitals(
        self,
        df_hospitals: pd.DataFrame,
        output_csv_path: str = "data/processed/hospital_road_connections.csv"
    ) -> pd.DataFrame:
        """
        Executes snapping across all hospital records and exports connection catalog.
        """
        records = []
        for _, row in df_hospitals.iterrows():
            res = self.snap_single_hospital(
                hosp_lat=row["latitude"],
                hosp_lon=row["longitude"],
                hosp_id=row["hospital_id"],
                hosp_name=row["hospital_name"],
                emergency_status=row["verification_status"]
            )
            records.append(res)

        df_connections = pd.DataFrame(records)
        os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
        df_connections.to_csv(output_csv_path, index=False, encoding="utf-8")
        return df_connections
