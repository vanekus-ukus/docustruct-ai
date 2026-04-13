from __future__ import annotations

import re
from datetime import date
from decimal import Decimal, InvalidOperation

from dateutil import parser


def normalize_whitespace(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def normalize_number(value: str | float | int | Decimal | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, Decimal):
        return float(value)

    cleaned = (
        str(value)
        .replace("\u00a0", "")
        .replace(" ", "")
        .replace("₽", "")
        .replace("руб.", "")
        .replace("руб", "")
    )
    cleaned = cleaned.replace(",", ".")
    cleaned = re.sub(r"[^0-9.\-]", "", cleaned)
    if not cleaned:
        return None
    try:
        return float(Decimal(cleaned))
    except InvalidOperation:
        return None


def normalize_currency(text: str | None) -> str | None:
    if not text:
        return None
    upper = text.upper()
    if "RUB" in upper or "РУБ" in upper or "₽" in text:
        return "RUB"
    if "USD" in upper or "$" in text:
        return "USD"
    if "EUR" in upper or "€" in text:
        return "EUR"
    return None


def normalize_date(value: str | None) -> str | None:
    if not value:
        return None
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value.strip()):
        return value.strip()
    try:
        parsed = parser.parse(value, dayfirst=True, fuzzy=True)
        return parsed.date().isoformat()
    except (ValueError, TypeError, OverflowError):
        return None


def is_close(left: float | None, right: float | None, tolerance: float = 0.02) -> bool:
    if left is None or right is None:
        return False
    if right == 0:
        return abs(left - right) <= tolerance
    return abs(left - right) / max(abs(right), 1.0) <= tolerance


def today_iso() -> str:
    return date.today().isoformat()
