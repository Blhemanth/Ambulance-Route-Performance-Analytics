import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.data_processing.data_cleaner import clean_cad_string, dedup_token, parse_time_window

class TestDataCleaner(unittest.TestCase):
    def test_dedup_token(self):
        self.assertEqual(dedup_token("BBAANNGGAALLOORREE"), "BANGALORE")
        self.assertEqual(dedup_token("TTIIMMIINNGGSS"), "TIMINGS")
        self.assertEqual(dedup_token("DDAATTAA"), "DATA")
        self.assertEqual(dedup_token("UUCCOOBBAANNKK"), "UCOBANK")
        self.assertEqual(dedup_token("9900((7700))"), "90(70)")

    def test_clean_cad_string(self):
        raw = "BBAANNGGAALLOORREE UNIVERSITY"
        self.assertEqual(clean_cad_string(raw), "BANGALORE UNIVERSITY")

        raw_rev = "NAIRTSEDEP EVISULCXE"
        self.assertEqual(clean_cad_string(raw_rev), "EXCLUSIVE PEDESTRIAN")

        raw_mixed = "ROAD FROM NAIRTSEDEP EVISULCXE"
        self.assertIn("EXCLUSIVE PEDESTRIAN", clean_cad_string(raw_mixed))

    def test_parse_time_window(self):
        t1, t2 = parse_time_window("07:00 09:00")
        self.assertEqual(t1, "07:00")
        self.assertEqual(t2, "09:00")

        t1, t2 = parse_time_window("08:30 - 11:30")
        self.assertEqual(t1, "08:30")
        self.assertEqual(t2, "11:30")

if __name__ == '__main__':
    unittest.main()
