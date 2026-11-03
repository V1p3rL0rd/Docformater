from pathlib import Path
from typing import Dict, Any

from app.converters.base import ConversionError, ConversionResult
from app.converters.pdf_to_docx import PdfToDocxConverter, HAS_PDF2DOCX
from app.converters.pdf_to_excel import PdfToExcelConverter, HAS_PDFPLUMBER


class ReverseConversionManager:
    """Orchestrates reverse conversion from PDF to Word (.docx) and Excel (.xlsx)."""

    def __init__(self):
        self.docx_converter = PdfToDocxConverter()
        self.excel_converter = PdfToExcelConverter()

    def get_status(self) -> Dict[str, Any]:
        return {
            "pdf_to_docx_available": True,
            "pdf_to_docx_engine": "pdf2docx (PyMuPDF)" if HAS_PDF2DOCX else "python-docx fallback",
            "pdf_to_excel_available": self.excel_converter.is_available,
            "pdf_to_excel_engine": "pdfplumber + openpyxl" if HAS_PDFPLUMBER else "pypdf + openpyxl",
            "supported_reverse_formats": ["docx", "xlsx"],
        }

    def convert_from_pdf(self, input_pdf: Path, output_file: Path, target_format: str) -> ConversionResult:
        if not input_pdf.exists():
            raise ConversionError(f"PDF file not found: {input_pdf}")

        if input_pdf.suffix.lower() != ".pdf":
            raise ConversionError(f"Input file must be a PDF, got: {input_pdf.suffix}")

        target_format = (target_format or "docx").lower().lstrip(".")

        if target_format == "docx":
            return self.docx_converter.convert(input_pdf, output_file)
        elif target_format in ("xlsx", "xls"):
            return self.excel_converter.convert(input_pdf, output_file)
        else:
            raise ConversionError(f"Unsupported target format: {target_format}. Allowed: 'docx', 'xlsx'")
