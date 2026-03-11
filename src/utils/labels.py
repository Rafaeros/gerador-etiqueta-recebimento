"""
Module to generate NFE labels (Pending Materials and Stock) from a JSON file.
Supports PDF generation (Windows) and PNG generation (Linux).
"""

import json
import os
import platform
import pathlib
from typing import List, Callable

from src.utils.logger import log_label_generation
import qrcode
from PIL import Image, ImageDraw, ImageFont

from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import white, black
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing

PAGE_W_MM: float = 85.0
PAGE_H_MM: float = 70.0
MARGIN_MM: float = 5.0
DPI: int = 203
MM_TO_PX: float = DPI / 25.4
PAGE_W_PX: int = int(PAGE_W_MM * MM_TO_PX)
PAGE_H_PX: int = int(PAGE_H_MM * MM_TO_PX)

BASE_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent
TMP_FOLDER = PROJECT_ROOT / "tmp"
TMP_FOLDER.mkdir(exist_ok=True, parents=True)
SRC_DIR = BASE_DIR.parent
LABELS_FOLDER = TMP_FOLDER / "labels"
LABELS_FOLDER.mkdir(exist_ok=True, parents=True)
LOGO_PATH = SRC_DIR / "assets" / "img" / "lanx-logo-sem-fundo.jpeg"
FONTS_PATH = SRC_DIR / "assets" / "fonts"

# Register ReportLab Fonts
try:
    pdfmetrics.registerFont(TTFont("Arial", FONTS_PATH / "Arial.ttf"))
    pdfmetrics.registerFont(TTFont("Arial-Bold", FONTS_PATH / "Arial-Bold.ttf"))
except Exception:
    pass  # Falback to default Helvetica if missing


# --- Helper Functions ---


def x_px(mm_val: float) -> int:
    return int(mm_val * MM_TO_PX)


def y_px(mm_val: float) -> int:
    return int(mm_val * MM_TO_PX)


def get_pil_font(font_name: str, size_pt: int) -> ImageFont.FreeTypeFont:
    size_px = int(size_pt * (DPI / 72))
    font_file = "Arial-Bold.ttf" if "Bold" in font_name else "Arial.ttf"
    try:
        return ImageFont.truetype(str(FONTS_PATH / font_file), size_px)
    except IOError:
        return ImageFont.load_default()


def wrap_text_lines(
    text: str, max_width: float, measure_fn: Callable[[str], float]
) -> List[str]:
    words = text.split()
    lines, current_line = [], ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        if measure_fn(test_line) <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines


def draw_pdf_qr(c: Canvas, qr_data: str, x: float, y: float, size: float) -> None:
    qr_code = qr.QrCodeWidget(qr_data)
    bounds = qr_code.getBounds()
    w, h = bounds[2] - bounds[0], bounds[3] - bounds[1]
    scale = min(size / w, size / h)
    drawing = Drawing(w * scale, h * scale, transform=[scale, 0, 0, scale, 0, 0])
    drawing.add(qr_code)
    drawing.drawOn(c, x, y)


# --- PDF DRAWING ROUTINES ---


def draw_pdf_text(
    pdf: Canvas,
    y_mm: float,
    text: str,
    x_mm: float = None,
    max_w_mm: float = 75.0,
    font: str = "Arial-Bold",
    size: int = 22,
    color=black,
    wrap: bool = False,
    offset_x_mm: float = 0.0,
) -> None:
    pdf.setFillColor(color)
    if wrap:
        size = 8
        pdf.setFont(font, size)
        lines = wrap_text_lines(
            text, max_w_mm * mm, lambda t: pdf.stringWidth(t, font, size)
        )
        for line in lines:
            px = (
                x_mm * mm
                if x_mm is not None
                else (PAGE_W_MM * mm - pdf.stringWidth(line, font, size)) / 2
            )
            pdf.drawString(px + (offset_x_mm * mm), y_mm * mm, line)
            y_mm -= 3.0
        return

    while size > 4 and pdf.stringWidth(text, font, size) > (max_w_mm * mm):
        size -= 1
    pdf.setFont(font, size)
    px = (
        x_mm * mm
        if x_mm is not None
        else (PAGE_W_MM * mm - pdf.stringWidth(text, font, size)) / 2
    )
    pdf.drawString(px + (offset_x_mm * mm), y_mm * mm, text)


def _draw_single_stock_label_pdf(pdf: Canvas, data: dict, order: dict, qr_code: bool):
    """Draws one stock label page on the PDF."""
    pdf.setFillColor(black)
    pdf.rect(0, (PAGE_H_MM - 40) * mm, PAGE_W_MM * mm, 10 * mm, stroke=0, fill=1)
    pdf.setStrokeColor(black)

    draw_pdf_text(
        pdf,
        PAGE_H_MM - MARGIN_MM - 2,
        data.get("date", ""),
        x_mm=MARGIN_MM,
        max_w_mm=80,
        size=10,
    )

    if LOGO_PATH.exists():
        pdf.drawImage(
            str(LOGO_PATH),
            MARGIN_MM * mm,
            (PAGE_H_MM - 17) * mm,
            10 * mm,
            10 * mm,
            mask="auto",
        )

    nfe = order.get("nfe", data.get("nfe_number", ""))
    draw_pdf_text(pdf, PAGE_H_MM - 7, f"NF {nfe}", max_w_mm=85, size=13)
    draw_pdf_text(
        pdf,
        PAGE_H_MM - 6,
        order.get("address", ""),
        x_mm=70,
        max_w_mm=15,
        font="Arial",
        size=5,
        wrap=True,
    )
    draw_pdf_text(
        pdf, PAGE_H_MM - 15, str(order.get("order", "")), max_w_mm=85, size=11
    )

    if qr_code:
        qr_data = f"{order.get('code', '')};{int(order.get('qty', 0))}"
        qr_x_mm = PAGE_W_MM - MARGIN_MM - 10
        draw_pdf_qr(pdf, qr_data, qr_x_mm * mm, 3 * mm, 10 * mm)

    draw_pdf_text(pdf, PAGE_H_MM - 25, order.get("supplier", ""), max_w_mm=85, size=22)
    draw_pdf_text(
        pdf,
        PAGE_H_MM - 37,
        order.get("code", ""),
        max_w_mm=85,
        font="Arial",
        size=16,
        color=white,
    )
    draw_pdf_text(
        pdf,
        PAGE_H_MM - 45,
        order.get("description", ""),
        max_w_mm=82,
        font="Arial",
        size=8,
        wrap=True,
    )
    draw_pdf_text(
        pdf,
        MARGIN_MM + 10 - MARGIN_MM,
        f"Quantidade: {int(order.get('qty', 0))} {order.get('unit_type', '')}",
        max_w_mm=85,
        font="Arial",
        size=10,
    )
    draw_pdf_text(
        pdf,
        MARGIN_MM,
        f"Lote Total: {int(order.get('qty_total', 0))} {order.get('unit_type', '')}",
        max_w_mm=85,
        font="Arial",
        size=10,
    )
    pdf.showPage()


def _draw_single_pending_label_pdf(pdf: Canvas, nfe_number: str, mat: dict):
    """Draws one pending label page on the PDF."""
    pdf.setFillColor(black)
    pdf.rect(0, 0, PAGE_W_MM * mm, PAGE_H_MM * mm, stroke=0, fill=1)
    pdf.setFillColor(white)
    pdf.rect(
        (PAGE_W_MM - 10) * mm,
        MARGIN_MM * mm,
        10 * mm,
        (PAGE_H_MM - 2 * MARGIN_MM) * mm,
        stroke=0,
        fill=1,
    )
    pdf.rect(5 * mm, 5 * mm, (PAGE_W_MM - 20) * mm, 10 * mm, stroke=0, fill=1)

    draw_pdf_text(
        pdf,
        PAGE_H_MM - 10,
        f"NF {nfe_number}",
        offset_x_mm=-5,
        max_w_mm=80,
        size=14,
        color=white,
    )
    draw_pdf_text(
        pdf,
        PAGE_H_MM - 17,
        f"Tipo de Serviço: {mat.get('service_type', '')}",
        offset_x_mm=-5,
        size=14,
        color=white,
    )
    draw_pdf_text(
        pdf,
        PAGE_H_MM - 28,
        mat.get("op_number", ""),
        offset_x_mm=-5,
        size=18,
        color=white,
    )
    draw_pdf_text(
        pdf,
        PAGE_H_MM - 38,
        mat.get("product", ""),
        offset_x_mm=-5,
        font="Arial",
        size=18,
        color=white,
    )
    draw_pdf_text(
        pdf,
        PAGE_H_MM - 50,
        mat.get("code", ""),
        offset_x_mm=-5,
        font="Arial",
        size=18,
        color=white,
    )
    draw_pdf_text(
        pdf,
        8,
        f"QUANTIDADE: {int(mat.get('pending_qty', 0))} UND",
        offset_x_mm=-5,
        font="Arial",
        size=10,
        color=black,
    )
    pdf.showPage()


# --- IMAGE DRAWING ROUTINES ---


def draw_img_text(
    draw: ImageDraw.Draw,
    y_mm: float,
    text: str,
    x_mm: float = None,
    max_w_mm: float = 75.0,
    font_name: str = "Arial-Bold",
    size: int = 22,
    color="black",
    wrap: bool = False,
    offset_x_mm: float = 0.0,
) -> None:
    if wrap:
        size = 8
        font = get_pil_font(font_name, size)
        lines = wrap_text_lines(
            text, x_px(max_w_mm), lambda t: draw.textlength(t, font=font)
        )
        for line in lines:
            px = (
                x_px(x_mm)
                if x_mm is not None
                else (PAGE_W_PX - draw.textlength(line, font=font)) / 2
            )
            draw.text(
                (px + x_px(offset_x_mm), y_px(PAGE_H_MM - y_mm)),
                line,
                font=font,
                fill=color,
                anchor="ls",
            )
            y_mm -= 3.0
        return

    font = get_pil_font(font_name, size)
    while size > 4 and draw.textlength(text, font=font) > x_px(max_w_mm):
        size -= 1
        font = get_pil_font(font_name, size)

    px = (
        x_px(x_mm)
        if x_mm is not None
        else (PAGE_W_PX - draw.textlength(text, font=font)) / 2
    )
    draw.text(
        (px + x_px(offset_x_mm), y_px(PAGE_H_MM - y_mm)),
        text,
        font=font,
        fill=color,
        anchor="ls",
    )


def _generate_single_stock_img(
    data: dict, order: dict, qr_code: bool, logo_img: Image, output_path: str
):
    img = Image.new("RGB", (PAGE_W_PX, PAGE_H_PX), "white")
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, y_px(30), PAGE_W_PX, y_px(40)], fill="black")

    draw_img_text(
        draw,
        PAGE_H_MM - MARGIN_MM - 2,
        data.get("date", ""),
        x_mm=MARGIN_MM,
        max_w_mm=80,
        size=10,
    )

    if logo_img:
        img.paste(logo_img, (x_px(MARGIN_MM), y_px(7)), logo_img)

    nfe = order.get("nfe", data.get("nfe_number", ""))
    draw_img_text(draw, PAGE_H_MM - 7, f"NF {nfe}", max_w_mm=85, size=13)
    draw_img_text(
        draw,
        PAGE_H_MM - 6,
        order.get("address", ""),
        x_mm=70,
        max_w_mm=15,
        font_name="Arial",
        size=5,
        wrap=True,
    )
    draw_img_text(
        draw, PAGE_H_MM - 15, str(order.get("order", "")), max_w_mm=85, size=11
    )

    if qr_code:
        qr_data = f"{order.get('code', '')};{int(order.get('qty', 0))}"
        qr = qrcode.QRCode(version=1, box_size=10, border=0)
        qr.add_data(qr_data)
        qr.make(fit=True)
        q_img = qr.make_image(fill_color="black", back_color="white").resize(
            (x_px(10), x_px(10)), Image.NEAREST
        )
        qr_x_mm = PAGE_W_MM - MARGIN_MM - 10
        img.paste(q_img, (x_px(qr_x_mm), y_px(PAGE_H_MM - 13)))

    draw_img_text(draw, PAGE_H_MM - 25, order.get("supplier", ""), max_w_mm=85, size=22)
    draw_img_text(
        draw,
        PAGE_H_MM - 37,
        order.get("code", ""),
        max_w_mm=85,
        font_name="Arial",
        size=16,
        color="white",
    )
    draw_img_text(
        draw,
        PAGE_H_MM - 45,
        order.get("description", ""),
        max_w_mm=82,
        font_name="Arial",
        size=8,
        wrap=True,
    )
    draw_img_text(
        draw,
        MARGIN_MM + 10 - MARGIN_MM,
        f"Quantidade: {int(order.get('qty', 0))} {order.get('unit_type', '')}",
        max_w_mm=85,
        font_name="Arial",
        size=10,
    )
    draw_img_text(
        draw,
        MARGIN_MM,
        f"Lote Total: {int(order.get('qty_total', 0))} {order.get('unit_type', '')}",
        max_w_mm=85,
        font_name="Arial",
        size=10,
    )

    img.save(output_path)


def _generate_single_pending_img(nfe_number: str, mat: dict, output_path: str):
    img = Image.new("RGB", (PAGE_W_PX, PAGE_H_PX), "black")
    draw = ImageDraw.Draw(img)

    draw.rectangle(
        [x_px(PAGE_W_MM - 10), y_px(MARGIN_MM), PAGE_W_PX, y_px(PAGE_H_MM - MARGIN_MM)],
        fill="white",
    )
    draw.rectangle(
        [x_px(5), y_px(PAGE_H_MM - 15), x_px(PAGE_W_MM - 15), y_px(PAGE_H_MM - 5)],
        fill="white",
    )

    draw_img_text(
        draw,
        PAGE_H_MM - 10,
        f"NF {nfe_number}",
        offset_x_mm=-5,
        max_w_mm=80,
        size=14,
        color="white",
    )
    draw_img_text(
        draw,
        PAGE_H_MM - 17,
        f"Tipo de Serviço: {mat.get('service_type', '')}",
        offset_x_mm=-5,
        size=14,
        color="white",
    )
    draw_img_text(
        draw,
        PAGE_H_MM - 28,
        mat.get("op_number", ""),
        offset_x_mm=-5,
        size=18,
        color="white",
    )
    draw_img_text(
        draw,
        PAGE_H_MM - 38,
        mat.get("product", ""),
        offset_x_mm=-5,
        font_name="Arial",
        size=18,
        color="white",
    )
    draw_img_text(
        draw,
        PAGE_H_MM - 50,
        mat.get("code", ""),
        offset_x_mm=-5,
        font_name="Arial",
        size=18,
        color="white",
    )
    draw_img_text(
        draw,
        8,
        f"QUANTIDADE: {int(mat.get('pending_qty', 0))} UND",
        offset_x_mm=-5,
        font_name="Arial",
        size=10,
        color="black",
    )

    img.save(output_path)


def _draw_single_nfe_label_pdf(pdf: Canvas, nfe_number: str, current: int, total: int):
    """Draws the exclusive NFE label on the PDF with a large centered counter."""
    pdf.setFillColor(white)
    pdf.rect(0, 0, PAGE_W_MM * mm, PAGE_H_MM * mm, stroke=0, fill=1)
    pdf.setFillColor(black)
    pdf.setStrokeColor(black)
    pdf.setLineWidth(2)
    pdf.rect(
        2 * mm, 2 * mm, (PAGE_W_MM - 4) * mm, (PAGE_H_MM - 4) * mm, stroke=1, fill=0
    )
    draw_pdf_text(pdf, PAGE_H_MM / 2 + 6, f"NF {nfe_number}", size=36)
    draw_pdf_text(pdf, PAGE_H_MM / 2 - 12, f"{current} / {total}", size=36)

    pdf.showPage()


def _generate_single_nfe_img(
    nfe_number: str, current: int, total: int, output_path: str
):
    """Generates the image of the exclusive NFE label with a large centered counter."""
    img = Image.new("RGB", (PAGE_W_PX, PAGE_H_PX), "white")
    draw = ImageDraw.Draw(img)
    draw.rectangle(
        [x_px(2), y_px(2), PAGE_W_PX - x_px(2), PAGE_H_PX - y_px(2)],
        outline="black",
        width=4,
    )
    draw_img_text(draw, PAGE_H_MM / 2 + 6, f"NF {nfe_number}", size=36, color="black")
    draw_img_text(
        draw, PAGE_H_MM / 2 - 12, f"{current} / {total}", size=36, color="black"
    )

    img.save(output_path)


# --- MAIN GENERATION LOGIC ---


def generate_pdf_document(data: dict, qr_code: bool) -> List[str]:
    """Generates a single PDF containing stock (2x) and pending (1x) labels sorted by order."""
    if not data.get("orders"):
        return []

    pdf_path = str(LABELS_FOLDER / "labels_print_job.pdf")
    pdf = Canvas(pdf_path, pagesize=(PAGE_W_MM * mm, PAGE_H_MM * mm))

    pending_materials = data.get("pending_materials", [])

    for order in data["orders"]:
        if order.get("qty", 0) > 0:
            for _ in range(2):
                _draw_single_stock_label_pdf(pdf, data, order, qr_code)

        order_code = order.get("code", "")
        nfe_str = str(order.get("nfe", data.get("nfe_number", "")))

        for mat in pending_materials:
            if mat.get("code") == order_code and mat.get("pending_qty", 0) > 0:
                _draw_single_pending_label_pdf(pdf, nfe_str, mat)

    pdf.save()
    return [pdf_path]


def generate_img_documents(data: dict, qr_code: bool) -> List[str]:
    """Generates a sequential list of PNG files for Linux printing (stock 2x, pending 1x per order)."""
    if not data.get("orders"):
        return []

    logo_img = None
    if LOGO_PATH.exists():
        logo_img = Image.open(LOGO_PATH).convert("RGBA").resize((x_px(10), x_px(10)))

    paths = []
    idx = 0
    pending_materials = data.get("pending_materials", [])

    for order in data["orders"]:
        if order.get("qty", 0) > 0:
            for _ in range(2):
                path = str(LABELS_FOLDER / f"label_job_{idx:03d}_stock.png")
                _generate_single_stock_img(data, order, qr_code, logo_img, path)
                paths.append(path)
                idx += 1

        order_code = order.get("code", "")
        nfe_str = str(order.get("nfe", data.get("nfe_number", "")))

        for mat in pending_materials:
            if mat.get("code") == order_code and mat.get("pending_qty", 0) > 0:
                path = str(LABELS_FOLDER / f"label_job_{idx:03d}_pending.png")
                _generate_single_pending_img(nfe_str, mat, path)
                paths.append(path)
                idx += 1

    return paths


def generate_manual_labels(data: dict, qr_code_mode: str) -> List[str]:
    """
    Receives a dictionary assembled by the user in the Manuals tab and
    routes to the PDF generator (Windows) or Images (Linux).
    """
    with_qr = qr_code_mode.lower() == "s"
    is_linux = platform.system().lower().startswith("linux")

    label_type = data.get("type")
    print_qty = int(data.get("print_qty", 1))

    try:
        if label_type == "stock":
            log_label_generation("Estoque Manual", print_qty)
        elif label_type == "pending":
            log_label_generation("Falta Manual", print_qty)
        elif label_type == "nfe":
            log_label_generation("NFE Manual", print_qty)
    except Exception as e:
        print(f"Failed to log manual labels: {e}")

    # --- Helper to safely handle empty floats ---
    def safe_float(val):
        try:
            return float(str(val).replace(",", "."))
        except (ValueError, TypeError):
            return 0.0

    if is_linux:
        # PNG generation (Linux)
        paths = []
        logo_img = None
        if LOGO_PATH.exists():
            logo_img = (
                Image.open(LOGO_PATH).convert("RGBA").resize((x_px(10), x_px(10)))
            )

        for i in range(print_qty):
            path = str(LABELS_FOLDER / f"manual_label_{i:03d}.png")

            if label_type == "stock":
                order_fake = {
                    "nfe": data.get("nfe", ""),
                    "address": data.get("address", ""),  # <-- CORRECTION HERE
                    "order": data.get("oc", ""),
                    "code": data.get("code", ""),
                    "description": data.get("description", ""),
                    "qty": safe_float(data.get("qty")),
                    "qty_total": safe_float(data.get("qty_total")),
                    "unit_type": data.get("unit", "un"),
                    "supplier": data.get("supplier", ""),
                }
                _generate_single_stock_img(
                    {"date": data.get("date", "")}, order_fake, with_qr, logo_img, path
                )

            elif label_type == "pending":
                mat_fake = {
                    "service_type": data.get("service_type", ""),
                    "op_number": data.get("op_number", ""),
                    "product": data.get("product", ""),
                    "code": data.get("code", ""),
                    "pending_qty": safe_float(data.get("qty")),
                }
                _generate_single_pending_img(data.get("nfe", ""), mat_fake, path)

            elif label_type == "nfe":
                _generate_single_nfe_img(data.get("nfe", ""), i + 1, print_qty, path)

            paths.append(path)
        return paths

    else:
        # PDF generation (Windows)
        pdf_path = str(LABELS_FOLDER / "manual_labels_job.pdf")
        pdf = Canvas(pdf_path, pagesize=(PAGE_W_MM * mm, PAGE_H_MM * mm))

        for i in range(print_qty):
            if label_type == "stock":
                order_fake = {
                    "nfe": data.get("nfe", ""),
                    "address": data.get("address", ""),  # <-- CORRECTION HERE
                    "order": data.get("oc", ""),
                    "code": data.get("code", ""),
                    "description": data.get("description", ""),
                    "qty": safe_float(data.get("qty")),
                    "qty_total": safe_float(data.get("qty_total")),
                    "unit_type": data.get("unit", "un"),
                    "supplier": data.get("supplier", ""),
                }
                _draw_single_stock_label_pdf(
                    pdf, {"date": data.get("date", "")}, order_fake, with_qr
                )

            elif label_type == "pending":
                mat_fake = {
                    "service_type": data.get("service_type", ""),
                    "op_number": data.get("op_number", ""),
                    "product": data.get("product", ""),
                    "code": data.get("code", ""),
                    "pending_qty": safe_float(data.get("qty")),
                }
                _draw_single_pending_label_pdf(pdf, data.get("nfe", ""), mat_fake)

            elif label_type == "nfe":
                _draw_single_nfe_label_pdf(pdf, data.get("nfe", ""), i + 1, print_qty)

        pdf.save()
        return [pdf_path]


# --- ENTRY POINT ---


def generate_nfe_labels(nfe_number: str, qr_code_mode: str) -> List[str]:
    """
    Reads the JSON file and dispatches the rendering payload.
    """
    json_path = TMP_FOLDER / f"nfe_{nfe_number}.json"

    print(f"DEBUG: Looking for JSON at: {json_path}")

    if not json_path.exists():
        print("Error: JSON file not found at the path above!")
        return []

    with open(json_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    try:
        stock_qty = 0
        pending_qty = 0
        pending_materials = data.get("pending_materials", [])

        for order in data.get("orders", []):
            if order.get("qty", 0) > 0:
                stock_qty += 2

            order_code = order.get("code", "")
            for mat in pending_materials:
                if mat.get("code") == order_code and mat.get("pending_qty", 0) > 0:
                    pending_qty += 1

        if stock_qty > 0:
            log_label_generation("Estoque NFE", stock_qty)
        if pending_qty > 0:
            log_label_generation("Falta NFE", pending_qty)
    except Exception as e:
        print(f"Failed to log NFE labels: {e}")

    with_qr = qr_code_mode.lower() == "s"
    is_linux = platform.system().lower().startswith("linux")

    if is_linux:
        print("DEBUG: Generating PNG images for Linux...")
        return generate_img_documents(data, with_qr)
    else:
        print("DEBUG: Generating PDF for Windows...")
        return generate_pdf_document(data, with_qr)


if __name__ == "__main__":
    generated = generate_nfe_labels("1327", "s")
    print(f"Files generated successfully: {len(generated)}")
    for f in generated:
        print(f" - {f}")
