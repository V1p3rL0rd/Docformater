import unittest
from pathlib import Path
from fastapi.testclient import TestClient

from app.converters.reverse_manager import ReverseConversionManager
from app.main import app

BASE_DIR = Path(__file__).resolve().parent.parent
SAMPLE_DIR = BASE_DIR / "sample_files"
OUTPUT_DIR = BASE_DIR / "storage" / "test_outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class TestReverseConversion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manager = ReverseConversionManager()
        cls.client = TestClient(app)
        cls.sample_pdf = SAMPLE_DIR / "sample_presentation.pdf"

    def test_pdf_to_docx_direct(self):
        out_docx = OUTPUT_DIR / "test_out.docx"
        if out_docx.exists():
            out_docx.unlink()

        result = self.manager.convert_from_pdf(self.sample_pdf, out_docx, target_format="docx")
        self.assertTrue(result.success)
        self.assertTrue(out_docx.exists())
        self.assertGreater(out_docx.stat().st_size, 0)
        print(f"\n[Test PDF->DOCX] Size: {result.converted_size}B using {result.engine_used}")

    def test_pdf_to_xlsx_direct(self):
        out_xlsx = OUTPUT_DIR / "test_out.xlsx"
        if out_xlsx.exists():
            out_xlsx.unlink()

        result = self.manager.convert_from_pdf(self.sample_pdf, out_xlsx, target_format="xlsx")
        self.assertTrue(result.success)
        self.assertTrue(out_xlsx.exists())
        self.assertGreater(out_xlsx.stat().st_size, 0)
        print(f"\n[Test PDF->XLSX] Size: {result.converted_size}B using {result.engine_used}")

    def test_api_pdf_to_docx(self):
        with open(self.sample_pdf, "rb") as f:
            response = self.client.post(
                "/api/convert-from-pdf",
                files={"file": ("sample.pdf", f, "application/pdf")},
                data={"target_format": "docx"},
            )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["target_format"], "docx")
        self.assertIn("download_url", data)

        # Check file download
        dl_resp = self.client.get(data["download_url"])
        self.assertEqual(dl_resp.status_code, 200)
        self.assertGreater(len(dl_resp.content), 0)

    def test_api_pdf_to_xlsx(self):
        with open(self.sample_pdf, "rb") as f:
            response = self.client.post(
                "/api/convert-from-pdf",
                files={"file": ("sample.pdf", f, "application/pdf")},
                data={"target_format": "xlsx"},
            )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["target_format"], "xlsx")
        self.assertIn("download_url", data)

        # Check file download
        dl_resp = self.client.get(data["download_url"])
        self.assertEqual(dl_resp.status_code, 200)
        self.assertGreater(len(dl_resp.content), 0)


if __name__ == "__main__":
    unittest.main()
