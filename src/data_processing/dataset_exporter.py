"""
Dataset Exporter Module for Bengaluru Traffic Signal Dataset.
Orchestrates PDF extraction, applies mathematical validation, and exports
structured relational CSV files to data/processed/.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import os
import json
import pandas as pd
from typing import Dict, Any

from src.data_processing.pdf_extractor import PDFExtractor
from src.data_processing.data_validator import DataValidator

class DatasetExporter:
    def __init__(self, output_dir: str = "data/processed", reports_dir: str = "reports"):
        self.output_dir = output_dir
        self.reports_dir = reports_dir
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
        self.extractor = PDFExtractor()
        self.validator = DataValidator()

    def run_pipeline(self) -> Dict[str, Any]:
        """Executes full PDF extraction, validation, and CSV export."""
        print("="*70)
        print("STARTING BENGALURU TRAFFIC SIGNAL DATASET EXTRACTION PIPELINE")
        print("="*70)

        # 1. Extract data from all PDFs
        raw_dataset = self.extractor.extract_all()
        intersections = raw_dataset["intersections"]
        roads = raw_dataset["roads"]
        phases = raw_dataset["signal_phases"]
        timings = raw_dataset["signal_timings"]
        errors = raw_dataset["extraction_errors"]

        print(f"Extraction Completed:")
        print(f"  Intersections extracted: {len(intersections)}")
        print(f"  Road approaches extracted: {len(roads)}")
        print(f"  Signal phases extracted: {len(phases)}")
        print(f"  Timing records extracted: {len(timings)}")
        print(f"  Extraction anomalies logged: {len(errors)}")

        # 2. Validate extracted relational data
        validation_results = self.validator.validate_dataset(raw_dataset)
        print("\nValidation Summary:")
        for k, v in validation_results.items():
            print(f"  {k}: {v}")

        # 3. Convert to DataFrames and Export CSVs
        df_intersections = pd.DataFrame(intersections)
        df_roads = pd.DataFrame(roads)
        df_phases = pd.DataFrame(phases)
        df_timings = pd.DataFrame(timings)
        df_errors = pd.DataFrame(errors)

        paths = {
            "intersections": os.path.join(self.output_dir, "intersections.csv"),
            "roads": os.path.join(self.output_dir, "roads.csv"),
            "signal_phases": os.path.join(self.output_dir, "signal_phases.csv"),
            "signal_timings": os.path.join(self.output_dir, "signal_timings.csv"),
            "extraction_errors": os.path.join(self.output_dir, "extraction_errors.csv"),
        }

        df_intersections.to_csv(paths["intersections"], index=False)
        df_roads.to_csv(paths["roads"], index=False)
        df_phases.to_csv(paths["signal_phases"], index=False)
        df_timings.to_csv(paths["signal_timings"], index=False)
        df_errors.to_csv(paths["extraction_errors"], index=False)

        print("\nRelational Datasets Exported Successfully to data/processed/:")
        for name, p in paths.items():
            file_size = os.path.getsize(p)
            print(f"  {os.path.basename(p)} ({file_size} bytes)")

        # Save summary report
        report_path = os.path.join(self.reports_dir, "extraction_summary.json")
        summary_payload = {
            "pipeline_status": "SUCCESS" if validation_results["is_valid"] else "COMPLETED_WITH_WARNINGS",
            "file_counts": {k: len(v) for k, v in raw_dataset.items()},
            "validation_results": validation_results,
            "exported_files": paths
        }
        with open(report_path, "w") as f:
            json.dump(summary_payload, f, indent=2)
        print(f"\nExecution Report saved to {report_path}")

        return summary_payload

if __name__ == "__main__":
    exporter = DatasetExporter()
    exporter.run_pipeline()
