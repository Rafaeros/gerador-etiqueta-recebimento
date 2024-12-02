"""Module to generate and print labels from a json file"""

import json
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import mm
from reportlab.lib.colors import white, black

WIDTH, HEIGHT = 85 * mm, 70 * mm
MARGIN = 5 * mm


def get_middle_x_coord(pdf, text, font_size) -> tuple[float, float]:
    """Get the middle x coordinate of the text"""
    text_width = pdf.stringWidth(text, "Helvetica", font_size)
    x: float = (WIDTH - text_width) / 2
    return x


def draw_text(
    pdf: canvas,
    y: float,
    text: str,
    x: float = None,
    max_width: float = 65 * mm,
    font_size=22,
    pending: bool = False,
) -> None:
    """Draw responsive text in the middle of the page"""

    while font_size > 1:  # Limite inferior para o tamanho da fonte
        text_width = pdf.stringWidth(text, "Helvetica", font_size)
        if text_width <= max_width:
            break  # O texto cabe dentro do limite
        font_size -= 1  # Reduz o tamanho da fonte

    pdf.setFont("Helvetica", font_size)

    if x is None:
        x = get_middle_x_coord(pdf, text, font_size)
        if pending:
            x -= 5 * mm
        pdf.drawString(x, y, text)

    else:
        pdf.drawString(x, y, text)


def generate_pending_materials_labels(data: dict):
    """Generate and print labels from a json file"""

    pdf = canvas.Canvas("pending_labels.pdf", pagesize=(WIDTH, HEIGHT))
    rectangle_x = WIDTH - 10 * mm

    if data["pending_materials"] == []:
        return

    for material in data["pending_materials"]:
        pdf.setFillColor(black)
        pdf.rect(0, 0, WIDTH, HEIGHT, stroke=0, fill=1)
        pdf.setFillColor(white)
        pdf.rect(
            rectangle_x,
            MARGIN,
            10 * mm,
            HEIGHT - MARGIN - MARGIN,
            stroke=0,
            fill=1,
        )
        draw_text(pdf, HEIGHT - 10 * mm, material["op_number"], pending=True)
        draw_text(pdf, HEIGHT - 25 * mm, material["product"], pending=True)
        draw_text(pdf, HEIGHT - 45 * mm, material["code"], pending=True)
        draw_text(
            pdf,
            HEIGHT - 65 * mm,
            f"QTD: {int(material["pending_qty"])} PCs",
            pending=True,
        )
        pdf.setStrokeColor(white)
        pdf.rect(5 * mm, HEIGHT - 50 * mm, 65 * mm, 15 * mm, stroke=1, fill=0)
        pdf.showPage()

    pdf.save()


def generate_stock_labels(data: dict):
    """Generate and print labels from a json file"""

    pdf = canvas.Canvas("stock_labels.pdf", pagesize=(WIDTH, HEIGHT))

    date: str = data["date"]
    nfe: int = data["nfe_number"]
    supplier_name: str = data["supplier_name"]

    for order in data["orders"]:
        for _ in range(2):
            pdf.setFillColor(black)
            pdf.rect(0, HEIGHT - 40*mm, width=WIDTH, height=10 * mm, stroke=0, fill=1)
            draw_text(
                pdf,
                MARGIN + 10 * mm - MARGIN,
                f"QTD: {int(order['qty'])} {order['unit_type']}",
                max_width=85 * mm,
                font_size=10,
            )
            draw_text(
                pdf, HEIGHT - MARGIN, date, MARGIN, max_width=80 * mm, font_size=10
            )
            draw_text(
                pdf, HEIGHT - MARGIN, f"NF {nfe}", max_width=85 * mm, font_size=15
            )
            draw_text(
                pdf, HEIGHT - 15 * mm, order["order"], max_width=85 * mm, font_size=15
            )
            draw_text(
                pdf, HEIGHT - 25 * mm, supplier_name, max_width=85 * mm, font_size=15
            )
            pdf.setFillColor(white)
            draw_text(
                pdf, HEIGHT - 37 * mm, order["code"], max_width=85 * mm, font_size=15
            )
            pdf.setFillColor(black)
            draw_text(pdf, HEIGHT - 45 * mm, order["description"], max_width=80 * mm, font_size=10)
            draw_text(
                pdf,
                MARGIN,
                f"QTD TOTAL: {int(order['qty_total'])} {order['unit_type']}",
                max_width=85 * mm,
                font_size=10,
            )
            pdf.showPage()
    pdf.save()


def generate_nfe_labels():
    """Generate and print labels from a json file"""

    with open("nfe_data.json", "r", encoding="utf-8") as file:
        data = json.load(file)
        generate_pending_materials_labels(data)
        generate_stock_labels(data)

if __name__ == "__main__":
    generate_nfe_labels()
