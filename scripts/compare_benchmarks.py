from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Сравнение двух benchmark summary файлов")
    parser.add_argument("--baseline", required=True, help="Путь к baseline summary.json")
    parser.add_argument("--candidate", required=True, help="Путь к candidate summary.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    baseline = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    candidate = json.loads(Path(args.candidate).read_text(encoding="utf-8"))

    field_delta: dict[str, dict[str, float]] = {}
    all_fields = sorted(set(baseline.get("field_metrics", {})) | set(candidate.get("field_metrics", {})))
    for field_name in all_fields:
        base_metric = baseline.get("field_metrics", {}).get(field_name, {})
        cand_metric = candidate.get("field_metrics", {}).get(field_name, {})
        field_delta[field_name] = {
            "baseline_accuracy": round(float(base_metric.get("accuracy", 0.0)), 4),
            "candidate_accuracy": round(float(cand_metric.get("accuracy", 0.0)), 4),
            "delta_accuracy": round(
                float(cand_metric.get("accuracy", 0.0)) - float(base_metric.get("accuracy", 0.0)),
                4,
            ),
        }

    result = {
        "baseline_name": baseline.get("name"),
        "candidate_name": candidate.get("name"),
        "document_type": candidate.get("document_type") or baseline.get("document_type"),
        "overall_accuracy": {
            "baseline": round(float(baseline.get("overall_accuracy", 0.0)), 4),
            "candidate": round(float(candidate.get("overall_accuracy", 0.0)), 4),
            "delta": round(
                float(candidate.get("overall_accuracy", 0.0)) - float(baseline.get("overall_accuracy", 0.0)),
                4,
            ),
        },
        "field_delta": field_delta,
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
