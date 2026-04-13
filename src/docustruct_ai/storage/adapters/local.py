from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from docustruct_ai.storage.base import ArtifactStorage


class LocalFileStorage(ArtifactStorage):
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def save_bytes(self, relative_path: str, content: bytes) -> str:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return str(path.resolve())

    def save_json(self, relative_path: str, payload: dict[str, Any]) -> str:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(path.resolve())

    def read_text(self, absolute_path: str) -> str:
        return Path(absolute_path).read_text(encoding="utf-8")

    def ensure_dir(self, relative_path: str) -> Path:
        path = self.root / relative_path
        path.mkdir(parents=True, exist_ok=True)
        return path
