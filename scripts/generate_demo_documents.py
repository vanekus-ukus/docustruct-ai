from __future__ import annotations

import json
from pathlib import Path

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
except Exception as exc:  # pragma: no cover
    raise SystemExit("Для генерации demo документов установите зависимости .[dev] с reportlab") from exc


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "examples" / "fixtures"
OUTPUT = ROOT / "examples" / "generated"


def register_font() -> str:
    if "DocuStructFont" in pdfmetrics.getRegisteredFontNames():
        return "DocuStructFont"
    candidates = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/dejavu/DejaVuSans.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            pdfmetrics.registerFont(TTFont("DocuStructFont", str(candidate)))
            return "DocuStructFont"
    return "Helvetica"


def draw_invoice(pdf: canvas.Canvas, payload: dict) -> None:
    font_name = register_font()
    pdf.setTitle(payload["title"])
    pdf.setFont(font_name, 16)
    pdf.drawString(40, 800, payload["title"])
    pdf.setFont(font_name, 11)
    pdf.drawString(40, 770, f"Поставщик: {payload['seller']}")
    pdf.drawString(40, 750, f"Покупатель: {payload['buyer']}")
    pdf.drawString(40, 730, f"Дата счета: {payload['invoice_date']}")
    pdf.drawString(40, 710, f"Срок оплаты: {payload.get('due_date', '')}")
    pdf.drawString(40, 690, f"Валюта: {payload['currency']}")
    y = 650
    pdf.drawString(40, y, "№  Описание              Кол-во   Цена      Сумма")
    y -= 20
    for idx, item in enumerate(payload["line_items"], start=1):
        pdf.drawString(
            40,
            y,
            f"{idx}  {item['description']}  {item['quantity']}  {item['unit_price']:.2f}  {item['total']:.2f}",
        )
        y -= 18
    pdf.drawString(40, y - 10, f"Подытог: {payload['subtotal']:.2f}")
    pdf.drawString(40, y - 30, f"НДС: {payload['tax']:.2f}")
    pdf.drawString(40, y - 50, f"Итого к оплате: {payload['total']:.2f}")


def draw_act(pdf: canvas.Canvas, payload: dict) -> None:
    font_name = register_font()
    pdf.setTitle(payload["title"])
    pdf.setFont(font_name, 16)
    pdf.drawString(40, 800, payload["title"])
    pdf.setFont(font_name, 11)
    pdf.drawString(40, 770, f"Исполнитель: {payload['seller']}")
    pdf.drawString(40, 750, f"Заказчик: {payload['buyer']}")
    pdf.drawString(40, 730, f"Дата: {payload['act_date']}")
    pdf.drawString(40, 710, f"Итого: {payload['total']:.2f} {payload['currency']}")


def draw_contract(pdf: canvas.Canvas, payload: dict) -> None:
    font_name = register_font()
    pdf.setTitle(payload["title"])
    pdf.setFont(font_name, 16)
    pdf.drawString(40, 800, payload["title"])
    pdf.setFont(font_name, 11)
    pdf.drawString(40, 770, f"Сторона А: {payload['party_a']}")
    pdf.drawString(40, 750, f"Сторона Б: {payload['party_b']}")
    pdf.drawString(40, 730, f"Дата договора: {payload['contract_date']}")
    pdf.drawString(40, 710, f"Общая сумма: {payload['total_amount']:.2f} {payload['currency']}")


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for fixture_path in FIXTURES.glob("*.json"):
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        output_path = OUTPUT / f"{fixture_path.stem}.pdf"
        pdf = canvas.Canvas(str(output_path), pagesize=A4)
        if payload["document_type"] == "invoice":
            draw_invoice(pdf, payload)
        elif payload["document_type"] == "act":
            draw_act(pdf, payload)
        else:
            draw_contract(pdf, payload)
        pdf.showPage()
        pdf.save()
        print(f"generated {output_path}")


if __name__ == "__main__":
    main()
