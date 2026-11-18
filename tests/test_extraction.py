import unittest
import os
import pandas as pd

class TestDatasetExtraction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.processed_dir = "data/processed"
        cls.int_path = os.path.join(cls.processed_dir, "intersections.csv")
        cls.roads_path = os.path.join(cls.processed_dir, "roads.csv")
        cls.phases_path = os.path.join(cls.processed_dir, "signal_phases.csv")
        cls.timings_path = os.path.join(cls.processed_dir, "signal_timings.csv")
        cls.errors_path = os.path.join(cls.processed_dir, "extraction_errors.csv")

    def test_csv_files_exist(self):
        self.assertTrue(os.path.exists(self.int_path), "intersections.csv missing")
        self.assertTrue(os.path.exists(self.roads_path), "roads.csv missing")
        self.assertTrue(os.path.exists(self.phases_path), "signal_phases.csv missing")
        self.assertTrue(os.path.exists(self.timings_path), "signal_timings.csv missing")
        self.assertTrue(os.path.exists(self.errors_path), "extraction_errors.csv missing")

    def test_intersections_integrity(self):
        df = pd.read_csv(self.int_path)
        self.assertGreaterEqual(len(df), 118, "Should have at least 118 intersections extracted")
        self.assertEqual(df["intersection_id"].nunique(), len(df), "Intersection IDs must be unique")
        self.assertTrue(df["name"].notnull().all(), "Intersection names must not be null")
        self.assertTrue(df["police_station"].notnull().all(), "Police station must not be null")
        # Coordinate bounds for Bengaluru
        self.assertTrue((df["latitude"] >= 12.70).all() and (df["latitude"] <= 13.30).all())
        self.assertTrue((df["longitude"] >= 77.30).all() and (df["longitude"] <= 77.90).all())

    def test_referential_integrity(self):
        df_int = pd.read_csv(self.int_path)
        valid_int_ids = set(df_int["intersection_id"])

        df_roads = pd.read_csv(self.roads_path)
        self.assertTrue(set(df_roads["intersection_id"]).issubset(valid_int_ids), "Orphaned road detected")

        df_phases = pd.read_csv(self.phases_path)
        self.assertTrue(set(df_phases["intersection_id"]).issubset(valid_int_ids), "Orphaned phase detected")

        df_timings = pd.read_csv(self.timings_path)
        self.assertTrue(set(df_timings["intersection_id"]).issubset(valid_int_ids), "Orphaned timing record detected")

    def test_timing_records_consistency(self):
        df_timings = pd.read_csv(self.timings_path)
        self.assertGreater(len(df_timings), 1000, "Should have thousands of timing records")
        # Green time positive
        self.assertTrue((df_timings["green_time_sec"] >= 0).all(), "Green time must be non-negative")
        self.assertTrue((df_timings["cycle_length_sec"] > 0).all(), "Cycle time must be positive")

if __name__ == "__main__":
    unittest.main()
