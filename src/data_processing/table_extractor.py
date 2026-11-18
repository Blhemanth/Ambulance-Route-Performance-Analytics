"""
Table & Schedule Extractor Module for Bengaluru Traffic Signal PDF Documents.
Extracts approach names, movement codes, time-of-day plans, phase green allocations,
pedestrian clearance intervals, and stated cycle lengths using hybrid table grid
and vector stream analysis.
"""

import re
from typing import Dict, List, Any, Optional
from src.data_processing.data_cleaner import clean_cad_string, dedup_token

class TableExtractor:
    def __init__(self):
        pass

    def parse_table_and_text(
        self,
        table_data: List[List[Optional[str]]],
        page_text: str,
        section: str = "UPPER",
        default_cross_road: str = ""
    ) -> Dict[str, Any]:
        """
        Parses intersection approaches, permitted movements, and timing schedules.
        Combines spatial table grids with vector text line parsing.
        """
        cross_road = default_cross_road
        approaches = self._extract_approaches(table_data)
        
        # Determine num_phases based on approaches or fallback
        num_phases = len(approaches) if approaches else 3

        # Parse timings from both page text and table rows
        timings = self._parse_timings(page_text, table_data, section, num_phases)

        return {
            "cross_road": cross_road,
            "num_phases": num_phases,
            "approaches": approaches,
            "timings": timings,
        }

    def _extract_approaches(self, table_data: List[List[Optional[str]]]) -> List[Dict[str, Any]]:
        """Extracts approach codes, road names, and movement codes."""
        if not table_data:
            return []

        approaches = []
        for row in table_data[:8]:
            clean_row = [clean_cad_string(c) if c else "" for c in row]
            
            # Skip rows containing headers or timings
            row_str = " ".join([c for c in clean_row if c])
            if any(term in row_str for term in ["TIMINGS", "PHASE", "CYCLE TIME", "ROAD FROM"]):
                continue
            if re.search(r"\d{2}:\d{2}", row_str):
                continue

            app_code = None
            app_name = None
            movements = []

            # Check individual cells
            for c_idx, cell in enumerate(clean_row):
                # Matches isolated letter "A" to "E"
                if re.match(r"^[A-E]$", cell):
                    app_code = cell
                    # Search adjacent cells for road name
                    for next_cell in clean_row[c_idx+1:c_idx+4]:
                        clean_cand = next_cell.strip()
                        if len(clean_cand) > 2 and not re.match(r"^[RLSP\s,]+$", clean_cand) and clean_cand not in ["TIMINGS", "DATA", "ROAD", "FROM"]:
                            app_name = clean_cand
                            break
                    break
                # Matches merged letter e.g. "A BANGALORE UNIVERSITY"
                m = re.match(r"^([A-E])\s+([A-Z0-9\.\s/&'-]+)$", cell)
                if m:
                    app_code = m.group(1)
                    app_name = m.group(2).strip()
                    break

            if app_code:
                # Extract movement symbols (R, L, S, P)
                for cell in clean_row:
                    if re.match(r"^[RLSP\s]+$", cell) and cell.strip() and cell not in ["A", "B", "C", "D", "E"]:
                        movements.append(cell.strip())

                # If name not found yet, pick longest descriptive cell
                if not app_name:
                    for cell in clean_row:
                        if len(cell) > 3 and not re.match(r"^[RLSP\s,]+$", cell) and cell not in ["TIMINGS", "DATA", "ROAD", "FROM"]:
                            app_name = cell.strip()
                            break

                if app_name:
                    app_name = re.sub(r"\b(DATA|ROAD|FROM|TIMINGS)\b", "", app_name).strip()
                    approaches.append({
                        "approach_code": app_code,
                        "road_name": app_name,
                        "movements": movements,
                        "lanes": self._estimate_lanes(app_name)
                    })

        return approaches

    def _estimate_lanes(self, road_name: str) -> int:
        """Estimate lane count based on road terminology."""
        name_upper = road_name.upper()
        if any(term in name_upper for term in ["RING ROAD", "ORR", "HIGHWAY", "EXPRESSWAY", "MYSORE ROAD", "HOSUR ROAD"]):
            return 3
        elif any(term in name_upper for term in ["MAIN ROAD", "DOUBLE ROAD", "100 FT", "80 FT", "AVENUE", "BOULEVARD"]):
            return 2
        return 2

    def _parse_timings(
        self,
        page_text: str,
        table_data: List[List[Optional[str]]],
        section: str,
        num_phases: int
    ) -> List[Dict[str, Any]]:
        """Parses schedule timing rows from text stream corresponding to the section."""
        timing_records = []
        all_timing_lines = []

        for line in page_text.splitlines():
            cleaned = clean_cad_string(line)
            if re.search(r"\b\d{2}:\d{2}\b", cleaned):
                all_timing_lines.append(cleaned)

        # In 2-junction PDFs, timing lines for Junction 1 are typically in the first half,
        # and Junction 2 in the second half.
        target_lines = all_timing_lines
        if len(all_timing_lines) >= 8:
            mid = len(all_timing_lines) // 2
            if section == "UPPER":
                target_lines = all_timing_lines[:mid]
            else:
                target_lines = all_timing_lines[mid:]

        for line in target_lines:
            m_time = list(re.finditer(r"\b\d{2}:\d{2}\b", line))
            if len(m_time) >= 2:
                t1 = m_time[0].group(0)
                t2 = m_time[1].group(0)
                after = line[m_time[1].end():]
                tokens = re.findall(r"\d+(?:\(\d+\))?", after)

                w_vals = []
                s_vals = []
                for tok in tokens:
                    m = re.match(r"^(\d+)(?:\((\d+)\))?", tok)
                    if m:
                        w_vals.append(int(m.group(1)))
                        s_vals.append(int(m.group(2)) if m.group(2) else int(m.group(1)))

                if len(w_vals) >= 3:
                    w_cycle = w_vals[-1]
                    w_greens = w_vals[:-1]
                    w_sum = sum(w_greens)

                    # If cycle time was missing, zero, or unstated, derive it from phase greens sum
                    if w_cycle <= 0:
                        w_cycle = w_sum

                    plan_name = self._classify_plan_name(t1, line)
                    diff = w_cycle - w_sum

                    val_status = "VALID"
                    lost_time = 0
                    if diff == 0:
                        val_status = "VALID"
                        lost_time = 0
                    elif 0 < diff <= 20:
                        val_status = "VALID_WITH_AMBER_CLEARANCE"
                        lost_time = diff
                    else:
                        val_status = f"FLAGGED_DISCREPANCY_DELTA_{diff}"

                    # Phase mapping
                    phase_greens = {p_idx: g for p_idx, g in enumerate(w_greens, start=1)}

                    timing_records.append({
                        "plan_name": plan_name,
                        "start_time": t1,
                        "end_time": t2,
                        "phase_greens": phase_greens,
                        "cycle_time": w_cycle,
                        "greens_sum": w_sum,
                        "lost_time": lost_time,
                        "validation_status": val_status
                    })

                    # If Sunday plan has distinct numbers, append Sunday plan record
                    if s_vals != w_vals and len(s_vals) >= 3:
                        s_cycle = s_vals[-1]
                        s_greens = s_vals[:-1]
                        s_sum = sum(s_greens)
                        if s_cycle <= 0:
                            s_cycle = s_sum
                        s_diff = s_cycle - s_sum
                        s_status = "VALID" if s_diff == 0 else ("VALID_WITH_AMBER_CLEARANCE" if 0 < s_diff <= 20 else f"FLAGGED_DISCREPANCY_DELTA_{s_diff}")
                        s_phase_greens = {p_idx: g for p_idx, g in enumerate(s_greens, start=1)}
                        timing_records.append({
                            "plan_name": "SUNDAY_PLAN",
                            "start_time": t1,
                            "end_time": t2,
                            "phase_greens": s_phase_greens,
                            "cycle_time": s_cycle,
                            "greens_sum": s_sum,
                            "lost_time": max(0, s_diff),
                            "validation_status": s_status
                        })

        return timing_records

    def _classify_plan_name(self, start_time: str, line: str) -> str:
        """Classify TOD plan name."""
        if "SUNDAY" in line.upper():
            return "SUNDAY_PLAN"
        h = int(start_time.split(":")[0])
        if h < 8:
            return "WEEKDAY_EARLY_OFFPEAK"
        elif 8 <= h < 11:
            return "WEEKDAY_MORNING_PEAK"
        elif 11 <= h < 16:
            return "WEEKDAY_INTER_PEAK"
        elif 16 <= h < 20:
            return "WEEKDAY_EVENING_PEAK"
        else:
            return "WEEKDAY_NIGHT_OFFPEAK"
