from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def test_run_benchmark_cli_generates_reports(tmp_path: Path) -> None:
    input_path = Path("examples/evaluation/invoice_benchmark.json")
    db_path = tmp_path / "benchmark.db"
    artifacts_root = tmp_path / "artifacts"

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/run_benchmark.py",
            "--input",
            str(input_path),
            "--name",
            "invoice-cli-benchmark",
            "--document-type",
            "invoice",
            "--database-url",
            f"sqlite:///{db_path}",
            "--artifacts-root",
            str(artifacts_root),
        ],
        check=True,
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
        env={**os.environ, "PYTHONPATH": "src"},
    )

    payload = json.loads(completed.stdout.strip())
    assert payload["status"] == "completed"
    assert payload["documents_total"] == 2
    assert payload["overall_accuracy"] < 1.0
    assert Path(payload["report_path"]).exists()
    assert (artifacts_root / "evaluation" / "invoice-cli-benchmark" / "summary.json").exists()
