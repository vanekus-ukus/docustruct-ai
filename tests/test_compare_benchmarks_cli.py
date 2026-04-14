from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def test_compare_benchmarks_cli_reports_delta(tmp_path: Path) -> None:
    baseline_path = tmp_path / "baseline.json"
    candidate_path = tmp_path / "candidate.json"
    baseline_path.write_text(
        json.dumps(
            {
                "name": "ocr_only",
                "document_type": "invoice",
                "overall_accuracy": 0.8,
                "field_metrics": {"invoice_number": {"accuracy": 0.5}},
            }
        ),
        encoding="utf-8",
    )
    candidate_path.write_text(
        json.dumps(
            {
                "name": "ocr_plus_vlm",
                "document_type": "invoice",
                "overall_accuracy": 0.9,
                "field_metrics": {"invoice_number": {"accuracy": 1.0}},
            }
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/compare_benchmarks.py",
            "--baseline",
            str(baseline_path),
            "--candidate",
            str(candidate_path),
        ],
        check=True,
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
        env={**os.environ, "PYTHONPATH": "src"},
    )
    payload = json.loads(completed.stdout.strip())
    assert payload["overall_accuracy"]["delta"] == 0.1
    assert payload["field_delta"]["invoice_number"]["delta_accuracy"] == 0.5
