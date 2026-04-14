from __future__ import annotations

import json
from pathlib import Path

from fastapi import UploadFile
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from sqlalchemy import select

from docustruct_ai.confidence.service import ConfidenceService
from docustruct_ai.config import Settings
from docustruct_ai.extraction.orchestrator import ExtractionOrchestrator
from docustruct_ai.extraction.registry import DocumentSchemaRegistry
from docustruct_ai.grounding.service import GroundingService
from docustruct_ai.ingestion.service import IngestionService
from docustruct_ai.models import Document, EngineRun
from docustruct_ai.ocr.pymupdf_adapter import PyMuPDFTextOcrAdapter
from docustruct_ai.parsing.heuristic_parser import HeuristicParser
from docustruct_ai.routing.service import RoutingService
from docustruct_ai.services.pipeline import DocumentPipelineService
from docustruct_ai.storage.adapters.local import LocalFileStorage
from docustruct_ai.validation.service import ValidationService
from docustruct_ai.vlm.stub import StubVLMBackend


def _register_font() -> str:
    if "DocuStructVLMFallbackFont" in pdfmetrics.getRegisteredFontNames():
        return "DocuStructVLMFallbackFont"
    candidates = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/dejavu/DejaVuSans.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            pdfmetrics.registerFont(TTFont("DocuStructVLMFallbackFont", str(candidate)))
            return "DocuStructVLMFallbackFont"
    return "Helvetica"


def _render_fixture_pdf(payload: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    font_name = _register_font()
    pdf = canvas.Canvas(str(output_path), pagesize=A4)
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
    pdf.showPage()
    pdf.save()


def test_pipeline_uses_vlm_fallback_candidate_for_missing_required_field(tmp_path: Path, db_session) -> None:
    payload = json.loads(Path("examples/fixtures/noisy_invoice.json").read_text(encoding="utf-8"))
    pdf_path = tmp_path / "noisy_invoice.pdf"
    _render_fixture_pdf(payload, pdf_path)

    source_storage = LocalFileStorage(tmp_path / "storage")
    artifact_storage = LocalFileStorage(tmp_path / "artifacts")
    registry = DocumentSchemaRegistry()
    settings = Settings(
        database_url="sqlite:///./ignored.db",
        storage_root=tmp_path / "storage",
        artifacts_root=tmp_path / "artifacts",
        execution_mode="inline",
        enable_vlm_fallback=True,
        vlm_fallback_quality_threshold=0.95,
        vlm_fallback_missing_required_threshold=1,
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

    with pdf_path.open("rb") as fh:
        upload = UploadFile(file=fh, filename=pdf_path.name)
        document, job = ingestion.create_document(
            db_session,
            file=upload,
            document_type="invoice",
            external_id="vlm-fallback-invoice",
        )

    document.metadata_json = {
        **document.metadata_json,
        "vlm_candidate": {"invoice_number": "INV-VLM-001"},
    }
    db_session.add(document)
    db_session.commit()

    result = pipeline.run(db_session, document_id=document.id, job_id=job.id)
    refreshed = db_session.execute(select(Document).where(Document.id == document.id)).scalar_one()
    vlm_run = db_session.execute(
        select(EngineRun)
        .where(EngineRun.document_id == document.id)
        .where(EngineRun.engine_type == "vlm")
    ).scalar_one()

    assert result.payload["invoice_number"] == "INV-VLM-001"
    assert result.metadata["vlm_fallback_used"] is True
    assert "missing_required_fields" in result.metadata["vlm_trigger_reasons"]
    assert refreshed.routing_state == "needs_review"
    assert refreshed.metadata_json["routing_reasons"]
    assert vlm_run.status == "used"
