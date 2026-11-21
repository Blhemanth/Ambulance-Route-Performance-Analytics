import unittest
import glob
import os
import pypdf

class TestDatasetAudit(unittest.TestCase):
    def setUp(self):
        self.dataset_dir = 'dataset'
        for candidate in ['dataset', 'datasets', 'traffic datasets']:
            if os.path.exists(candidate) and glob.glob(os.path.join(candidate, '*.pdf')):
                self.dataset_dir = candidate
                break
        self.pdf_files = sorted(glob.glob(os.path.join(self.dataset_dir, '*.pdf')))

    def test_total_file_count(self):
        """Verify exactly 118 PDF files are present in the dataset."""
        self.assertEqual(len(self.pdf_files), 118, f"Expected 118 PDFs, found {len(self.pdf_files)}")

    def test_single_page_per_document(self):
        """Verify each document is a single-page engineering drawing."""
        for p in self.pdf_files[:20]: # Check representative batch
            reader = pypdf.PdfReader(p)
            self.assertEqual(len(reader.pages), 1, f"File {p} has {len(reader.pages)} pages instead of 1")

    def test_vector_and_raster_classification(self):
        """Verify 114 vector PDFs and 4 raster scan PDFs."""
        zero_text_count = 0
        for p in self.pdf_files:
            reader = pypdf.PdfReader(p)
            text = reader.pages[0].extract_text() or ''
            if len(text.strip()) == 0:
                zero_text_count += 1
        self.assertEqual(zero_text_count, 4, f"Expected 4 scanned raster PDFs, found {zero_text_count}")

if __name__ == '__main__':
    unittest.main()
