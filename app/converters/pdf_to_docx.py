import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional

from app.converters.base import ConversionError, ConversionResult
from app.converters.libreoffice import find_libreoffice_binary

try:
    from pdf2docx import Converter as Pdf2DocxConverterEngine
    HAS_PDF2DOCX = True
except ImportError:
    HAS_PDF2DOCX = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    from docx import Document
    from docx.shared import Pt, Inches, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False


class PdfToDocxConverter:
    """Converts PDF files to Microsoft Word (.docx) format."""

    def __init__(self):
        self.lo_binary = find_libreoffice_binary()

    def convert(self, input_pdf: Path, output_docx: Path) -> ConversionResult:
        if not input_pdf.exists():
            raise ConversionError(f"PDF file not found: {input_pdf}")

        start_time = time.time()
        orig_size = input_pdf.stat().st_size
        output_docx.parent.mkdir(parents=True, exist_ok=True)
        engine_used = None

        # 1. Prefer pdf2docx library (specialized layout analyzer & Word generator)
        if HAS_PDF2DOCX:
            try:
                cv = Pdf2DocxConverterEngine(str(input_pdf))
                cv.convert(str(output_docx), start=0, end=None)
                cv.close()
                if output_docx.exists() and output_docx.stat().st_size > 0:
                    engine_used = "pdf2docx (PyMuPDF Layout Engine)"
            except Exception:
                engine_used = None

        # 2. Try LibreOffice headless Writer PDF import if available
        if engine_used is None and self.lo_binary and os.path.exists(self.lo_binary):
            try:
                with tempfile.TemporaryDirectory() as temp_dir:
                    profile_dir = Path(temp_dir) / "profile"
                    profile_dir.mkdir(parents=True, exist_ok=True)
                    out_dir = Path(temp_dir) / "out"
                    out_dir.mkdir(parents=True, exist_ok=True)

                    cmd = [
                        self.lo_binary,
                        f"-env:UserInstallation=file://{profile_dir.as_posix()}",
                        "--headless",
                        "--invisible",
                        "--infilter=writer_pdf_import",
                        "--convert-to",
                        "docx:MS Word 2007 XML",
                        "--outdir",
                        str(out_dir),
                        str(input_pdf),
                    ]

                    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60, check=False)
                    gen_files = list(out_dir.glob("*.docx"))
                    if gen_files:
                        shutil.copy2(gen_files[0], output_docx)
                        engine_used = "LibreOffice Writer PDF Import"
            except Exception:
                engine_used = None

        # 3. Native fallback: pdfplumber/pypdf + python-docx
        if engine_used is None and HAS_DOCX and (HAS_PDFPLUMBER or True):
            try:
                self._convert_with_python_docx(input_pdf, output_docx)
                engine_used = "Native Python DOCX Builder"
            except Exception as e:
                raise ConversionError(f"PDF to DOCX conversion failed: {e}")

        if not output_docx.exists() or output_docx.stat().st_size == 0:
            raise ConversionError("PDF to DOCX conversion failed: no output file generated.")

        duration = time.time() - start_time
        converted_size = output_docx.stat().st_size

        return ConversionResult(
            success=True,
            output_path=output_docx,
            original_size=orig_size,
            converted_size=converted_size,
            engine_used=engine_used or "python-docx",
            duration_seconds=round(duration, 3),
        )

    def _convert_with_python_docx(self, input_pdf: Path, output_docx: Path):
        """Constructs a clean Word document by extracting paragraphs and tables."""
        doc = Document()

        # Set standard margins
        sections = doc.sections
        for section in sections:
            section.top_margin = Inches(1)
            section.bottom_margin = Inches(1)
            section.left_margin = Inches(1)
            section.right_margin = Inches(1)

        has_content = False

        if HAS_PDFPLUMBER:
            import pdfplumber
            with pdfplumber.open(input_pdf) as pdf:
                for p_idx, page in enumerate(pdf.pages, start=1):
                    if p_idx > 1:
                        doc.add_page_break()

                    tables = page.extract_tables()
                    raw_text = page.extract_text() or ""

                    # Add text paragraphs
                    for line in raw_text.splitlines():
                        clean_line = line.strip()
                        if clean_line:
                            has_content = True
                            p = doc.add_paragraph(clean_line)
                            p.paragraph_format.line_spacing = 1.15
                            p.paragraph_format.space_after = Pt(4)

                    # Add tables if detected
                    if tables:
                        for table_data in tables:
                            if not table_data:
                                continue
                            has_content = True
                            cols_count = max(len(r) for r in table_data)
                            t = doc.add_table(rows=len(table_data), cols=cols_count)
                            t.style = "Light Grid Accent 1" if "Light Grid Accent 1" in doc.styles else "Table Grid"

                            for r_idx, row in enumerate(table_data):
                                for c_idx, cell_value in enumerate(row):
                                    if c_idx < cols_count:
                                        t.cell(r_idx, c_idx).text = str(cell_value or "").strip()

        if not has_content:
            # Fallback using pypdf
            import pypdf
            reader = pypdf.PdfReader(str(input_pdf))
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    for line in text.splitlines():
                        if line.strip():
                            doc.add_paragraph(line.strip())

        doc.save(str(output_docx))
