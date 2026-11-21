import unittest
from src.network.network_integrator import NetworkIntegrator
from src.optimization.sensitivity_analysis import SensitivityAnalyzer

class TestModelIntegration(unittest.TestCase):
    def setUp(self):
        self.integrator = NetworkIntegrator()
        self.analyzer = SensitivityAnalyzer()

    def test_full_integration_pipeline(self):
        res = self.integrator.run_integrated_pipeline(
            corridor_filter="Corridor 1: South-Central (Adugodi - Koramangala - Wilson Garden - Dairy Circle)"
        )
        self.assertEqual(res["status"], "SUCCESS")
        comp = res["comparison_matrix"]

        # Check that throughput is non-negative
        self.assertGreaterEqual(comp["max_flow_throughput_pcu_hr"]["baseline"], 0.0)
        self.assertGreaterEqual(comp["max_flow_throughput_pcu_hr"]["optimized"], 0.0)

        # Check queue reduction
        self.assertLessEqual(comp["total_system_residual_queue_veh"]["optimized"],
                             comp["total_system_residual_queue_veh"]["baseline"] + 1e-4)

    def test_sensitivity_analysis_stress_test(self):
        stress_res = self.analyzer.run_stress_test(multipliers=[1.0, 1.10, 1.20])
        df_summary = stress_res["summary_dataframe"]
        self.assertEqual(len(df_summary), 3)
        # Residual queue should increase or stay same with higher demand
        q0 = df_summary.loc[0, "Residual Queue Opt (Veh)"]
        q1 = df_summary.loc[1, "Residual Queue Opt (Veh)"]
        q2 = df_summary.loc[2, "Residual Queue Opt (Veh)"]
        self.assertLessEqual(q0, q1 + 1e-4)
        self.assertLessEqual(q1, q2 + 1e-4)

if __name__ == "__main__":
    unittest.main()
