import unittest
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

BASE_DIR = Path(__file__).resolve().parent.parent
SAMPLE_DIR = BASE_DIR / "sample_files"


class TestApiEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_status_endpoint(self):
        response = self.client.get("/api/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "online")
        self.assertIn("converter", data)
        self.assertIn("compressor", data)

    def test_convert_docx_api(self):
        file_path = SAMPLE_DIR / "sample_contract.docx"
        with open(file_path, "rb") as f:
            response = self.client.post(
                "/api/convert",
                files={"file": ("sample_contract.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("download_url", data)

        # Test download
        dl_resp = self.client.get(data["download_url"])
        self.assertEqual(dl_resp.status_code, 200)
        self.assertGreater(len(dl_resp.content), 0)

    def test_convert_xlsx_api(self):
        file_path = SAMPLE_DIR / "sample_financial_report.xlsx"
        with open(file_path, "rb") as f:
            response = self.client.post(
                "/api/convert",
                files={"file": ("sample_financial_report.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])

    def test_compress_pdf_api(self):
        file_path = SAMPLE_DIR / "sample_presentation.pdf"
        with open(file_path, "rb") as f:
            response = self.client.post(
                "/api/compress",
                files={"file": ("sample_presentation.pdf", f, "application/pdf")},
                data={"mode": "lossless"}
            )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["mode"], "lossless")
        self.assertIn("download_url", data)

    def test_convert_and_compress_api(self):
        file_path = SAMPLE_DIR / "sample_contract.docx"
        with open(file_path, "rb") as f:
            response = self.client.post(
                "/api/convert-and-compress",
                files={"file": ("sample_contract.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                data={"mode": "lossless"}
            )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("final_size", data)


if __name__ == "__main__":
    unittest.main()
