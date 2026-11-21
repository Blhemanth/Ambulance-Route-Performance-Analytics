import unittest
from src.optimization.signal_optimizer import SignalOptimizer

class TestSignalOptimizer(unittest.TestCase):
    def setUp(self):
        self.optimizer = SignalOptimizer()

    def test_cycle_conservation_and_optimality(self):
        # 3 vehicular phases + 1 pedestrian phase
        # Cycle time = 120s
        phases = [
            {"phase_number": 1, "lanes": 2, "is_pedestrian_phase": False},
            {"phase_number": 2, "lanes": 2, "is_pedestrian_phase": False},
            {"phase_number": 3, "lanes": 2, "is_pedestrian_phase": False},
            {"phase_number": 4, "lanes": 1, "is_pedestrian_phase": True},
        ]
        demands = {1: 700.0, 2: 500.0, 3: 400.0}

        res = self.optimizer.optimize_intersection_timings(
            intersection_name="Test_Junction",
            cycle_time=120,
            phases=phases,
            demands_pcu_hr=demands,
            lost_time_per_phase=4.0,
            min_veh_green=10.0,
            ped_min_green=10.0
        )

        self.assertTrue(res["is_optimal"], "LP solver should find an optimal solution")
        greens = res["optimized_phase_greens"]

        # Check that phase 1 gets at least as much green as phase 2 and 3 because demand is higher
        self.assertGreaterEqual(greens[1], greens[3])

        # Check total cycle conservation: sum(greens) + lost_time + ped_green == cycle_time
        veh_greens_sum = greens[1] + greens[2] + greens[3]
        total_cycle_calc = veh_greens_sum + res["total_lost_time"] + res["pedestrian_green"]
        self.assertAlmostEqual(total_cycle_calc, 120.0, places=1)

    def test_minimum_green_bounds(self):
        phases = [
            {"phase_number": 1, "lanes": 2, "is_pedestrian_phase": False},
            {"phase_number": 2, "lanes": 2, "is_pedestrian_phase": False},
        ]
        demands = {1: 1000.0, 2: 50.0} # Heavily skewed demand

        res = self.optimizer.optimize_intersection_timings(
            intersection_name="Skewed_Junction",
            cycle_time=100,
            phases=phases,
            demands_pcu_hr=demands,
            lost_time_per_phase=4.0,
            min_veh_green=10.0
        )

        self.assertTrue(res["is_optimal"])
        greens = res["optimized_phase_greens"]
        # Even with low demand, phase 2 must receive at least min_veh_green (10.0s)
        self.assertGreaterEqual(greens[2], 10.0 - 1e-4)

if __name__ == "__main__":
    unittest.main()
