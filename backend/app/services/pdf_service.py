import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from app.config import settings
from app.models.billing import Invoice

def generate_invoice_pdf(invoice: Invoice) -> bytes:
    """
    Generates a commercial GST Tax Invoice PDF.
    Rule: Invoices stay in English.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#D97706") # Turmeric yellow/amber
    )
    normal_style = styles['Normal']
    normal_style.fontSize = 9
    normal_style.leading = 12

    bold_style = ParagraphStyle(
        'Bold',
        parent=normal_style,
        fontName='Helvetica-Bold'
    )

    elements = []

    # Header
    company_info = f"""
    <b>{settings.COMPANY_NAME}</b><br/>
    {settings.COMPANY_ADDRESS}<br/>
    Phone: {settings.COMPANY_PHONE} | Email: {settings.COMPANY_EMAIL}<br/>
    <b>GSTIN: {settings.COMPANY_GSTIN} | State: {settings.COMPANY_STATE} (Code: {settings.COMPANY_STATE_CODE})</b>
    """
    elements.append(Paragraph(company_info, normal_style))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("<b>TAX INVOICE</b>", title_style))
    elements.append(Spacer(1, 8))

    # Invoice & Customer Details Table
    inv_details = [
        [
            Paragraph(f"<b>Invoice No:</b> {invoice.invoice_no}<br/><b>Invoice Date:</b> {invoice.created_at.strftime('%d-%m-%Y')}<br/><b>Status:</b> {invoice.status.value.upper()}", normal_style),
            Paragraph(f"<b>Billed To:</b><br/><b>{invoice.customer.name}</b><br/>{invoice.customer.address}<br/><b>GSTIN:</b> {invoice.customer.gstin or 'URP'}<br/><b>State:</b> {invoice.customer.state} ({invoice.customer.state_code})", normal_style)
        ]
    ]
    detail_table = Table(inv_details, colWidths=[270, 270])
    detail_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#D6D3D1")),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FFFDF7")),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(detail_table)
    elements.append(Spacer(1, 12))

    # Items Table
    item_rows = [
        ["#", "Product Description", "HSN", "Qty (Pkts)", "Rate (Rs)", "Subtotal", "CGST", "SGST", "IGST", "Total (Rs)"]
    ]

    for idx, item in enumerate(invoice.items, start=1):
        item_rows.append([
            str(idx),
            item.product.name,
            item.hsn_code or item.product.hsn_code,
            str(item.quantity_packets),
            f"{item.unit_price_paise / 100:.2f}",
            f"{item.subtotal_paise / 100:.2f}",
            f"{item.cgst_paise / 100:.2f}",
            f"{item.sgst_paise / 100:.2f}",
            f"{item.igst_paise / 100:.2f}",
            f"{item.total_paise / 100:.2f}"
        ])

    # Totals row
    item_rows.append([
        "", "TOTALS", "", "", "",
        f"Rs {invoice.subtotal_paise / 100:.2f}",
        f"Rs {invoice.cgst_paise / 100:.2f}",
        f"Rs {invoice.sgst_paise / 100:.2f}",
        f"Rs {invoice.igst_paise / 100:.2f}",
        f"Rs {invoice.total_paise / 100:.2f}"
    ])

    items_table = Table(item_rows, colWidths=[20, 140, 50, 45, 45, 60, 45, 45, 45, 45])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F5F5F4")),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E7E5E4")),
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#FEF3C7")),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 20))

    # Signatory Box
    sig_data = [
        ["Declaration: We declare that this invoice shows the actual price of the goods described and that all particulars are true and correct.",
         f"For {settings.COMPANY_NAME}\n\n\nAuthorized Signatory"]
    ]
    sig_table = Table(sig_data, colWidths=[340, 200])
    sig_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#D6D3D1")),
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(sig_table)

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def generate_credit_note_pdf(credit_note, invoice) -> bytes:
    """Generates a GST Credit Note PDF in memory."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CNTitle',
        parent=styles['Heading1'],
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#B45309")
    )
    normal_style = styles['Normal']
    normal_style.fontSize = 9
    normal_style.leading = 12

    elements = []
    company_info = f"""
    <b>{settings.COMPANY_NAME}</b><br/>
    {settings.COMPANY_ADDRESS}<br/>
    Phone: {settings.COMPANY_PHONE} | Email: {settings.COMPANY_EMAIL}<br/>
    <b>GSTIN: {settings.COMPANY_GSTIN} | State: {settings.COMPANY_STATE} (Code: {settings.COMPANY_STATE_CODE})</b>
    """
    elements.append(Paragraph(company_info, normal_style))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("<b>CREDIT NOTE</b>", title_style))
    elements.append(Spacer(1, 8))

    inv_no = invoice.invoice_no if invoice else f"#{credit_note.invoice_id}"
    rows = [
        ["Credit Note No:", credit_note.credit_note_no, "Against Invoice:", inv_no],
        ["Date:", credit_note.created_at.strftime("%d-%m-%Y"), "Amount (Rs):", f"{credit_note.total_paise / 100:.2f}"],
        ["Reason:", credit_note.reason, "", ""],
    ]
    tbl = Table(rows, colWidths=[100, 170, 100, 170])
    tbl.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E7E5E4")),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(tbl)
    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
