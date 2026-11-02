import unittest
from pathlib import Path
from app.converters.manager import ConversionManager

BASE_DIR = Path(__file__).resolve().parent.parent
SAMPLE_DIR = BASE_DIR / "sample_files"
OUTPUT_DIR = BASE_DIR / "storage" / "test_outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class TestConverters(unittest.TestCase):
    def setUp(self):
        self.manager = ConversionManager()

    def test_docx_to_pdf_conversion(self):
        docx_file = SAMPLE_DIR / "sample_contract.docx"
        out_pdf = OUTPUT_DIR / "output_contract.pdf"
        if out_pdf.exists():
            out_pdf.unlink()

        result = self.manager.convert_to_pdf(docx_file, out_pdf)
        self.assertTrue(result.success)
        self.assertTrue(out_pdf.exists())
        self.assertGreater(out_pdf.stat().st_size, 0)
        print(f"\n[Test DOCX->PDF] Converted {result.original_size}B to {result.converted_size}B using {result.engine_used}")

    def test_excel_to_pdf_conversion(self):
        xlsx_file = SAMPLE_DIR / "sample_financial_report.xlsx"
        out_pdf = OUTPUT_DIR / "output_financial_report.pdf"
        if out_pdf.exists():
            out_pdf.unlink()

        result = self.manager.convert_to_pdf(xlsx_file, out_pdf)
        self.assertTrue(result.success)
        self.assertTrue(out_pdf.exists())
        self.assertGreater(out_pdf.stat().st_size, 0)
        print(f"\n[Test XLSX->PDF] Converted {result.original_size}B to {result.converted_size}B using {result.engine_used}")

    def test_txt_to_pdf_conversion(self):
        txt_file = SAMPLE_DIR / "sample_notes.txt"
        out_pdf = OUTPUT_DIR / "output_notes.pdf"
        if out_pdf.exists():
            out_pdf.unlink()

        result = self.manager.convert_to_pdf(txt_file, out_pdf)
        self.assertTrue(result.success)
        self.assertTrue(out_pdf.exists())
        self.assertGreater(out_pdf.stat().st_size, 0)
        print(f"\n[Test TXT->PDF] Converted {result.original_size}B to {result.converted_size}B using {result.engine_used}")


if __name__ == "__main__":
    unittest.main()
