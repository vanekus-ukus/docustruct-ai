from __future__ import annotations

import json
from pathlib import Path

from fastapi import UploadFile
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from sqlalchemy import select

from docustruct_ai.api.routes.documents import (
    get_document,
    get_document_result,
    get_document_status,
    upload_document,
)
from docustruct_ai.api.routes.review import submit_review_task
from docustruct_ai.api.schemas import ReviewSubmitRequest
from docustruct_ai.confidence.service import ConfidenceService
from docustruct_ai.config import Settings
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


def _register_font() -> str:
    if "DocuStructApiFont" in pdfmetrics.getRegisteredFontNames():
        return "DocuStructApiFont"
    candidates = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/dejavu/DejaVuSans.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            pdfmetrics.registerFont(TTFont("DocuStructApiFont", str(candidate)))
            return "DocuStructApiFont"
    return "Helvetica"


def _render_fixture_pdf(payload: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    font_name = _register_font()
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


def _build_services(tmp_path: Path) -> tuple[IngestionService, DocumentPipelineService, ReviewService, DocumentQueryService]:
    source_storage = LocalFileStorage(tmp_path / "storage")
    artifact_storage = LocalFileStorage(tmp_path / "artifacts")
    registry = DocumentSchemaRegistry()
    settings = Settings(
        database_url="sqlite:///./ignored.db",
        storage_root=tmp_path / "storage",
        artifacts_root=tmp_path / "artifacts",
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


def test_api_route_flow_upload_to_result(tmp_path: Path, db_session) -> None:
    payload = json.loads(Path("examples/fixtures/invoice_demo.json").read_text(encoding="utf-8"))
    pdf_path = tmp_path / "invoice_demo.pdf"
    _render_fixture_pdf(payload, pdf_path)
    ingestion, pipeline, _, query = _build_services(tmp_path)

    with pdf_path.open("rb") as fh:
        upload = UploadFile(file=fh, filename=pdf_path.name)
        upload_response = upload_document(
            file=upload,
            document_type="invoice",
            external_id="api-invoice-001",
            db=db_session,
            ingestion_service=ingestion,
            pipeline_service=pipeline,
        )

    document_response = get_document(upload_response.document_id, db=db_session, query_service=query)
    status_response = get_document_status(upload_response.document_id, db=db_session, query_service=query)
    result_response = get_document_result(upload_response.document_id, db=db_session, query_service=query)

    assert upload_response.status == "completed"
    assert document_response.document_type == "invoice"
    assert document_response.routing_state == "accepted"
    assert status_response.status == "processed"
    assert result_response.route == "accepted"
    assert result_response.payload["invoice_number"] == payload["invoice_number"]
    assert result_response.payload["supplier_name"] == payload["seller"]


def test_api_route_flow_review_submit(tmp_path: Path, db_session) -> None:
    payload = json.loads(Path("examples/fixtures/noisy_invoice.json").read_text(encoding="utf-8"))
    pdf_path = tmp_path / "noisy_invoice.pdf"
    _render_fixture_pdf(payload, pdf_path)
    ingestion, pipeline, review_service, query = _build_services(tmp_path)

    with pdf_path.open("rb") as fh:
        upload = UploadFile(file=fh, filename=pdf_path.name)
        upload_response = upload_document(
            file=upload,
            document_type="invoice",
            external_id="api-noisy-invoice-001",
            db=db_session,
            ingestion_service=ingestion,
            pipeline_service=pipeline,
        )

    document_model = db_session.execute(
        select(Document).where(Document.id == upload_response.document_id)
    ).scalar_one()
    tasks = db_session.execute(
        select(ReviewTask).where(ReviewTask.document_id == document_model.id).order_by(ReviewTask.id)
    ).scalars().all()
    assert tasks
    assert document_model.routing_state == "needs_review"

    for task in tasks:
        request = ReviewSubmitRequest(
            decision="edit" if task.field_id is not None else "accept",
            final_value="INV-2024-ERR" if task.field_id is not None else None,
            reviewer="qa@example.com",
            comment="API route flow review",
        )
        response = submit_review_task(
            task_id=task.id,
            payload=request,
            db=db_session,
            review_service=review_service,
        )
        assert response.status == "completed"

    refreshed = db_session.execute(select(Document).where(Document.id == document_model.id)).scalar_one()
    result_response = get_document_result(refreshed.id, db=db_session, query_service=query)
    assert refreshed.status == "reviewed"
    assert refreshed.routing_state == "accepted"
    assert result_response.payload["invoice_number"] == "INV-2024-ERR"
