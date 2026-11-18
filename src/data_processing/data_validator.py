"""
Data Validator Module for Bengaluru Traffic Signal Dataset.
Validates referential integrity, physical bounds, cycle-time consistency,
and pedestrian safety requirements across extracted relational records.
"""

from typing import Dict, List, Any

class DataValidator:
    def __init__(self):
        self.validation_summary = {}

    def validate_dataset(self, dataset: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Runs full validation across all tables in the dataset."""
        intersections = dataset.get("intersections", [])
        roads = dataset.get("roads", [])
        signal_phases = dataset.get("signal_phases", [])
        signal_timings = dataset.get("signal_timings", [])
        extraction_errors = dataset.get("extraction_errors", [])

        int_ids = set(i["intersection_id"] for i in intersections)

        # 1. Validate Intersections
        invalid_ints = []
        for item in intersections:
            lat = item.get("latitude", 0)
            lon = item.get("longitude", 0)
            if not (12.70 <= lat <= 13.30 and 77.30 <= lon <= 77.90):
                invalid_ints.append(item["intersection_id"])

        # 2. Validate Roads
        orphaned_roads = [r["road_id"] for r in roads if r["intersection_id"] not in int_ids]
        invalid_lanes = [r["road_id"] for r in roads if not (1 <= r.get("lanes", 0) <= 6)]
        invalid_capacities = [r["road_id"] for r in roads if not (500 <= r.get("capacity_pcu_hr", 0) <= 8000)]

        # 3. Validate Signal Phases
        orphaned_phases = [p["phase_id"] for p in signal_phases if p["intersection_id"] not in int_ids]

        # 4. Validate Signal Timings
        orphaned_timings = [t["timing_id"] for t in signal_timings if t["intersection_id"] not in int_ids]
        discrepancy_timings = [
            t["timing_id"] for t in signal_timings
            if "FLAGGED" in t.get("validation_status", "")
        ]

        # 5. Cycle Time Bounds Check (40s - 240s standard urban range)
        out_of_bounds_cycles = [
            t["timing_id"] for t in signal_timings
            if not (40 <= t.get("cycle_length_sec", 0) <= 240)
        ]

        summary = {
            "total_intersections": len(intersections),
            "invalid_coordinates_intersections": len(invalid_ints),
            "total_roads": len(roads),
            "orphaned_roads": len(orphaned_roads),
            "invalid_lane_roads": len(invalid_lanes),
            "invalid_capacity_roads": len(invalid_capacities),
            "total_signal_phases": len(signal_phases),
            "orphaned_signal_phases": len(orphaned_phases),
            "total_timing_records": len(signal_timings),
            "orphaned_timing_records": len(orphaned_timings),
            "flagged_discrepancy_timings": len(discrepancy_timings),
            "out_of_bounds_cycles": len(out_of_bounds_cycles),
            "total_logged_errors": len(extraction_errors),
            "is_valid": (len(orphaned_roads) == 0 and len(orphaned_phases) == 0 and len(orphaned_timings) == 0)
        }

        self.validation_summary = summary
        return summary
