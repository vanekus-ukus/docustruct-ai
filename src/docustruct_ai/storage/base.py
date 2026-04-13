from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class ArtifactStorage(ABC):
    @abstractmethod
    def save_bytes(self, relative_path: str, content: bytes) -> str:
        """Save bytes and return absolute path."""

    @abstractmethod
    def save_json(self, relative_path: str, payload: dict[str, Any]) -> str:
        """Save JSON-like payload and return absolute path."""

    @abstractmethod
    def read_text(self, absolute_path: str) -> str:
        """Read text from storage."""

    @abstractmethod
    def ensure_dir(self, relative_path: str) -> Path:
        """Ensure subdirectory exists."""
