import csv
from io import StringIO, BytesIO
from typing import List, Any
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

def generate_csv_string(headers: List[str], rows: List[List[Any]]) -> str:
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    return output.getvalue()

def generate_excel_bytes(sheet_title: str, headers: List[str], rows: List[List[Any]]) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_title[:31] # Excel max sheet title is 31 chars

    # Header styling (Turmeric yellow background)
    header_fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
    header_font = Font(name="Arial", size=10, bold=True, color="92400E")
    regular_font = Font(name="Arial", size=9)
    thin_border = Border(
        left=Side(style='thin', color='E5E7EB'),
        right=Side(style='thin', color='E5E7EB'),
        top=Side(style='thin', color='E5E7EB'),
        bottom=Side(style='thin', color='E5E7EB')
    )

    ws.append(headers)
    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border

    for row_idx, row in enumerate(rows, start=2):
        ws.append(row)
        for col_idx in range(1, len(row) + 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.font = regular_font
            cell.border = thin_border
            if isinstance(row[col_idx - 1], (int, float)):
                cell.alignment = Alignment(horizontal="right")

    # Auto-adjust column widths
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    buffer = BytesIO()
    wb.save(buffer)
    excel_bytes = buffer.getvalue()
    buffer.close()
    return excel_bytes
