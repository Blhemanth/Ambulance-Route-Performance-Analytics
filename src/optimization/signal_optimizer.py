"""
Model 4: Traffic Signal Timing Linear Programming Optimizer.
Formulates and solves the Queue-Minimizing Signal Timing Linear Program (LP)
using SciPy HiGHS simplex/interior-point solver, subject to cycle duration conservation,
safety bounds, pedestrian clearance minimums, and approach saturation flow constraints.
"""

import math
import numpy as np
from scipy.optimize import linprog
from typing import Dict, List, Any, Tuple, Optional

class SignalOptimizer:
    def __init__(self):
        pass

    def optimize_intersection_timings(
        self,
        intersection_name: str,
        cycle_time: int,
        phases: List[Dict[str, Any]],
        demands_pcu_hr: Dict[int, float],
        lost_time_per_phase: float = 4.0, # 3s yellow + 1s all-red
        min_veh_green: float = 10.0,
        max_veh_green: float = 120.0,
        ped_min_green: float = 10.0,
        saturation_flow_per_lane: float = 1800.0,
        initial_queues: Optional[Dict[int, float]] = None,
        weights: Optional[Dict[int, float]] = None
    ) -> Dict[str, Any]:
        """
        Solves LP for optimal green splits g_p across phases to minimize residual queues.
        Uses SciPy HiGHS Linear Programming solver.
        """
        # Separate pedestrian phases from vehicular phases
        veh_phases = [p for p in phases if not p.get("is_pedestrian_phase", False)]
        has_ped_phase = any(p.get("is_pedestrian_phase", False) for p in phases)

        if not veh_phases:
            veh_phases = phases

        num_veh = len(veh_phases)
        total_lost_time = num_veh * lost_time_per_phase
        ped_green_allowance = ped_min_green if has_ped_phase else 0.0
        available_green = cycle_time - total_lost_time - ped_green_allowance

        if available_green < num_veh * min_veh_green:
            min_veh_green = max(5.0, available_green / float(num_veh))

        # Problem dimensions: x = [g_1..g_N, Q_1..Q_N, D_1..D_N] (3 * num_veh variables)
        num_vars = 3 * num_veh

        # 1. Objective function c vector: minimize sum(w_p * Q_p) - epsilon * sum(demand_ratio * g_p)
        c = np.zeros(num_vars, dtype=float)
        tot_demand = sum(demands_pcu_hr.get(ph["phase_number"], 1.0) for ph in veh_phases)
        if tot_demand <= 0:
            tot_demand = 1.0

        for i, ph in enumerate(veh_phases):
            p_no = ph["phase_number"]
            w = weights.get(p_no, 1.0) if weights else 1.0
            c[num_veh + i] = w # Q_i coefficient (minimize residual queue)
            # Secondary objective (epsilon): allocate surplus green to higher-demand movements
            demand_ratio = demands_pcu_hr.get(p_no, 100.0) / tot_demand
            c[i] = -1e-4 * demand_ratio

        # 2. Variable Bounds
        bounds = []
        for i, ph in enumerate(veh_phases):
            bounds.append((min_veh_green, max_veh_green)) # g_i
        for i in range(num_veh):
            bounds.append((0.0, None)) # Q_i >= 0
        for i in range(num_veh):
            bounds.append((0.0, None)) # D_i >= 0

        # 3. Equality constraints:
        # Eq 0: sum(g_i) = available_green
        # Eq 1..N: Q_i + D_i = Q_curr + A_i
        A_eq = []
        b_eq = []

        # Cycle conservation
        eq_cycle = np.zeros(num_vars, dtype=float)
        eq_cycle[:num_veh] = 1.0
        A_eq.append(eq_cycle)
        b_eq.append(available_green)

        # Queue balance equations
        if initial_queues is None:
            initial_queues = {ph["phase_number"]: 5.0 for ph in veh_phases}

        for i, ph in enumerate(veh_phases):
            p_no = ph["phase_number"]
            q_p = demands_pcu_hr.get(p_no, 600.0)
            A_p = (q_p * cycle_time) / 3600.0 # Arrivals per cycle
            Q_curr = initial_queues.get(p_no, 5.0)

            eq_q = np.zeros(num_vars, dtype=float)
            eq_q[num_veh + i] = 1.0 # Q_i
            eq_q[2 * num_veh + i] = 1.0 # D_i
            A_eq.append(eq_q)
            b_eq.append(Q_curr + A_p)

        # 4. Inequality constraints:
        # D_i <= (s_i / 3600) * g_i  =>  -(s_i / 3600) * g_i + D_i <= 0
        A_ub = []
        b_ub = []

        for i, ph in enumerate(veh_phases):
            lanes = ph.get("lanes", 2)
            sat_flow = lanes * saturation_flow_per_lane
            sat_rate_per_sec = sat_flow / 3600.0

            ub_row = np.zeros(num_vars, dtype=float)
            ub_row[i] = -sat_rate_per_sec # -sat_rate * g_i
            ub_row[2 * num_veh + i] = 1.0 # + D_i
            A_ub.append(ub_row)
            b_ub.append(0.0)

        # Solve Linear Program using HiGHS
        res = linprog(
            c,
            A_ub=np.array(A_ub),
            b_ub=np.array(b_ub),
            A_eq=np.array(A_eq),
            b_eq=np.array(b_eq),
            bounds=bounds,
            method="highs"
        )

        is_optimal = res.success
        status_str = "Optimal" if is_optimal else res.message

        optimized_greens = {}
        residual_queues = {}
        departures = {}
        capacities_pcu_hr = {}
        degrees_of_sat = {}
        webster_delays_sec = {}

        if is_optimal:
            x_opt = res.x
            for i, ph in enumerate(veh_phases):
                p_no = ph["phase_number"]
                g_val = round(float(x_opt[i]), 1)
                q_val = round(float(x_opt[num_veh + i]), 2)
                d_val = round(float(x_opt[2 * num_veh + i]), 2)

                optimized_greens[p_no] = g_val
                residual_queues[p_no] = q_val
                departures[p_no] = d_val

                # Effective capacity u_eff = (g / C) * sat_flow
                lanes = ph.get("lanes", 2)
                sat_flow = lanes * saturation_flow_per_lane
                u_eff = (g_val / float(cycle_time)) * sat_flow
                capacities_pcu_hr[p_no] = round(u_eff, 1)

                # Saturation degree
                q_p = demands_pcu_hr.get(p_no, 600.0)
                X = (q_p / u_eff) if u_eff > 0 else 1.0
                degrees_of_sat[p_no] = round(X, 3)

                # Webster delay
                webster_delays_sec[p_no] = self._calculate_webster_delay(cycle_time, g_val, q_p, sat_flow)

        if has_ped_phase:
            optimized_greens["PED"] = ped_min_green

        return {
            "status": status_str,
            "is_optimal": is_optimal,
            "intersection_name": intersection_name,
            "cycle_time": cycle_time,
            "total_lost_time": total_lost_time,
            "pedestrian_green": ped_green_allowance,
            "optimized_phase_greens": optimized_greens,
            "residual_queues": residual_queues,
            "cycle_departures": departures,
            "departures": departures,
            "effective_capacities_pcu_hr": capacities_pcu_hr,
            "capacities_pcu_hr": capacities_pcu_hr,
            "degrees_of_saturation": degrees_of_sat,
            "webster_delays_sec": webster_delays_sec,
            "total_residual_queue": sum(residual_queues.values()) if is_optimal else 0.0,
            "average_delay_sec": (sum(webster_delays_sec.values()) / len(webster_delays_sec)) if webster_delays_sec else 0.0
        }

    def _calculate_webster_delay(self, C: float, g: float, q: float, s: float) -> float:
        """Webster's theoretical vehicle delay equation."""
        if C <= 0 or g <= 0 or s <= 0:
            return 30.0

        lam = min(0.95, g / float(C))
        u_eff = lam * s
        q_sec = max(0.01, q / 3600.0)
        X = min(0.95, q / u_eff) if u_eff > 0 else 0.95

        num1 = C * ((1.0 - lam) ** 2)
        den1 = 2.0 * (1.0 - lam * X)
        d1 = num1 / max(0.05, den1)

        num2 = X ** 2
        den2 = 2.0 * q_sec * (1.0 - X)
        d2 = num2 / max(0.01, den2)

        total_delay = 0.9 * (d1 + d2)
        return round(max(5.0, min(total_delay, 180.0)), 1)
