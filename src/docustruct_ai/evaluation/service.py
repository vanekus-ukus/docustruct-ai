from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from docustruct_ai.evaluation.types import EvaluationSummary
from docustruct_ai.extraction.registry import DocumentSchemaRegistry
from docustruct_ai.models import EvaluationRun
from docustruct_ai.storage.base import ArtifactStorage
from docustruct_ai.utils.normalization import is_close, normalize_date, normalize_number
from docustruct_ai.utils.text import fuzzy_similarity


class EvaluationService:
    def __init__(self, registry: DocumentSchemaRegistry, artifact_storage: ArtifactStorage) -> None:
        self.registry = registry
        self.artifact_storage = artifact_storage

    def run(
        self,
        db: Session,
        name: str,
        document_type: str,
        items: list[dict[str, Any]],
    ) -> EvaluationRun:
        schema = self.registry.get(document_type)
        field_map = schema.field_map()
        totals = defaultdict(lambda: {"correct": 0, "total": 0, "omission": 0, "hallucination": 0})

        for item in items:
            prediction = item["prediction"]
            ground_truth = item["ground_truth"]
            for field_name, field_def in field_map.items():
                pred = prediction.get(field_name)
                truth = ground_truth.get(field_name)
                totals[field_name]["total"] += 1
                if truth in (None, "", []) and pred not in (None, "", []):
                    totals[field_name]["hallucination"] += 1
                elif truth not in (None, "", []) and pred in (None, "", []):
                    totals[field_name]["omission"] += 1
                elif self._compare(field_def.scoring_type, pred, truth):
                    totals[field_name]["correct"] += 1

        summary = {
            "name": name,
            "document_type": document_type,
            "field_metrics": {},
            "documents_total": len(items),
        }
        overall_correct = 0
        overall_total = 0
        for field_name, metrics in totals.items():
            accuracy = (metrics["correct"] / metrics["total"]) if metrics["total"] else 0.0
            summary["field_metrics"][field_name] = {
                **metrics,
                "accuracy": round(accuracy, 4),
            }
            overall_correct += metrics["correct"]
            overall_total += metrics["total"]
        summary["overall_accuracy"] = round((overall_correct / overall_total), 4) if overall_total else 0.0

        report_md = self._build_markdown(summary)
        base_path = f"evaluation/{name}"
        json_path = self.artifact_storage.save_json(f"{base_path}/summary.json", summary)
        md_path = Path(self.artifact_storage.save_bytes(f"{base_path}/summary.md", report_md.encode("utf-8")))

        run = EvaluationRun(
            name=name,
            status="completed",
            document_type=document_type,
            summary_json=summary,
            report_path=str(md_path),
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    def _compare(self, scoring_type: str, prediction: Any, truth: Any) -> bool:
        if scoring_type == "numeric_tolerance":
            return is_close(normalize_number(prediction), normalize_number(truth), tolerance=0.03)
        if scoring_type == "date_equivalence":
            return normalize_date(str(prediction)) == normalize_date(str(truth))
        if scoring_type == "fuzzy_text":
            return fuzzy_similarity(str(prediction or ""), str(truth or "")) >= 0.9
        if scoring_type == "array_match":
            return prediction == truth
        return prediction == truth

    def _build_markdown(self, summary: dict[str, Any]) -> str:
        lines = [
            f"# Evaluation report: {summary['name']}",
            "",
            f"- Тип документа: `{summary['document_type']}`",
            f"- Количество документов: `{summary['documents_total']}`",
            f"- Общая accuracy: `{summary['overall_accuracy']}`",
            "",
            "## Метрики по полям",
            "",
            "| Поле | Accuracy | Correct | Total | Omission | Hallucination |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for field_name, metrics in summary["field_metrics"].items():
            lines.append(
                f"| {field_name} | {metrics['accuracy']} | {metrics['correct']} | {metrics['total']} | {metrics['omission']} | {metrics['hallucination']} |"
            )
        return "\n".join(lines)
