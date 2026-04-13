from __future__ import annotations

from pathlib import Path

from docustruct_ai.evaluation.service import EvaluationService
from docustruct_ai.extraction.registry import DocumentSchemaRegistry
from docustruct_ai.storage.adapters.local import LocalFileStorage


def test_evaluation_service_computes_summary(tmp_path: Path, db_session) -> None:
    service = EvaluationService(DocumentSchemaRegistry(), LocalFileStorage(tmp_path))
    run = service.run(
        db=db_session,
        name="invoice-eval",
        document_type="invoice",
        items=[
            {
                "document_id": "doc-1",
                "prediction": {"invoice_number": "INV-1", "total": 120.0},
                "ground_truth": {"invoice_number": "INV-1", "total": 120.0},
            }
        ],
    )

    assert run.summary_json["overall_accuracy"] >= 0.1
