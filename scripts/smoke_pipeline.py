from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import UploadFile
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

os.environ.setdefault("DATABASE_URL", "sqlite:///./smoke.db")
os.environ.setdefault("STORAGE_ROOT", "./smoke_data/storage")
os.environ.setdefault("ARTIFACTS_ROOT", "./smoke_data/artifacts")
os.environ.setdefault("EXECUTION_MODE", "inline")

from docustruct_ai.db.base import Base
from docustruct_ai.db.session import SessionLocal, engine
from docustruct_ai.models import ReviewTask
from docustruct_ai.services.factory import get_ingestion_service, get_pipeline_service


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "examples" / "fixtures"
GENERATED = ROOT / "examples" / "generated"


def register_font() -> str:
    if "DocuStructSmokeFont" in pdfmetrics.getRegisteredFontNames():
        return "DocuStructSmokeFont"
    candidates = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/dejavu/DejaVuSans.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            pdfmetrics.registerFont(TTFont("DocuStructSmokeFont", str(candidate)))
            return "DocuStructSmokeFont"
    return "Helvetica"


def render_fixture_pdf(payload: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    font_name = register_font()
    pdf = canvas.Canvas(str(output_path), pagesize=A4)
    pdf.setTitle(payload["title"])
    pdf.setFont(font_name, 16)
    pdf.drawString(40, 800, payload["title"])
    pdf.setFont(font_name, 11)

    if payload["document_type"] == "invoice":
        pdf.drawString(40, 770, f"Поставщик: {payload['seller']}")
        pdf.drawString(40, 750, f"Покупатель: {payload['buyer']}")
        pdf.drawString(40, 730, f"Дата счета: {payload['invoice_date']}")
        pdf.drawString(40, 710, f"Срок оплаты: {payload.get('due_date', '')}")
        pdf.drawString(40, 690, f"Валюта: {payload['currency']}")
        y = 650
        pdf.drawString(40, y, "№  Описание              Кол-во   Цена      Сумма")
        y -= 20
        for idx, item in enumerate(payload.get("line_items", []), start=1):
            pdf.drawString(
                40,
                y,
                f"{idx}  {item['description']}  {item['quantity']}  {item['unit_price']:.2f}  {item['total']:.2f}",
            )
            y -= 18
        pdf.drawString(40, y - 10, f"Подытог: {payload['subtotal']:.2f}")
        pdf.drawString(40, y - 30, f"НДС: {payload.get('tax', 0):.2f}")
        pdf.drawString(40, y - 50, f"Итого к оплате: {payload['total']:.2f}")
    elif payload["document_type"] == "act":
        pdf.drawString(40, 770, f"Исполнитель: {payload['seller']}")
        pdf.drawString(40, 750, f"Заказчик: {payload['buyer']}")
        pdf.drawString(40, 730, f"Дата: {payload['act_date']}")
        pdf.drawString(40, 710, f"Итого: {payload['total']:.2f} {payload['currency']}")
    else:
        pdf.drawString(40, 770, f"Сторона А: {payload['party_a']}")
        pdf.drawString(40, 750, f"Сторона Б: {payload['party_b']}")
        pdf.drawString(40, 730, f"Дата договора: {payload['contract_date']}")
        pdf.drawString(40, 710, f"Общая сумма: {payload['total_amount']:.2f} {payload['currency']}")
    pdf.showPage()
    pdf.save()


def main() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    GENERATED.mkdir(parents=True, exist_ok=True)
    db = SessionLocal()
    try:
        ingestion = get_ingestion_service()
        pipeline = get_pipeline_service()
        for fixture_path in sorted(FIXTURES.glob("*.json")):
            payload = json.loads(fixture_path.read_text(encoding="utf-8"))
            pdf_path = GENERATED / f"{fixture_path.stem}.pdf"
            render_fixture_pdf(payload, pdf_path)
            with pdf_path.open("rb") as fh:
                upload = UploadFile(file=fh, filename=pdf_path.name)
                document, job = ingestion.create_document(db, upload, payload["document_type"])
                result = pipeline.run(db, document.id, job.id)
            review_count = db.query(ReviewTask).filter(ReviewTask.document_id == document.id).count()
            print(
                json.dumps(
                    {
                        "fixture": fixture_path.name,
                        "document_type": payload["document_type"],
                        "route": result.route,
                        "confidence": result.confidence,
                        "review_tasks": review_count,
                    },
                    ensure_ascii=False,
                )
            )
    finally:
        db.close()


if __name__ == "__main__":
    main()
