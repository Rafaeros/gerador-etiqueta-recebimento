"""Module to generate and print labels from a json file"""

import json
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import mm
from reportlab.lib.colors import white, black
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


WIDTH, HEIGHT = 85 * mm, 70 * mm
MARGIN = 5 * mm
ARIAL_FONT_PATH = "./assets/fonts/Arial.ttf"
ARIAL_BD_FONT_PATH = "./assets/fonts/Arial-Bold.ttf"

pdfmetrics.registerFont(TTFont("Arial", ARIAL_FONT_PATH))
pdfmetrics.registerFont(TTFont("Arial-Bold", ARIAL_BD_FONT_PATH))


def get_middle_x_coord(pdf, text: str, font_name, font_size) -> float:
    """Get the middle x coordinate of the text"""
    text_width = pdf.stringWidth(text, font_name, font_size)
    x: float = (WIDTH - text_width) / 2
    return x


def draw_text(
    pdf: canvas,
    y: float,
    text: str,
    x: float = None,
    max_width: float = 75 * mm,
    font_name: str = "Arial-Bold",
    font_size=22,
    pending: bool = False,
    wrap: bool = False,
) -> None:
    """Draw responsive text in the middle of the page"""

    if wrap:
        font_size = 8
        pdf.setFont(font_name, font_size)
        words = text.split(" ")
        lines = []
        current_line = ""
        for word in words:
            test_line = f"{current_line} {word}".strip()
            if pdf.stringWidth(test_line, font_name, font_size) <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line)
        for line in lines:
            if x is None:
                x = get_middle_x_coord(pdf, line, font_name, font_size)
                if pending:
                    x -= 5 * mm
            pdf.drawString(x, y, line)
            y -= font_size + 5

        return

    while font_size > 1:  # Limite inferior para o tamanho da fonte
        text_width = pdf.stringWidth(text, font_name, font_size)
        if text_width <= max_width:
            break  # O texto cabe dentro do limite
        font_size -= 1  # Reduz o tamanho da fonte

    pdf.setFont(font_name, font_size)

    if x is None:
        x = get_middle_x_coord(pdf, text, font_name, font_size)
        if pending:
            x -= 5 * mm
        pdf.drawString(x, y, text)

    else:
        pdf.drawString(x, y, text)


def generate_pending_materials_labels(data: dict):
    """Generate and print labels from a json file"""

    pdf = canvas.Canvas("./tmp/pending_labels.pdf", pagesize=(WIDTH, HEIGHT))
    rectangle_x = WIDTH - 10 * mm

    if data["pending_materials"] == []:
        return

    for material in data["pending_materials"]:

        if material["pending_qty"] == 0:
            continue

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
        draw_text(
            pdf, HEIGHT - 15 * mm, material["op_number"], pending=True, font_size=18
        )
        draw_text(
            pdf,
            HEIGHT - 30 * mm,
            material["product"],
            pending=True,
            font_name="Arial",
            font_size=21,
        )
        draw_text(
            pdf,
            HEIGHT - 45 * mm,
            material["code"],
            pending=True,
            font_name="Arial",
            font_size=19.5,
        )
        draw_text(
            pdf,
            10 * mm,
            f"QUANTIDADE: {int(material["pending_qty"])} UND",
            pending=True,
            font_name="Arial",
            font_size=10,
        )
        pdf.setStrokeColor(white)
        pdf.rect(5 * mm, 6 * mm, WIDTH - 20 * mm, 10 * mm, stroke=1, fill=0)
        pdf.showPage()

    pdf.save()


def generate_stock_labels(data: dict):
    """Generate and print labels from a json file"""

    pdf = canvas.Canvas("./tmp/stock_labels.pdf", pagesize=(WIDTH, HEIGHT))

    date: str = data["date"]
    nfe: int = data["nfe_number"]
    supplier_name: str = data["supplier_name"]

    for order in data["orders"]:

        if order["qty"] == 0:
            continue

        qr = qrcode.make(f"{order["code"]};{int(order["qty"])}")
        qr.save("./tmp/qr-code.png")

        for _ in range(2):
            pdf.setFillColor(black)
            pdf.rect(0, HEIGHT - 40 * mm, width=WIDTH, height=10 * mm, stroke=0, fill=1)
            pdf.setStrokeColor(white)
            pdf.rect(0.4 * mm, 5 * mm, 65 * mm, 15 * mm, stroke=1, fill=0)

            draw_text(
                pdf, HEIGHT - MARGIN, date, MARGIN, max_width=80 * mm, font_size=10
            )

            pdf.drawImage(
                "./assets/img/fk-logo.png",
                MARGIN,
                HEIGHT - 17 * mm,
                width=10 * mm,
                height=10 * mm,
            )

            draw_text(
                pdf,
                HEIGHT - 7 * mm,
                f"NF {nfe}",
                max_width=85 * mm,
                font_name="Arial-Bold",
                font_size=13,
            )
            draw_text(
                pdf,
                HEIGHT - 15 * mm,
                order["order"],
                max_width=85 * mm,
                font_name="Arial-Bold",
                font_size=11,
            )
            pdf.drawImage(
                "./tmp/qr-code.png",
                70 * mm,
                HEIGHT - 17 * mm,
                width=10 * mm,
                height=10 * mm,
            )
            draw_text(
                pdf,
                HEIGHT - 25 * mm,
                supplier_name,
                max_width=85 * mm,
                font_name="Arial-Bold",
                font_size=22,
            )
            pdf.setFillColor(white)
            draw_text(
                pdf,
                HEIGHT - 37 * mm,
                order["code"],
                max_width=85 * mm,
                font_name="Arial",
                font_size=16,
            )
            pdf.setFillColor(black)
            draw_text(
                pdf,
                HEIGHT - 45 * mm,
                order["description"],
                max_width=82 * mm,
                font_name="Arial",
                font_size=8,
                wrap=True,
            )
            draw_text(
                pdf,
                MARGIN + 10 * mm - MARGIN,
                f"Quantidade: {int(order['qty'])} {order['unit_type']}",
                max_width=85 * mm,
                font_name="Arial",
                font_size=10,
            )
            draw_text(
                pdf,
                MARGIN,
                f"Lote Total: {int(order['qty_total'])} {order['unit_type']}",
                max_width=85 * mm,
                font_name="Arial",
                font_size=10.5,
            )
            pdf.showPage()
    pdf.save()


def generate_nfe_labels():
    """Generate and print labels from a json file"""

    with open("./tmp/nfe_data.json", "r", encoding="utf-8") as file:
        data = json.load(file)
        generate_pending_materials_labels(data)
        generate_stock_labels(data)


if __name__ == "__main__":
    generate_nfe_labels()
