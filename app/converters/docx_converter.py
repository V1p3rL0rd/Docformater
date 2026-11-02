import time
from pathlib import Path

from app.converters.base import ConversionError, ConversionResult

try:
    from docx import Document
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    HAS_DOCX_LIBS = True
except ImportError:
    HAS_DOCX_LIBS = False


class NativeDocxConverter:
    """Pure Python fallback converter for DOCX documents using python-docx and ReportLab."""

    def __init__(self):
        self.is_available = HAS_DOCX_LIBS

    def convert(self, input_file: Path, output_file: Path) -> ConversionResult:
        if not self.is_available:
            raise ConversionError("python-docx or reportlab is not installed.")

        start_time = time.time()
        orig_size = input_file.stat().st_size

        try:
            doc = Document(str(input_file))
        except Exception as e:
            raise ConversionError(f"Failed to open DOCX file: {e}")

        output_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            pdf = SimpleDocTemplate(
                str(output_file),
                pagesize=A4,
                leftMargin=40,
                rightMargin=40,
                topMargin=40,
                bottomMargin=40,
            )

            styles = getSampleStyleSheet()
            normal_style = styles["Normal"]
            normal_style.fontSize = 10
            normal_style.leading = 14

            title_style = styles["Title"]
            title_style.fontSize = 18
            title_style.leading = 22

            h1_style = styles["Heading1"]
            h1_style.fontSize = 14
            h1_style.leading = 18

            h2_style = styles["Heading2"]
            h2_style.fontSize = 12
            h2_style.leading = 16

            story = []

            for paragraph in doc.paragraphs:
                text = paragraph.text.strip()
                if not text:
                    story.append(Spacer(1, 6))
                    continue

                style_name = paragraph.style.name.lower() if paragraph.style else ""
                
                # Format inline runs (bold, italic)
                formatted_parts = []
                for run in paragraph.runs:
                    run_text = run.text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    if run.bold and run.italic:
                        run_text = f"<b><i>{run_text}</i></b>"
                    elif run.bold:
                        run_text = f"<b>{run_text}</b>"
                    elif run.italic:
                        run_text = f"<i>{run_text}</i>"
                    formatted_parts.append(run_text)

                html_text = "".join(formatted_parts) if formatted_parts else text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

                if "heading 1" in style_name:
                    p = Paragraph(html_text, h1_style)
                    story.append(p)
                    story.append(Spacer(1, 8))
                elif "heading 2" in style_name:
                    p = Paragraph(html_text, h2_style)
                    story.append(p)
                    story.append(Spacer(1, 6))
                elif "title" in style_name:
                    p = Paragraph(html_text, title_style)
                    story.append(p)
                    story.append(Spacer(1, 12))
                else:
                    p = Paragraph(html_text, normal_style)
                    story.append(p)
                    story.append(Spacer(1, 4))

            # Process tables
            for table in doc.tables:
                table_data = []
                for row in table.rows:
                    row_cells = []
                    for cell in row.cells:
                        clean_cell_text = cell.text.strip().replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                        row_cells.append(Paragraph(clean_cell_text, normal_style))
                    if row_cells:
                        table_data.append(row_cells)

                if table_data:
                    # Calculate approximate column width
                    col_count = max(len(r) for r in table_data)
                    col_width = (A4[0] - 80) / max(col_count, 1)
                    
                    t = Table(table_data, colWidths=[col_width] * col_count)
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor("#1e293b")),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ('TOPPADDING', (0, 0), (-1, -1), 6),
                        ('LEFTPADDING', (0, 0), (-1, -1), 6),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ]))
                    story.append(Spacer(1, 10))
                    story.append(t)
                    story.append(Spacer(1, 10))

            if not story:
                story.append(Paragraph("Empty Document", normal_style))

            pdf.build(story)

        except Exception as e:
            raise ConversionError(f"Native DOCX to PDF conversion failed: {e}")

        duration = time.time() - start_time
        converted_size = output_file.stat().st_size

        return ConversionResult(
            success=True,
            output_path=output_file,
            original_size=orig_size,
            converted_size=converted_size,
            engine_used="native_python_docx",
            duration_seconds=round(duration, 3),
            warning="Converted using native Python engine (layout may slightly differ from MS Word/LibreOffice)."
        )
