import os
from pathlib import Path
from docx import Document
import openpyxl
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample_files"
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)


def create_sample_docx():
    path = SAMPLE_DIR / "sample_contract.docx"
    doc = Document()
    doc.add_heading("Договор оказания услуг № 102/2026", 0)
    p = doc.add_paragraph("Настоящий договор заключен между Заказчиком и Исполнителем о нижеследующем:")
    p.runs[0].bold = True

    doc.add_heading("1. Предмет договора", level=1)
    doc.add_paragraph("Исполнитель обязуется оказать услуги по автоматизации документооборота и конвертации офисных файлов.")

    doc.add_heading("2. Спецификация и стоимость", level=1)
    table = doc.add_table(rows=1, cols=3)
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = "Наименование услуги"
    hdr_cells[1].text = "Количество"
    hdr_cells[2].text = "Стоимость (руб.)"

    data = [
        ("Конвертация DOCX в PDF", "10 000", "50 000"),
        ("Конвертация Excel в PDF", "5 000", "35 000"),
        ("Сжатие PDF без потери качества", "15 000", "45 000"),
    ]

    for item, qty, price in data:
        row_cells = table.add_row().cells
        row_cells[0].text = item
        row_cells[1].text = qty
        row_cells[2].text = price

    doc.save(str(path))
    print(f"Created {path}")


def create_sample_xlsx():
    path = SAMPLE_DIR / "sample_financial_report.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Отчет 2026"

    headers = ["Месяц", "Доход (руб)", "Расход (руб)", "Чистая прибыль", "Рентабельность"]
    ws.append(headers)

    months = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь"]
    for i, m in enumerate(months, start=1):
        income = 100000 * i
        expense = 45000 * i
        profit = income - expense
        margin = f"{(profit / income) * 100:.1f}%"
        ws.append([m, income, expense, profit, margin])

    # Second sheet
    ws2 = wb.create_sheet(title="Аналитика")
    ws2.append(["Показатель", "Значение"])
    ws2.append(["Общий доход", 2100000])
    ws2.append(["Статус", "Выполнен успешно"])

    wb.save(str(path))
    print(f"Created {path}")


def create_sample_txt():
    path = SAMPLE_DIR / "sample_notes.txt"
    with open(path, "w", encoding="utf-8") as f:
        f.write("ТЕХНИЧЕСКАЯ ЗАМЕТКА ПО ПРОЕКТУ\n")
        f.write("=" * 40 + "\n\n")
        f.write("1. Архитектура сервиса построена на FastAPI.\n")
        f.write("2. Поддерживается сжатие PDF без потери качества (Object Streams).\n")
        f.write("3. Поддерживается конвертация Word и Excel.\n")
    print(f"Created {path}")


def create_sample_pdf_with_image():
    # Create an unoptimized PDF with an embedded raster image to test lossless and smart compression
    path = SAMPLE_DIR / "sample_presentation.pdf"
    img_path = SAMPLE_DIR / "test_pattern.png"

    # Create test image
    img = Image.new("RGB", (800, 600), color=(73, 109, 137))
    img.save(img_path)

    c = canvas.Canvas(str(path), pagesize=letter)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(100, 700, "Отчет компании DocuFlow")
    c.setFont("Helvetica", 12)
    c.drawString(100, 670, "Демонстрационный PDF документ для тестирования сжатия без потерь.")
    c.drawImage(str(img_path), 100, 300, width=400, height=300)
    c.showPage()
    c.save()

    if img_path.exists():
        img_path.unlink()
    print(f"Created {path}")


if __name__ == "__main__":
    create_sample_docx()
    create_sample_xlsx()
    create_sample_txt()
    create_sample_pdf_with_image()
    print("All sample files generated successfully!")
