import time
from pathlib import Path
from typing import Dict, Any

from app.config import SUPPORTED_OFFICE_EXTENSIONS
from app.converters.base import ConversionError, ConversionResult
from app.converters.libreoffice import LibreOfficeConverter, find_libreoffice_binary
from app.converters.docx_converter import NativeDocxConverter
from app.converters.excel_converter import NativeExcelConverter

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


class ConversionManager:
    """Orchestrates document to PDF conversion, picking the best available engine."""

    def __init__(self):
        self.lo_converter = LibreOfficeConverter()
        self.docx_converter = NativeDocxConverter()
        self.excel_converter = NativeExcelConverter()

    def get_status(self) -> Dict[str, Any]:
        """Return status and capabilities of available conversion engines."""
        lo_bin = find_libreoffice_binary()
        return {
            "libreoffice_available": self.lo_converter.is_available,
            "libreoffice_binary": lo_bin,
            "native_docx_available": self.docx_converter.is_available,
            "native_excel_available": self.excel_converter.is_available,
            "supported_extensions": sorted(list(SUPPORTED_OFFICE_EXTENSIONS)),
            "recommended_deployment": "Docker or LibreOffice installed for 100% pixel-perfect formatting."
        }

    def convert_to_pdf(self, input_path: Path, output_path: Path) -> ConversionResult:
        """
        Convert any supported office document to PDF.
        Attempts LibreOffice first for full fidelity; falls back to pure Python if LO not found.
        """
        suffix = input_path.suffix.lower()
        if suffix not in SUPPORTED_OFFICE_EXTENSIONS:
            raise ConversionError(f"Unsupported file format: {suffix}. Supported: {', '.join(sorted(SUPPORTED_OFFICE_EXTENSIONS))}")

        # 1. Prefer LibreOffice if available (handles all formats with 100% native layout)
        if self.lo_converter.is_available:
            try:
                return self.lo_converter.convert(input_path, output_path)
            except Exception as e:
                # If LibreOffice fails and a native fallback exists, try the fallback
                if suffix not in (".docx", ".xlsx", ".csv", ".txt"):
                    raise ConversionError(f"LibreOffice conversion failed: {e}")

        # 2. Native fallbacks when LibreOffice is not installed
        if suffix == ".docx":
            if self.docx_converter.is_available:
                return self.docx_converter.convert(input_path, output_path)
            raise ConversionError("DOCX conversion requires LibreOffice or python-docx+reportlab.")

        elif suffix in (".xlsx", ".csv"):
            if self.excel_converter.is_available:
                return self.excel_converter.convert(input_path, output_path)
            raise ConversionError("Spreadsheet conversion requires LibreOffice or openpyxl+reportlab.")

        elif suffix == ".txt":
            return self._convert_txt_to_pdf(input_path, output_path)

        elif suffix in (".doc", ".xls", ".ppt", ".pptx", ".odt", ".ods", ".odp", ".rtf"):
            raise ConversionError(
                f"Conversion of legacy/complex format '{suffix}' requires LibreOffice on the server. "
                f"Please run the app with Docker or install LibreOffice (`brew install --cask libreoffice` on macOS or `apt install libreoffice` on Linux)."
            )

        raise ConversionError(f"No suitable converter available for {suffix}")

    def _convert_txt_to_pdf(self, input_path: Path, output_path: Path) -> ConversionResult:
        if not HAS_REPORTLAB:
            raise ConversionError("ReportLab is required to convert TXT to PDF.")

        start_time = time.time()
        orig_size = input_path.stat().st_size

        output_path.parent.mkdir(parents=True, exist_ok=True)
        pdf = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            leftMargin=40,
            rightMargin=40,
            topMargin=40,
            bottomMargin=40,
        )

        styles = getSampleStyleSheet()
        code_style = styles["Code"]
        code_style.fontSize = 9
        code_style.leading = 12

        story = []
        with open(input_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                escaped = line.rstrip("\r\n").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                if not escaped.strip():
                    story.append(Spacer(1, 6))
                else:
                    story.append(Paragraph(escaped, code_style))

        if not story:
            story.append(Paragraph("(Пустой текстовый файл)", code_style))

        pdf.build(story)
        duration = time.time() - start_time
        converted_size = output_path.stat().st_size

        return ConversionResult(
            success=True,
            output_path=output_path,
            original_size=orig_size,
            converted_size=converted_size,
            engine_used="native_txt",
            duration_seconds=round(duration, 3),
        )
