"""
Signal Delay Estimation Model Module.
Phase 4 — Task 6: Mathematically Defensible Signal Delay Modeling.

Implements Webster's uniform delay approximation for fixed-time undersaturated
traffic signals (IRC:93-1985 / Highway Capacity Manual):

    d_signal = R² / (2 * C)

Where:
- R = C - G = Red duration for the relevant approach movement (seconds).
- G = Effective green duration (seconds).
- C = Signal cycle length (seconds).

Key Properties & Assumptions:
1. Uniform vehicle arrival assumption: In the absence of real-time loop detector / queue
   measurements, arrivals are assumed uniform over the cycle.
2. Undersaturated operation: Valid for demand volume within capacity (v/c < 1.0).
3. Queue delay disclaimer: The static timing records do not record physical queues or spillback.
   The model explicitly does NOT claim to represent congested queue clearance or emergency preemption.
4. Non-negative & bounded:
   For any valid timing plan (0 < G <= C), 0 <= d_signal <= C / 2.
   All delays are strictly finite and non-negative, preserving Dijkstra's optimality guarantee.
5. Graceful fallback: If signal data is missing or flagged as invalid, baseline road
   travel time is preserved (d_signal = 0.0), and the reason is recorded.
"""

import os
import math
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd

DEFAULT_TOD_PLAN = "WEEKDAY_MORNING_PEAK"
SUPPORTED_TOD_PLANS = [
    "WEEKDAY_MORNING_PEAK",
    "WEEKDAY_EVENING_PEAK",
    "WEEKDAY_INTER_PEAK",
    "WEEKDAY_NIGHT_OFFPEAK",
    "SUNDAY_PLAN"
]


def calculate_webster_uniform_delay(
    cycle_sec: float,
    green_sec: float,
    yellow_sec: float = 3.0,
    all_red_sec: float = 1.0
) -> Tuple[float, float]:
    """
    Computes Webster's uniform delay: d = R^2 / (2 * C).
    Returns: (delay_sec, delay_min).
    Guarantees non-negative, finite result.
    """
    if cycle_sec <= 0 or math.isnan(cycle_sec):
        return 0.0, 0.0
    if green_sec is None or math.isnan(green_sec) or green_sec < 0:
        return 0.0, 0.0

    # Effective green cannot exceed cycle length
    g = min(float(green_sec), float(cycle_sec))
    r = max(0.0, float(cycle_sec) - g)

    if r == 0.0:
        return 0.0, 0.0

    delay_sec = (r ** 2) / (2.0 * float(cycle_sec))
    delay_sec = round(max(0.0, delay_sec), 2)
    delay_min = round(delay_sec / 60.0, 4)

    return delay_sec, delay_min


class SignalDelayModel:
    def __init__(
        self,
        mapping_csv_path: str = "data/processed/signal_network_mapping.csv",
        timings_csv_path: str = "data/processed/signal_timings.csv",
        audit_csv_path: str = "data/processed/signal_validation_audit.csv"
    ):
        self.mapping_csv_path = mapping_csv_path
        self.timings_csv_path = timings_csv_path
        self.audit_csv_path = audit_csv_path

        self.df_mapping = pd.read_csv(mapping_csv_path) if os.path.exists(mapping_csv_path) else pd.DataFrame()
        self.df_timings = pd.read_csv(timings_csv_path) if os.path.exists(timings_csv_path) else pd.DataFrame()
        self.df_audit = pd.read_csv(audit_csv_path) if os.path.exists(audit_csv_path) else pd.DataFrame()

        # Build set of severely flagged timing IDs/intersections from audit
        self.severe_error_records = set()
        if not self.df_audit.empty:
            errors = self.df_audit[self.df_audit["severity"] == "ERROR"]
            self.severe_error_records = set(errors["record_id"].astype(str))

        # Index timings by (intersection_id, plan_name, phase_number)
        self.timing_lookup: Dict[Tuple[str, str, int], Dict[str, Any]] = {}
        if not self.df_timings.empty:
            for _, r in self.df_timings.iterrows():
                iid = str(r["intersection_id"]).strip()
                pname = str(r["plan_name"]).strip()
                pnum = int(r.get("phase_number", 1))
                key = (iid, pname, pnum)
                self.timing_lookup[key] = r.to_dict()

    def get_edge_signal_delay(
        self,
        edge_id: str,
        time_of_day_plan: str = DEFAULT_TOD_PLAN
    ) -> Dict[str, Any]:
        """
        Retrieves estimated signal delay for a specific road edge under a time-of-day plan.
        """
        if self.df_mapping.empty:
            return self._build_unavailable_record(edge_id, "NO_MAPPING_DATA")

        match_rows = self.df_mapping[self.df_mapping["road_edge_id"] == edge_id]
        if match_rows.empty:
            return self._build_unavailable_record(edge_id, "EDGE_NOT_IN_SIGNAL_MAPPING")

        m = match_rows.iloc[0]
        iid = str(m["gis_junction_id"]).strip()
        phase_num = int(m.get("signal_phase_number", 1))
        phase_id = str(m.get("signal_phase_id", "PH_0001"))
        verif_status = str(m.get("verification_status", "UNVERIFIED"))

        # Lookup timing record
        timing_key = (iid, time_of_day_plan, phase_num)
        timing_rec = self.timing_lookup.get(timing_key)

        # Fallback to any available plan if specific plan not found for this junction
        plan_used = time_of_day_plan
        if not timing_rec:
            # Try finding any peak or offpeak plan for this junction and phase
            for (tiid, tpname, tpnum), cand in self.timing_lookup.items():
                if tiid == iid and tpnum == phase_num:
                    timing_rec = cand
                    plan_used = tpname
                    break

        if not timing_rec:
            return self._build_unavailable_record(
                edge_id, f"NO_TIMING_RECORD_FOR_{iid}_P{phase_num}",
                intersection_id=iid, phase_id=phase_id
            )

        timing_id = str(timing_rec.get("timing_id", ""))
        c_sec = float(timing_rec.get("cycle_length_sec", 120.0))
        g_sec = float(timing_rec.get("green_time_sec", 30.0))

        # Check if record has severe data quality errors
        if timing_id in self.severe_error_records or c_sec < 20 or g_sec <= 0:
            return {
                "edge_id": edge_id,
                "intersection_id": iid,
                "phase_id": phase_id,
                "phase_number": phase_num,
                "approach_code": str(m.get("approach_code", "A")),
                "plan_name": plan_used,
                "cycle_sec": c_sec,
                "green_sec": g_sec,
                "red_sec": max(0.0, c_sec - g_sec),
                "signal_delay_sec": 0.0,
                "signal_delay_min": 0.0,
                "is_signal_available": False,
                "verification_status": "FLAGGED_SUPPRESSED",
                "reason": f"Signal delay suppressed due to data discrepancy audit on timing {timing_id}"
            }

        # Calculate Webster uniform delay
        d_sec, d_min = calculate_webster_uniform_delay(c_sec, g_sec)
        r_sec = max(0.0, c_sec - g_sec)

        return {
            "edge_id": edge_id,
            "intersection_id": iid,
            "phase_id": phase_id,
            "phase_number": phase_num,
            "approach_code": str(m.get("approach_code", "A")),
            "plan_name": plan_used,
            "cycle_sec": c_sec,
            "green_sec": g_sec,
            "red_sec": r_sec,
            "signal_delay_sec": d_sec,
            "signal_delay_min": d_min,
            "is_signal_available": True,
            "verification_status": verif_status,
            "reason": f"Webster uniform delay: ({r_sec:.1f}s)^2 / (2 * {c_sec:.1f}s) = {d_sec:.2f}s"
        }

    def _build_unavailable_record(
        self,
        edge_id: str,
        reason: str,
        intersection_id: str = "N/A",
        phase_id: str = "N/A"
    ) -> Dict[str, Any]:
        return {
            "edge_id": edge_id,
            "intersection_id": intersection_id,
            "phase_id": phase_id,
            "phase_number": 0,
            "approach_code": "NONE",
            "plan_name": "NONE",
            "cycle_sec": 0.0,
            "green_sec": 0.0,
            "red_sec": 0.0,
            "signal_delay_sec": 0.0,
            "signal_delay_min": 0.0,
            "is_signal_available": False,
            "verification_status": "UNAVAILABLE",
            "reason": reason
        }

    def compute_all_edge_delays(
        self,
        time_of_day_plan: str = DEFAULT_TOD_PLAN
    ) -> pd.DataFrame:
        """Computes signal delay across all 1164 network edges for a TOD plan."""
        records = []
        if not self.df_mapping.empty:
            for _, r in self.df_mapping.iterrows():
                eid = r["road_edge_id"]
                delay_info = self.get_edge_signal_delay(eid, time_of_day_plan)
                records.append(delay_info)

        return pd.DataFrame(records)


def generate_and_save_edge_signal_delays(
    output_path: str = "data/processed/edge_signal_delays.csv",
    time_of_day_plan: str = DEFAULT_TOD_PLAN
) -> pd.DataFrame:
    """Pre-computes and exports network edge signal delays."""
    model = SignalDelayModel()
    df_delays = model.compute_all_edge_delays(time_of_day_plan)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_delays.to_csv(output_path, index=False)
    return df_delays


if __name__ == "__main__":
    df_delays = generate_and_save_edge_signal_delays()
    print(f"Computed edge signal delays for {len(df_delays)} links under {DEFAULT_TOD_PLAN}.")
    print("Available vs Unavailable:\n", df_delays["is_signal_available"].value_counts())
    print("Signal Delay (sec) distribution:\n", df_delays[df_delays["is_signal_available"]]["signal_delay_sec"].describe())
