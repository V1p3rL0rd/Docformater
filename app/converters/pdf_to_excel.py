import time
from pathlib import Path
from typing import List, Optional

from app.converters.base import ConversionError, ConversionResult

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

try:
    import pypdf
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False


def _try_parse_number(val: str):
    """Convert string to int or float if possible, preserving formatting."""
    clean = val.strip().replace(" ", "").replace("\xa0", "")
    # Check integer
    try:
        if clean.isdigit() or (clean.startswith("-") and clean[1:].isdigit()):
            return int(clean)
    except Exception:
        pass
    # Check float with dot or comma
    try:
        clean_dot = clean.replace(",", ".")
        val_float = float(clean_dot)
        return val_float
    except Exception:
        pass
    return val


class PdfToExcelConverter:
    """Converts PDF documents containing tables or tabular data into Excel (.xlsx) workbooks."""

    def __init__(self):
        self.is_available = HAS_OPENPYXL and (HAS_PDFPLUMBER or HAS_PYPDF)

    def convert(self, input_pdf: Path, output_xlsx: Path) -> ConversionResult:
        if not input_pdf.exists():
            raise ConversionError(f"PDF file not found: {input_pdf}")

        if not self.is_available:
            raise ConversionError("Excel conversion requires openpyxl and pdfplumber/pypdf.")

        start_time = time.time()
        orig_size = input_pdf.stat().st_size
        output_xlsx.parent.mkdir(parents=True, exist_ok=True)

        engine_used = "pdfplumber + openpyxl"
        page_count = 0
        wb = openpyxl.Workbook()
        # Remove default sheet to build custom ones
        default_sheet = wb.active

        # Styling
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1E40AF", end_color="1E40AF", fill_type="solid")
        zebra_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
        regular_font = Font(name="Calibri", size=10)
        border_side = Side(border_style="thin", color="CBD5E1")
        cell_border = Border(left=border_side, right=border_side, top=border_side, bottom=border_side)
        center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
        left_align = Alignment(horizontal="left", vertical="center", wrap_text=True)

        tables_found = 0

        if HAS_PDFPLUMBER:
            try:
                with pdfplumber.open(input_pdf) as pdf:
                    page_count = len(pdf.pages)

                    for p_idx, page in enumerate(pdf.pages, start=1):
                        extracted_tables = page.extract_tables()

                        if not extracted_tables:
                            # Fallback: extract lines of text and split by spaces/tabs
                            raw_text = page.extract_text()
                            if raw_text:
                                text_lines = [line.split() for line in raw_text.splitlines() if line.strip()]
                                if text_lines:
                                    extracted_tables = [text_lines]

                        if not extracted_tables:
                            continue

                        for t_idx, table in enumerate(extracted_tables, start=1):
                            tables_found += 1
                            sheet_title = f"Лист {p_idx}" if len(extracted_tables) == 1 else f"Стр {p_idx} Табл {t_idx}"
                            sheet = wb.create_sheet(title=sheet_title[:31])

                            for r_idx, row in enumerate(table, start=1):
                                for c_idx, cell_value in enumerate(row, start=1):
                                    cell = sheet.cell(row=r_idx, column=c_idx)
                                    val_str = str(cell_value or "").strip()
                                    parsed_val = _try_parse_number(val_str)
                                    cell.value = parsed_val
                                    cell.border = cell_border

                                    if r_idx == 1:
                                        cell.font = header_font
                                        cell.fill = header_fill
                                        cell.alignment = center_align
                                    else:
                                        cell.font = regular_font
                                        cell.alignment = left_align
                                        if r_idx % 2 == 0:
                                            cell.fill = zebra_fill

                            # Auto adjust column widths
                            for col in sheet.columns:
                                max_len = 0
                                col_letter = get_column_letter(col[0].column)
                                for cell in col:
                                    try:
                                        if cell.value:
                                            max_len = max(max_len, len(str(cell.value)))
                                    except Exception:
                                        pass
                                sheet.column_dimensions[col_letter].width = max(min(max_len + 4, 50), 12)
            except Exception as e:
                engine_used = None

        # Fallback to pypdf if pdfplumber fails or is missing
        if tables_found == 0 and HAS_PYPDF:
            try:
                engine_used = "pypdf + openpyxl"
                reader = pypdf.PdfReader(str(input_pdf))
                page_count = len(reader.pages)

                for p_idx, page in enumerate(reader.pages, start=1):
                    text = page.extract_text() or ""
                    lines = [line.strip() for line in text.splitlines() if line.strip()]
                    if not lines:
                        continue

                    tables_found += 1
                    sheet = wb.create_sheet(title=f"Стр {p_idx}"[:31])
                    for r_idx, line in enumerate(lines, start=1):
                        parts = line.split()
                        for c_idx, part in enumerate(parts, start=1):
                            cell = sheet.cell(row=r_idx, column=c_idx)
                            cell.value = _try_parse_number(part)
                            cell.font = regular_font
                            cell.border = cell_border
            except Exception as e:
                raise ConversionError(f"Failed to extract PDF data for Excel: {e}")

        # If no tables found, add an informative sheet
        if tables_found == 0:
            ws = wb.create_sheet(title="Данные")
            ws.cell(row=1, column=1, value="В переданном PDF документе не обнаружено таблиц или текста.")
        
        # Remove empty initial default sheet if custom sheets were created
        if len(wb.sheetnames) > 1 and "Sheet" in wb.sheetnames:
            wb.remove(default_sheet)

        wb.save(str(output_xlsx))

        duration = time.time() - start_time
        converted_size = output_xlsx.stat().st_size

        return ConversionResult(
            success=True,
            output_path=output_xlsx,
            original_size=orig_size,
            converted_size=converted_size,
            engine_used=engine_used or "openpyxl",
            duration_seconds=round(duration, 3),
            page_count=page_count,
        )
