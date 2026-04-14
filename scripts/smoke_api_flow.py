from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import UploadFile
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from sqlalchemy import select

os.environ.setdefault("DATABASE_URL", "sqlite:///./smoke_api.db")
os.environ.setdefault("STORAGE_ROOT", "./smoke_api_data/storage")
os.environ.setdefault("ARTIFACTS_ROOT", "./smoke_api_data/artifacts")
os.environ.setdefault("EXECUTION_MODE", "inline")

from docustruct_ai.api.routes.documents import get_document_result, upload_document
from docustruct_ai.api.routes.review import submit_review_task
from docustruct_ai.api.schemas import ReviewSubmitRequest
from docustruct_ai.confidence.service import ConfidenceService
from docustruct_ai.config import Settings
from docustruct_ai.db.base import Base
from docustruct_ai.db.session import SessionLocal, engine
from docustruct_ai.extraction.orchestrator import ExtractionOrchestrator
from docustruct_ai.extraction.registry import DocumentSchemaRegistry
from docustruct_ai.grounding.service import GroundingService
from docustruct_ai.ingestion.service import IngestionService
from docustruct_ai.models import Document, ReviewTask
from docustruct_ai.ocr.pymupdf_adapter import PyMuPDFTextOcrAdapter
from docustruct_ai.parsing.heuristic_parser import HeuristicParser
from docustruct_ai.review.service import ReviewService
from docustruct_ai.routing.service import RoutingService
from docustruct_ai.services.documents import DocumentQueryService
from docustruct_ai.services.pipeline import DocumentPipelineService
from docustruct_ai.storage.adapters.local import LocalFileStorage
from docustruct_ai.validation.service import ValidationService
from docustruct_ai.vlm.stub import StubVLMBackend


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "examples" / "fixtures"
GENERATED = ROOT / "examples" / "generated_api"


def register_font() -> str:
    if "DocuStructApiSmokeFont" in pdfmetrics.getRegisteredFontNames():
        return "DocuStructApiSmokeFont"
    candidates = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/dejavu/DejaVuSans.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            pdfmetrics.registerFont(TTFont("DocuStructApiSmokeFont", str(candidate)))
            return "DocuStructApiSmokeFont"
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


def build_services(base_dir: Path) -> tuple[IngestionService, DocumentPipelineService, ReviewService, DocumentQueryService]:
    source_storage = LocalFileStorage(base_dir / "storage")
    artifact_storage = LocalFileStorage(base_dir / "artifacts")
    registry = DocumentSchemaRegistry()
    settings = Settings(
        database_url=os.environ["DATABASE_URL"],
        storage_root=base_dir / "storage",
        artifacts_root=base_dir / "artifacts",
        execution_mode="inline",
    )
    ingestion = IngestionService(source_storage)
    pipeline = DocumentPipelineService(
        settings=settings,
        artifact_storage=artifact_storage,
        parser=HeuristicParser(),
        ocr_backend=PyMuPDFTextOcrAdapter(),
        vlm_backend=StubVLMBackend(),
        extractor=ExtractionOrchestrator(registry),
        registry=registry,
        grounding_service=GroundingService(),
        validation_service=ValidationService(registry),
        confidence_service=ConfidenceService(),
        routing_service=RoutingService(settings),
    )
    review = ReviewService(settings)
    query = DocumentQueryService()
    return ingestion, pipeline, review, query


def main() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        ingestion, pipeline, review, query = build_services(ROOT / "smoke_api_data")
        for fixture_path in [FIXTURES / "invoice_demo.json", FIXTURES / "noisy_invoice.json"]:
            payload = json.loads(fixture_path.read_text(encoding="utf-8"))
            pdf_path = GENERATED / f"{fixture_path.stem}.pdf"
            render_fixture_pdf(payload, pdf_path)
            with pdf_path.open("rb") as fh:
                upload = UploadFile(file=fh, filename=pdf_path.name)
                upload_response = upload_document(
                    file=upload,
                    document_type=payload["document_type"],
                    external_id=fixture_path.stem,
                    db=db,
                    ingestion_service=ingestion,
                    pipeline_service=pipeline,
                )

            document = db.execute(select(Document).where(Document.id == upload_response.document_id)).scalar_one()
            tasks = db.execute(select(ReviewTask).where(ReviewTask.document_id == document.id)).scalars().all()
            if tasks:
                for task in tasks:
                    submit_review_task(
                        task_id=task.id,
                        payload=ReviewSubmitRequest(
                            decision="edit" if task.field_id is not None else "accept",
                            final_value="INV-2024-ERR" if task.field_id is not None else None,
                            reviewer="smoke@example.com",
                            comment="Smoke API flow",
                        ),
                        db=db,
                        review_service=review,
                    )
            result = get_document_result(document.id, db=db, query_service=query)
            print(
                json.dumps(
                    {
                        "fixture": fixture_path.name,
                        "status": document.status,
                        "route": result.route,
                        "confidence": result.confidence,
                        "review_tasks": len(tasks),
                    },
                    ensure_ascii=False,
                )
            )
    finally:
        db.close()


if __name__ == "__main__":
    main()
