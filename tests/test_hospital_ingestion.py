"""
Unit Tests for Task 2 & Task 3: Hospital Data Ingestion and Classification.
Ambulance Route Optimization — Bengaluru.
"""

import unittest
import os
import json
import pandas as pd
from src.data_processing.hospital_processor import (
    HospitalDataProcessor,
    extract_representative_point,
    haversine_distance_m,
    BENGALURU_BBOX
)

class TestHospitalIngestion(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.raw_geojson_path = "hospital dataset/export.geojson"
        cls.processor = HospitalDataProcessor(cls.raw_geojson_path)
        cls.df_hospitals = cls.processor.process_and_classify()

    def test_geojson_loading(self):
        """Test 1: Verify raw GeoJSON loads safely and contains all 1,084 records."""
        self.assertTrue(os.path.exists(self.raw_geojson_path))
        features = self.processor.load_raw_geojson()
        self.assertEqual(len(features), 1084)

    def test_geometry_conversion_all_types(self):
        """Test 2: Geometry extraction for Point, Polygon, and MultiPolygon."""
        # Point test
        pt = {"type": "Point", "coordinates": [77.5946, 12.9716]}
        lat, lon, gtype = extract_representative_point(pt)
        self.assertAlmostEqual(lat, 12.9716)
        self.assertAlmostEqual(lon, 77.5946)
        self.assertEqual(gtype, "Point")

        # Polygon centroid test
        poly = {
            "type": "Polygon",
            "coordinates": [[[77.5, 12.9], [77.6, 12.9], [77.6, 13.0], [77.5, 13.0], [77.5, 12.9]]]
        }
        plat, plon, pgtype = extract_representative_point(poly)
        self.assertIsNotNone(plat)
        self.assertIsNotNone(plon)
        self.assertEqual(pgtype, "PolygonCentroid")

        # Empty / invalid geometry test
        ilat, ilon, igtype = extract_representative_point(None)
        self.assertIsNone(ilat)
        self.assertIsNone(ilon)

    def test_invalid_coordinates_detection(self):
        """Test 3: Verify coordinate range validation [-90, 90] and [-180, 180]."""
        valid_coords = self.df_hospitals.dropna(subset=["latitude", "longitude"])
        for _, row in valid_coords.iterrows():
            lat, lon = row["latitude"], row["longitude"]
            self.assertTrue(-90.0 <= lat <= 90.0, f"Latitude {lat} out of range")
            self.assertTrue(-180.0 <= lon <= 180.0, f"Longitude {lon} out of range")

    def test_missing_hospital_names_detection(self):
        """Test 4: Missing names are flagged as incomplete and never invented."""
        missing_names = self.df_hospitals[self.df_hospitals["data_quality_issue"] == "MISSING_NAME"]
        self.assertEqual(len(missing_names), 16)
        for _, row in missing_names.iterrows():
            self.assertEqual(row["verification_status"], "INCOMPLETE_OR_QUESTIONABLE")
            self.assertIn("Unnamed Facility", row["hospital_name"])

    def test_duplicate_hospital_records_detection(self):
        """Test 5: Proximity duplicate detection within 300m."""
        duplicates = self.df_hospitals[self.df_hospitals["is_duplicate"]]
        self.assertGreater(len(duplicates), 0)
        self.assertEqual(len(duplicates), 19)
        for _, row in duplicates.iterrows():
            self.assertEqual(row["verification_status"], "DUPLICATE_ENTRY")

    def test_bengaluru_boundary_validation(self):
        """Test 6: Check all hospital features are checked against Greater Bengaluru BBOX."""
        valid_records = self.df_hospitals[self.df_hospitals["data_quality_issue"] != "OUTSIDE_BENGALURU_BBOX"]
        for _, row in valid_records.iterrows():
            if pd.notna(row["latitude"]) and pd.notna(row["longitude"]):
                self.assertTrue(BENGALURU_BBOX["min_lat"] <= row["latitude"] <= BENGALURU_BBOX["max_lat"])
                self.assertTrue(BENGALURU_BBOX["min_lon"] <= row["longitude"] <= BENGALURU_BBOX["max_lon"])

    def test_evidence_based_classification(self):
        """Test 7: Verify strict classification without assuming OSM hospital = emergency."""
        statuses = set(self.df_hospitals["verification_status"].unique())
        expected_statuses = {
            "VERIFIED_EMERGENCY",
            "EMERGENCY_PROBABLE_UNVERIFIED",
            "HOSPITAL_EMERGENCY_UNVERIFIED",
            "GENERAL_HEALTHCARE",
            "DUPLICATE_ENTRY",
            "INCOMPLETE_OR_QUESTIONABLE"
        }
        self.assertTrue(statuses.issubset(expected_statuses))

        # Verified emergency count
        verified_count = len(self.df_hospitals[self.df_hospitals["verification_status"] == "VERIFIED_EMERGENCY"])
        self.assertEqual(verified_count, 103)

    def test_cleaned_dataset_exports(self):
        """Test 8: Output files exist and are valid."""
        csv_path = "data/processed/bengaluru_hospitals.csv"
        geojson_path = "data/processed/bengaluru_hospitals_cleaned.geojson"
        report_path = "data/processed/hospital_data_quality_report.csv"

        self.assertTrue(os.path.exists(csv_path))
        self.assertTrue(os.path.exists(geojson_path))
        self.assertTrue(os.path.exists(report_path))

        df_check = pd.read_csv(csv_path)
        self.assertEqual(len(df_check), 1084)
        self.assertIn("hospital_id", df_check.columns)
        self.assertIn("verification_status", df_check.columns)

if __name__ == "__main__":
    unittest.main()
