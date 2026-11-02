import unittest
from pathlib import Path
from app.compressors.manager import CompressionManager

BASE_DIR = Path(__file__).resolve().parent.parent
SAMPLE_DIR = BASE_DIR / "sample_files"
OUTPUT_DIR = BASE_DIR / "storage" / "test_outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class TestCompressor(unittest.TestCase):
    def setUp(self):
        self.manager = CompressionManager()

    def test_lossless_pdf_compression(self):
        sample_pdf = SAMPLE_DIR / "sample_presentation.pdf"
        out_pdf = OUTPUT_DIR / "sample_lossless_compressed.pdf"
        if out_pdf.exists():
            out_pdf.unlink()

        result = self.manager.compress_pdf(sample_pdf, out_pdf, mode="lossless")
        self.assertTrue(result.success)
        self.assertTrue(out_pdf.exists())
        self.assertLessEqual(result.compressed_size, result.original_size)
        print(f"\n[Test Lossless] Orig: {result.original_size}B -> Comp: {result.compressed_size}B (Saved: {result.saved_percent}%) Engine: {result.engine_used}")

    def test_smart_lossless_pdf_compression(self):
        sample_pdf = SAMPLE_DIR / "sample_presentation.pdf"
        out_pdf = OUTPUT_DIR / "sample_smart_compressed.pdf"
        if out_pdf.exists():
            out_pdf.unlink()

        result = self.manager.compress_pdf(sample_pdf, out_pdf, mode="smart_lossless")
        self.assertTrue(result.success)
        self.assertTrue(out_pdf.exists())
        self.assertLessEqual(result.compressed_size, result.original_size)
        print(f"\n[Test Smart] Orig: {result.original_size}B -> Comp: {result.compressed_size}B (Saved: {result.saved_percent}%) Engine: {result.engine_used}")

    def test_high_compression(self):
        sample_pdf = SAMPLE_DIR / "sample_presentation.pdf"
        out_pdf = OUTPUT_DIR / "sample_high_compressed.pdf"
        if out_pdf.exists():
            out_pdf.unlink()

        result = self.manager.compress_pdf(sample_pdf, out_pdf, mode="high")
        self.assertTrue(result.success)
        self.assertTrue(out_pdf.exists())
        self.assertLessEqual(result.compressed_size, result.original_size)
        print(f"\n[Test High] Orig: {result.original_size}B -> Comp: {result.compressed_size}B (Saved: {result.saved_percent}%) Engine: {result.engine_used}")


if __name__ == "__main__":
    unittest.main()
