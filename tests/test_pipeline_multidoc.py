from __future__ import annotations

import json
from pathlib import Path

from fastapi import UploadFile
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from docustruct_ai.confidence.service import ConfidenceService
from docustruct_ai.config import Settings
from docustruct_ai.extraction.orchestrator import ExtractionOrchestrator
from docustruct_ai.extraction.registry import DocumentSchemaRegistry
from docustruct_ai.grounding.service import GroundingService
from docustruct_ai.ingestion.service import IngestionService
from docustruct_ai.ocr.pymupdf_adapter import PyMuPDFTextOcrAdapter
from docustruct_ai.parsing.heuristic_parser import HeuristicParser
from docustruct_ai.routing.service import RoutingService
from docustruct_ai.services.pipeline import DocumentPipelineService
from docustruct_ai.storage.adapters.local import LocalFileStorage
from docustruct_ai.validation.service import ValidationService
from docustruct_ai.vlm.stub import StubVLMBackend


def _register_font() -> str:
    if "DocuStructTestFont" in pdfmetrics.getRegisteredFontNames():
        return "DocuStructTestFont"
    candidates = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/dejavu/DejaVuSans.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            pdfmetrics.registerFont(TTFont("DocuStructTestFont", str(candidate)))
            return "DocuStructTestFont"
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


def _build_pipeline(tmp_path: Path) -> tuple[IngestionService, DocumentPipelineService]:
    source_storage = LocalFileStorage(tmp_path / "storage")
    artifact_storage = LocalFileStorage(tmp_path / "artifacts")
    registry = DocumentSchemaRegistry()
    settings = Settings(
        database_url="sqlite:///./ignored.db",
        storage_root=tmp_path / "storage",
        artifacts_root=tmp_path / "artifacts",
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
    return ingestion, pipeline


def test_pipeline_accepts_act_and_contract_documents(tmp_path: Path, db_session) -> None:
    fixtures = [
        json.loads(Path("examples/fixtures/act_demo.json").read_text(encoding="utf-8")),
        json.loads(Path("examples/fixtures/contract_demo.json").read_text(encoding="utf-8")),
    ]
    ingestion, pipeline = _build_pipeline(tmp_path)

    for payload in fixtures:
        pdf_path = tmp_path / f"{payload['document_type']}.pdf"
        _render_fixture_pdf(payload, pdf_path)
        with pdf_path.open("rb") as fh:
            upload = UploadFile(file=fh, filename=pdf_path.name)
            document, job = ingestion.create_document(db_session, upload, payload["document_type"])
            result = pipeline.run(db_session, document.id, job.id)

        assert result.route == "accepted"
        assert result.confidence >= 0.8
        if payload["document_type"] == "act":
            assert result.payload["act_number"] == payload["act_number"]
            assert result.payload["act_date"] == payload["act_date"]
            assert result.payload["seller_name"] == payload["seller"]
            assert result.payload["buyer_name"] == payload["buyer"]
            assert result.payload["currency"] == payload["currency"]
            assert result.payload["total"] == payload["total"]
        else:
            assert result.payload["contract_number"] == payload["contract_number"]
            assert result.payload["contract_date"] == payload["contract_date"]
            assert result.payload["party_a"] == payload["party_a"]
            assert result.payload["party_b"] == payload["party_b"]
            assert result.payload["currency"] == payload["currency"]
            assert result.payload["total_amount"] == payload["total_amount"]
