from __future__ import annotations

import re
from difflib import SequenceMatcher


def slugify_text(value: str) -> str:
    return re.sub(r"[^a-z0-9а-я]+", "", value.lower())


def fuzzy_similarity(left: str | None, right: str | None) -> float:
    if not left or not right:
        return 0.0
    return SequenceMatcher(a=left.lower(), b=right.lower()).ratio()
