"""
Signal Data Validator Module for Bengaluru Traffic Signal Dataset.
Phase 4 — Task 4: Comprehensive Signal Data Validation.

Implements all 10 mandated data quality checks:
1. Missing junction names.
2. Duplicate timing plans.
3. Missing phase durations.
4. Invalid or negative durations.
5. Inconsistent cycle lengths (outside urban bounds 40s-260s).
6. Phase totals exceeding cycle length.
7. Missing approach information.
8. Conflicting timing plans (overlapping TOD intervals).
9. Incorrect time-of-day intervals.
10. Unreadable extraction results.

Flags questionable records for manual review without silently modifying original values.
Outputs: data/processed/signal_validation_audit.csv
"""

import os
import re
from typing import Dict, List, Any, Tuple
import pandas as pd


class SignalDataValidator:
    def __init__(
        self,
        intersections_path: str = "data/processed/intersections.csv",
        roads_path: str = "data/processed/roads.csv",
        phases_path: str = "data/processed/signal_phases.csv",
        timings_path: str = "data/processed/signal_timings.csv",
        pdf_inventory_path: str = "data/processed/pdf_inventory.csv"
    ):
        self.intersections_path = intersections_path
        self.roads_path = roads_path
        self.phases_path = phases_path
        self.timings_path = timings_path
        self.pdf_inventory_path = pdf_inventory_path

        self.df_intersections = pd.read_csv(intersections_path) if os.path.exists(intersections_path) else pd.DataFrame()
        self.df_roads = pd.read_csv(roads_path) if os.path.exists(roads_path) else pd.DataFrame()
        self.df_phases = pd.read_csv(phases_path) if os.path.exists(phases_path) else pd.DataFrame()
        self.df_timings = pd.read_csv(timings_path) if os.path.exists(timings_path) else pd.DataFrame()
        self.df_inventory = pd.read_csv(pdf_inventory_path) if os.path.exists(pdf_inventory_path) else pd.DataFrame()

        self.flagged_issues: List[Dict[str, Any]] = []

    def run_all_checks(self) -> pd.DataFrame:
        """Executes all 10 validation checks and returns consolidated audit findings."""
        self.flagged_issues.clear()

        self._check_1_missing_junction_names()
        self._check_2_duplicate_timing_plans()
        self._check_3_missing_phase_durations()
        self._check_4_invalid_or_negative_durations()
        self._check_5_inconsistent_cycle_lengths()
        self._check_6_phase_totals_exceeding_cycle()
        self._check_7_missing_approach_information()
        self._check_8_conflicting_timing_plans()
        self._check_9_incorrect_tod_intervals()
        self._check_10_unreadable_extraction_results()

        df_audit = pd.DataFrame(self.flagged_issues)
        if df_audit.empty:
            df_audit = pd.DataFrame(columns=[
                "check_number", "check_name", "record_id", "intersection_id",
                "severity", "issue_description", "raw_value", "recommended_action"
            ])
        return df_audit

    def _log_issue(
        self,
        check_number: int,
        check_name: str,
        record_id: str,
        intersection_id: str,
        severity: str,
        description: str,
        raw_val: Any,
        action: str
    ):
        self.flagged_issues.append({
            "check_number": check_number,
            "check_name": check_name,
            "record_id": str(record_id),
            "intersection_id": str(intersection_id),
            "severity": severity,  # WARNING, ERROR, INFO
            "issue_description": description,
            "raw_value": str(raw_val),
            "recommended_action": action
        })

    # Check 1: Missing junction names
    def _check_1_missing_junction_names(self):
        for _, row in self.df_intersections.iterrows():
            iid = row["intersection_id"]
            name = str(row.get("name", "")).strip()
            if not name or name.upper() in ["UNKNOWN", "NAN", "NONE"]:
                self._log_issue(1, "Missing Junction Name", iid, iid, "ERROR",
                                "Junction name is completely missing or empty", name,
                                "Conduct manual GIS inspection to assign canonical junction title")
            elif name.startswith("JUNCTION_"):
                self._log_issue(1, "Missing Junction Name", iid, iid, "WARNING",
                                "Junction name derived as fallback from PDF filename hash", name,
                                "Verify actual street intersections from original PDF drawing header")

    # Check 2: Duplicate timing plans
    def _check_2_duplicate_timing_plans(self):
        dups = self.df_timings[self.df_timings.duplicated(
            subset=["intersection_id", "plan_name", "start_time", "end_time", "phase_number"],
            keep=False
        )]
        for _, row in dups.iterrows():
            self._log_issue(2, "Duplicate Timing Plan", row["timing_id"], row["intersection_id"], "WARNING",
                            f"Identical timing record exists for phase {row['phase_number']} in plan {row['plan_name']}",
                            f"{row['plan_name']} ({row['start_time']}-{row['end_time']})",
                            "Deduplicate by retaining single schedule instance per phase")

    # Check 3: Missing phase durations
    def _check_3_missing_phase_durations(self):
        missing = self.df_timings[self.df_timings["green_time_sec"].isna()]
        for _, row in missing.iterrows():
            self._log_issue(3, "Missing Phase Duration", row["timing_id"], row["intersection_id"], "ERROR",
                            "Phase green time is NULL or NaN", "NaN",
                            "Flag record; do not invent duration; treat as unavailable")

    # Check 4: Invalid or negative durations
    def _check_4_invalid_or_negative_durations(self):
        invalid = self.df_timings[
            (self.df_timings["green_time_sec"] <= 0) |
            (self.df_timings.get("yellow_time_sec", 0) < 0) |
            (self.df_timings.get("all_red_sec", 0) < 0)
        ]
        for _, row in invalid.iterrows():
            g = row["green_time_sec"]
            self._log_issue(4, "Invalid or Negative Duration", row["timing_id"], row["intersection_id"], "ERROR",
                            f"Non-positive green interval encountered: {g}s", f"green={g}",
                            "Audit original timing sheet; suppress edge delay if invalid")

    # Check 5: Inconsistent cycle lengths (outside 40s - 260s)
    def _check_5_inconsistent_cycle_lengths(self):
        inconsistent = self.df_timings[
            (self.df_timings["cycle_length_sec"] < 40) |
            (self.df_timings["cycle_length_sec"] > 260)
        ]
        for _, row in inconsistent.iterrows():
            c = row["cycle_length_sec"]
            self._log_issue(5, "Inconsistent Cycle Length", row["timing_id"], row["intersection_id"], "WARNING",
                            f"Cycle length {c}s deviates outside standard urban bounds (40s-260s)", f"C={c}s",
                            "Check if cycle was misparsed from wrapped table column; flag for manual review")

    # Check 6: Phase totals exceeding cycle length
    def _check_6_phase_totals_exceeding_cycle(self):
        # Group timings by plan and calculate sum of greens
        grouped = self.df_timings.groupby(["intersection_id", "plan_name", "start_time", "end_time"])
        for (iid, pname, st, et), grp in grouped:
            c_stated = grp["cycle_length_sec"].iloc[0]
            greens_sum = grp["green_time_sec"].sum()
            if greens_sum > c_stated:
                self._log_issue(6, "Phase Totals Exceed Cycle", f"{iid}_{pname}", iid, "ERROR",
                                f"Sum of phase greens ({greens_sum}s) exceeds stated cycle length ({c_stated}s)",
                                f"greens_sum={greens_sum}, cycle={c_stated}",
                                "Flag timing plan for manual audit; preserve source values")

    # Check 7: Missing approach information
    def _check_7_missing_approach_information(self):
        # Intersections without roads
        road_iids = set(self.df_roads["intersection_id"].unique())
        for _, row in self.df_intersections.iterrows():
            iid = row["intersection_id"]
            if iid not in road_iids:
                self._log_issue(7, "Missing Approach Information", iid, iid, "WARNING",
                                "Intersection has zero documented road approaches in roads.csv", "0 approaches",
                                "Infer approaches from connected network edges in roads_gis.json")
        
        # Phases without approach code
        if not self.df_phases.empty:
            missing_app_phases = self.df_phases[self.df_phases["approach_code"].isna()]
            for _, row in missing_app_phases.iterrows():
                self._log_issue(7, "Missing Approach Information", row["phase_id"], row["intersection_id"], "WARNING",
                                "Signal phase has unassigned approach code", "approach_code=NaN",
                                "Map to incoming road approach based on geometric orientation")

    # Check 8: Conflicting timing plans (overlapping TOD intervals)
    def _check_8_conflicting_timing_plans(self):
        # Check weekdays vs sunday separately
        plans = self.df_timings[["intersection_id", "plan_name", "start_time", "end_time"]].drop_duplicates()
        for iid, grp in plans.groupby("intersection_id"):
            weekday_plans = grp[~grp["plan_name"].str.contains("SUNDAY", case=False, na=False)].sort_values(by="start_time")
            prev_end = None
            prev_plan = None
            for _, p in weekday_plans.iterrows():
                curr_st = p["start_time"]
                curr_et = p["end_time"]
                if prev_end and curr_st < prev_end and curr_st != "00:00":
                    self._log_issue(8, "Conflicting Timing Plans", f"{iid}_{p['plan_name']}", iid, "INFO",
                                    f"Overlapping time intervals between {prev_plan} and {p['plan_name']}",
                                    f"prev_end={prev_end}, curr_start={curr_st}",
                                    "Verify transition schedule; select dominant peak plan")
                prev_end = curr_et
                prev_plan = p["plan_name"]

    # Check 9: Incorrect time-of-day intervals
    def _check_9_incorrect_tod_intervals(self):
        for _, row in self.df_timings[["intersection_id", "timing_id", "start_time", "end_time"]].drop_duplicates().iterrows():
            st = str(row["start_time"]).strip()
            et = str(row["end_time"]).strip()
            time_regex = r"^\d{2}:\d{2}$"
            if not (re.match(time_regex, st) and re.match(time_regex, et)):
                self._log_issue(9, "Incorrect TOD Interval", row["timing_id"], row["intersection_id"], "ERROR",
                                f"Non-standard time format '{st}' - '{et}'", f"{st}-{et}",
                                "Standardize time format to HH:MM (24-hour clock)")
            elif st >= et and not (et in ["00:00", "01:00", "02:00"] and st >= "20:00"):
                self._log_issue(9, "Incorrect TOD Interval", row["timing_id"], row["intersection_id"], "WARNING",
                                f"Start time {st} is greater than or equal to end time {et}", f"{st}>={et}",
                                "Review timing line in source PDF for midnight transition or wrapped text")

    # Check 10: Unreadable extraction results
    def _check_10_unreadable_extraction_results(self):
        if not self.df_inventory.empty:
            unreadable = self.df_inventory[
                (self.df_inventory["extraction_status"] != "SUCCESS") |
                (self.df_inventory["num_timing_records"] == 0)
            ]
            for _, row in unreadable.iterrows():
                self._log_issue(10, "Unreadable Extraction Result", row["filename"], "N/A", "ERROR",
                                f"Document extraction status is {row['extraction_status']}; {row['num_timing_records']} records",
                                row["error_notes"],
                                "Apply high-resolution OCR scan or manual transcription")


def run_and_save_signal_validation(
    output_path: str = "data/processed/signal_validation_audit.csv"
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Runs the 10 checks and saves the audit CSV."""
    validator = SignalDataValidator()
    df_audit = validator.run_all_checks()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_audit.to_csv(output_path, index=False)

    summary = {
        "total_issues_flagged": len(df_audit),
        "errors": len(df_audit[df_audit["severity"] == "ERROR"]),
        "warnings": len(df_audit[df_audit["severity"] == "WARNING"]),
        "info": len(df_audit[df_audit["severity"] == "INFO"]),
        "by_check": df_audit["check_name"].value_counts().to_dict() if not df_audit.empty else {}
    }
    return df_audit, summary


if __name__ == "__main__":
    df, summary = run_and_save_signal_validation()
    print(f"Signal validation audit completed. Total issues flagged: {summary['total_issues_flagged']}")
    print(f"Errors: {summary['errors']}, Warnings: {summary['warnings']}, Info: {summary['info']}")
    print("Issues by check:\n", summary["by_check"])
