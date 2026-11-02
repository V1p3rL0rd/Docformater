import csv
import time
from pathlib import Path

from app.converters.base import ConversionError, ConversionResult

try:
    import openpyxl
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    HAS_EXCEL_LIBS = True
except ImportError:
    HAS_EXCEL_LIBS = False


class NativeExcelConverter:
    """Pure Python fallback converter for XLSX, XLS, and CSV spreadsheets using openpyxl/csv and ReportLab."""

    def __init__(self):
        self.is_available = HAS_EXCEL_LIBS

    def convert(self, input_file: Path, output_file: Path) -> ConversionResult:
        if not self.is_available:
            raise ConversionError("openpyxl or reportlab is not installed.")

        start_time = time.time()
        orig_size = input_file.stat().st_size
        suffix = input_file.suffix.lower()

        sheets_data = {}

        if suffix in (".xlsx", ".xlsm"):
            try:
                wb = openpyxl.load_workbook(str(input_file), data_only=True)
                for sheetname in wb.sheetnames:
                    sheet = wb[sheetname]
                    rows = []
                    for row in sheet.iter_rows(values_only=True):
                        # Filter completely empty trailing rows
                        if any(v is not None and str(v).strip() != "" for v in row):
                            cleaned_row = [str(v) if v is not None else "" for v in row]
                            rows.append(cleaned_row)
                    if rows:
                        sheets_data[sheetname] = rows
            except Exception as e:
                raise ConversionError(f"Failed to read Excel workbook: {e}")

        elif suffix == ".csv":
            try:
                rows = []
                with open(input_file, mode="r", encoding="utf-8", errors="replace") as f:
                    reader = csv.reader(f)
                    for row in reader:
                        rows.append(row)
                sheets_data["Sheet1"] = rows
            except Exception as e:
                raise ConversionError(f"Failed to read CSV file: {e}")
        else:
            raise ConversionError(f"Unsupported spreadsheet format for native converter: {suffix}")

        if not sheets_data:
            sheets_data["Sheet1"] = [["(Empty Spreadsheet)"]]

        output_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Spreadsheet PDF is better formatted in Landscape orientation
            pdf = SimpleDocTemplate(
                str(output_file),
                pagesize=landscape(A4),
                leftMargin=30,
                rightMargin=30,
                topMargin=30,
                bottomMargin=30,
            )

            styles = getSampleStyleSheet()
            sheet_title_style = styles["Heading2"]
            sheet_title_style.fontSize = 13
            sheet_title_style.leading = 16

            cell_style = styles["Normal"]
            cell_style.fontSize = 8
            cell_style.leading = 10

            header_cell_style = styles["Normal"]
            header_cell_style.fontSize = 8
            header_cell_style.leading = 10
            header_cell_style.fontName = "Helvetica-Bold"

            page_width = landscape(A4)[0] - 60
            story = []

            for sheet_idx, (sheet_name, rows) in enumerate(sheets_data.items()):
                if sheet_idx > 0:
                    story.append(PageBreak())

                story.append(Paragraph(f"<b>Лист:</b> {sheet_name}", sheet_title_style))
                story.append(Spacer(1, 8))

                if not rows:
                    story.append(Paragraph("<i>Лист пуст</i>", cell_style))
                    continue

                # Max columns in sheet (limit to 30 columns to fit on page sensibly)
                max_cols = min(max(len(r) for r in rows), 30)
                col_width = page_width / max(max_cols, 1)

                table_data = []
                for r_idx, row in enumerate(rows):
                    row_data = []
                    for c_idx in range(max_cols):
                        val = row[c_idx] if c_idx < len(row) else ""
                        escaped = val.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                        if r_idx == 0:
                            row_data.append(Paragraph(f"<b>{escaped}</b>", header_cell_style))
                        else:
                            row_data.append(Paragraph(escaped, cell_style))
                    table_data.append(row_data)

                t = Table(table_data, colWidths=[col_width] * max_cols, repeatRows=1)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2563eb")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('LEFTPADDING', (0, 0), (-1, -1), 4),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
                ]))
                story.append(t)

            pdf.build(story)

        except Exception as e:
            raise ConversionError(f"Native Excel to PDF conversion failed: {e}")

        duration = time.time() - start_time
        converted_size = output_file.stat().st_size

        return ConversionResult(
            success=True,
            output_path=output_file,
            original_size=orig_size,
            converted_size=converted_size,
            engine_used="native_python_excel",
            duration_seconds=round(duration, 3),
            warning="Converted using native Python engine (layout may slightly differ from MS Excel/LibreOffice)."
        )
