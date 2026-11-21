"""
Hospital Data Ingestion & Quality Classification Module.
Ambulance Route Optimization — Bengaluru.

Safely loads, validates, normalizes, deduplicates, and classifies hospital features
from the raw Overpass Turbo GeoJSON export without inventing any missing attributes.
"""

import os
import json
import math
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd

# Bounding box for Greater Bengaluru Metropolitan Area (BBMP + BMRDA urban extent)
BENGALURU_BBOX = {
    "min_lat": 12.70,
    "max_lat": 13.30,
    "min_lon": 77.30,
    "max_lon": 77.90
}

# Major verified multi-specialty trauma and emergency centres in Bengaluru
KNOWN_MAJOR_EMERGENCY_KEYWORDS = [
    "MANIPAL", "APOLLO", "FORTIS", "NARAYANA", "VICTORIA", "BOWRING",
    "SANJAY GANDHI", "RAMAIAH", "NIMHANS", "ST. JOHN", "ST JOHN",
    "COLUMBIA ASIA", "ASTER", "BAPTIST", "K.C. GENERAL", "KC GENERAL",
    "JAYADEVA", "INDIRA GANDHI", "ESI HOSPITAL", "COMMAND HOSPITAL"
]

def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two points in meters."""
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def extract_representative_point(geometry: Dict[str, Any]) -> Tuple[Optional[float], Optional[float], str]:
    """
    Extracts representative (latitude, longitude) coordinate from Point, Polygon,
    or MultiPolygon geometries.
    Returns: (latitude, longitude, geometry_type)
    """
    if not geometry or not isinstance(geometry, dict):
        return None, None, "UNKNOWN"

    gtype = geometry.get("type", "")
    coords = geometry.get("coordinates", [])

    if gtype == "Point":
        if len(coords) >= 2:
            return float(coords[1]), float(coords[0]), "Point"
        return None, None, "InvalidPoint"

    elif gtype == "Polygon":
        # Centroid of outer ring
        if coords and len(coords) > 0 and len(coords[0]) > 0:
            ring = coords[0]
            lons = [pt[0] for pt in ring]
            lats = [pt[1] for pt in ring]
            avg_lon = sum(lons) / len(lons)
            avg_lat = sum(lats) / len(lats)
            return avg_lat, avg_lon, "PolygonCentroid"
        return None, None, "InvalidPolygon"

    elif gtype == "MultiPolygon":
        all_lons = []
        all_lats = []
        for poly in coords:
            if poly and len(poly) > 0 and len(poly[0]) > 0:
                for pt in poly[0]:
                    all_lons.append(pt[0])
                    all_lats.append(pt[1])
        if all_lons and all_lats:
            return sum(all_lats) / len(all_lats), sum(all_lons) / len(all_lons), "MultiPolygonCentroid"
        return None, None, "InvalidMultiPolygon"

    return None, None, f"Unsupported_{gtype}"

class HospitalDataProcessor:
    """
    Ingests and normalizes the Bengaluru hospital dataset.
    Implements Task 2 and Task 3 of Phase 1.
    """

    def __init__(self, raw_geojson_path: str = "hospital dataset/export.geojson"):
        self.raw_geojson_path = raw_geojson_path
        self.raw_features: List[Dict[str, Any]] = []
        self.cleaned_records: List[Dict[str, Any]] = []
        self.quality_issues: List[Dict[str, Any]] = []
        self.df_hospitals: Optional[pd.DataFrame] = None

    def load_raw_geojson(self) -> List[Dict[str, Any]]:
        """Safely reads the raw GeoJSON file."""
        if not os.path.exists(self.raw_geojson_path):
            raise FileNotFoundError(f"Hospital GeoJSON not found at: {self.raw_geojson_path}")

        with open(self.raw_geojson_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.raw_features = data.get("features", [])
        return self.raw_features

    def process_and_classify(self) -> pd.DataFrame:
        """
        Processes all hospital features, normalizes attributes, detects duplicates,
        and assigns evidence-based verification statuses.
        """
        if not self.raw_features:
            self.load_raw_geojson()

        processed = []
        seen_names_coords: List[Tuple[str, float, float, int]] = []

        for idx, feat in enumerate(self.raw_features):
            props = feat.get("properties", {})
            geom = feat.get("geometry", {})

            # 1. Coordinate extraction
            lat, lon, geom_method = extract_representative_point(geom)
            
            # Extract identifiers
            osm_id_raw = props.get("@id", props.get("id", f"unknown_{idx}"))
            osm_type = "node"
            osm_id = str(osm_id_raw)
            if "/" in str(osm_id_raw):
                parts = str(osm_id_raw).split("/")
                osm_type = parts[0]
                osm_id = parts[1]

            # Extract names & labels
            raw_name = props.get("name")
            name = str(raw_name).strip() if raw_name is not None and str(raw_name).strip() != "" else None
            
            # Extract tags
            amenity = props.get("amenity")
            healthcare = props.get("healthcare")
            emergency_tag = props.get("emergency")
            if emergency_tag is not None:
                emergency_tag = str(emergency_tag).strip().lower()

            operator = props.get("operator")
            website = props.get("website", props.get("contact:website"))
            phone = props.get("phone", props.get("contact:phone"))
            wheelchair = props.get("wheelchair")
            beds = props.get("beds")

            # Address compilation
            addr_parts = []
            for k in ["addr:housenumber", "addr:street", "addr:suburb", "addr:city", "addr:postcode"]:
                if props.get(k):
                    addr_parts.append(str(props[k]).strip())
            address = ", ".join(addr_parts) if addr_parts else None

            # Spatial boundary check
            is_valid_coords = (lat is not None and lon is not None and
                               -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0)
            
            is_within_bengaluru = False
            if is_valid_coords:
                is_within_bengaluru = (
                    BENGALURU_BBOX["min_lat"] <= lat <= BENGALURU_BBOX["max_lat"] and
                    BENGALURU_BBOX["min_lon"] <= lon <= BENGALURU_BBOX["max_lon"]
                )

            # Duplicate check by name and proximity (< 300 meters)
            is_duplicate = False
            duplicate_of_id = None
            if name and is_valid_coords:
                for s_name, s_lat, s_lon, s_id in seen_names_coords:
                    if s_name.lower() == name.lower():
                        dist = haversine_distance_m(lat, lon, s_lat, s_lon)
                        if dist < 300.0:  # Same facility mapped multiple times (e.g. node + relation)
                            is_duplicate = True
                            duplicate_of_id = s_id
                            break
                if not is_duplicate:
                    seen_names_coords.append((name, lat, lon, idx))

            # Quality Issue Logging
            issue_type = "VALID"
            if not is_valid_coords:
                issue_type = "INVALID_COORDINATES"
                self.quality_issues.append({
                    "feature_index": idx,
                    "osm_id": osm_id,
                    "issue": "Invalid or missing coordinates",
                    "action": "Flagged incomplete"
                })
            elif not is_within_bengaluru:
                issue_type = "OUTSIDE_BENGALURU_BBOX"
                self.quality_issues.append({
                    "feature_index": idx,
                    "osm_id": osm_id,
                    "issue": f"Coordinates ({lat:.4f}, {lon:.4f}) outside Bengaluru boundary",
                    "action": "Flagged outside bounds"
                })
            elif name is None:
                issue_type = "MISSING_NAME"
                self.quality_issues.append({
                    "feature_index": idx,
                    "osm_id": osm_id,
                    "issue": "Facility name is null or blank",
                    "action": "Assigned UNNAMED_FACILITY"
                })
            elif is_duplicate:
                issue_type = "DUPLICATE_RECORD"
                self.quality_issues.append({
                    "feature_index": idx,
                    "osm_id": osm_id,
                    "issue": f"Duplicate of feature {duplicate_of_id} ('{name}') within 300m",
                    "action": "Flagged duplicate"
                })

            # Task 3: Classification Logic
            verification_status = "INCOMPLETE_OR_QUESTIONABLE"
            emergency_service_type = "UNKNOWN"

            if not is_valid_coords or not is_within_bengaluru or name is None:
                verification_status = "INCOMPLETE_OR_QUESTIONABLE"
                emergency_service_type = "NON_OPERATIONAL_OR_INCOMPLETE"
            elif is_duplicate:
                verification_status = "DUPLICATE_ENTRY"
                emergency_service_type = "DUPLICATE"
            elif emergency_tag == "yes":
                verification_status = "VERIFIED_EMERGENCY"
                emergency_service_type = "LEVEL_1_EMERGENCY_TRAUMA"
            elif emergency_tag == "no":
                verification_status = "GENERAL_HEALTHCARE"
                emergency_service_type = "NON_EMERGENCY_FACILITY"
            else:
                # Emergency tag is null/missing
                # Check if hospital name matches verified tertiary trauma keyword
                name_upper = name.upper() if name else ""
                has_major_kw = any(kw in name_upper for kw in KNOWN_MAJOR_EMERGENCY_KEYWORDS)
                
                if has_major_kw and (amenity == "hospital" or healthcare == "hospital"):
                    # Known major hospital in Bengaluru, but emergency tag unverified in OSM
                    verification_status = "EMERGENCY_PROBABLE_UNVERIFIED"
                    emergency_service_type = "MAJOR_HOSPITAL_UNVERIFIED_CASUALTY"
                elif amenity == "hospital" or healthcare == "hospital":
                    verification_status = "HOSPITAL_EMERGENCY_UNVERIFIED"
                    emergency_service_type = "GENERAL_HOSPITAL_UNVERIFIED"
                else:
                    # Clinic, doctor, dentist, etc.
                    verification_status = "GENERAL_HEALTHCARE"
                    emergency_service_type = "OUTPATIENT_OR_SPECIALTY"

            rec = {
                "hospital_id": f"BLR_HOSP_{idx + 1:04d}",
                "osm_id": osm_id,
                "osm_type": osm_type,
                "hospital_name": name if name else f"Unnamed Facility ({osm_id})",
                "raw_name": raw_name,
                "latitude": round(lat, 6) if lat is not None else None,
                "longitude": round(lon, 6) if lon is not None else None,
                "address": address,
                "amenity": amenity,
                "healthcare": healthcare,
                "emergency": emergency_tag,
                "verification_status": verification_status,
                "emergency_service_type": emergency_service_type,
                "operator": operator,
                "website": website,
                "phone": phone,
                "wheelchair": wheelchair,
                "beds": beds,
                "geometry_method": geom_method,
                "is_duplicate": is_duplicate,
                "duplicate_of_index": duplicate_of_id,
                "data_quality_issue": issue_type,
                "source": "OpenStreetMap_Overpass_Turbo"
            }
            processed.append(rec)

        self.cleaned_records = processed
        self.df_hospitals = pd.DataFrame(processed)
        return self.df_hospitals

    def export_cleaned_datasets(self, output_dir: str = "data/processed") -> Dict[str, str]:
        """Exports normalized CSV and GeoJSON datasets and quality reports."""
        os.makedirs(output_dir, exist_ok=True)
        if self.df_hospitals is None:
            self.process_and_classify()

        csv_path = os.path.join(output_dir, "bengaluru_hospitals.csv")
        geojson_path = os.path.join(output_dir, "bengaluru_hospitals_cleaned.geojson")
        report_path = os.path.join(output_dir, "hospital_data_quality_report.csv")

        # 1. Save CSV
        self.df_hospitals.to_csv(csv_path, index=False, encoding="utf-8")

        # 2. Save Cleaned GeoJSON
        geojson_features = []
        for _, row in self.df_hospitals.iterrows():
            if pd.notna(row["latitude"]) and pd.notna(row["longitude"]):
                feat = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [float(row["longitude"]), float(row["latitude"])]
                    },
                    "properties": {
                        "hospital_id": row["hospital_id"],
                        "osm_id": row["osm_id"],
                        "hospital_name": row["hospital_name"],
                        "verification_status": row["verification_status"],
                        "emergency_service_type": row["emergency_service_type"],
                        "emergency": row["emergency"],
                        "amenity": row["amenity"],
                        "healthcare": row["healthcare"],
                        "address": row["address"],
                        "phone": row["phone"],
                        "website": row["website"]
                    }
                }
                geojson_features.append(feat)

        geojson_data = {
            "type": "FeatureCollection",
            "name": "Bengaluru_Hospitals_Cleaned",
            "crs": {
                "type": "name",
                "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}
            },
            "features": geojson_features
        }

        with open(geojson_path, "w", encoding="utf-8") as f:
            json.dump(geojson_data, f, indent=2)

        # 3. Save Quality Report
        df_quality = pd.DataFrame(self.quality_issues)
        if df_quality.empty:
            df_quality = pd.DataFrame(columns=["feature_index", "osm_id", "issue", "action"])
        df_quality.to_csv(report_path, index=False, encoding="utf-8")

        return {
            "csv": csv_path,
            "geojson": geojson_path,
            "quality_report": report_path
        }
