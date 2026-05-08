from __future__ import annotations

from datetime import datetime
import re
from urllib.parse import urlparse

from .utils import clean_string


MISSING_TOKENS = {"", "n/a", "na", "none", "null", "unknown", "tbd", "tba", "-", "--", "**"}


def is_missing(value: str | None) -> bool:
    if value is None:
        return True
    return clean_string(value).lower() in MISSING_TOKENS


def normalize_for_compare(value: str) -> str:
    return re.sub(r"\s+", " ", clean_string(value).lower())


def normalize_url(value: str | None) -> str:
    text = clean_string(value)
    if not text:
        return ""
    if not text.startswith(("http://", "https://")):
        text = f"https://{text}"
    parsed = urlparse(text)
    if not parsed.netloc:
        return ""
    return text


def parse_year(value: str | None) -> int | None:
    text = clean_string(value)
    if not text:
        return None
    match = re.search(r"\b(19|20)\d{2}\b", text)
    if not match:
        return None
    return int(match.group(0))


def parse_datetime(value: str | None) -> datetime | None:
    text = clean_string(value)
    if not text:
        return None

    normalized = text.replace("Z", "+00:00")
    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%m/%d/%Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
    ]
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        pass

    for fmt in formats:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def format_month_day(value: datetime) -> str:
    return value.strftime("%B %d").replace(" 0", " ")


def normalize_field_value(field_name: str, value: str) -> str:
    text = clean_string(value)
    if not text:
        return ""
    if field_name == "website":
        return normalize_url(text)
    if field_name == "year":
        year = parse_year(text)
        return str(year) if year else ""
    if field_name == "status":
        # JSON-LD eventStatus is often a URL, e.g. https://schema.org/EventCancelled.
        lowered = text.lower().rstrip("/")
        if "/" in lowered:
            lowered = lowered.rsplit("/", 1)[-1]
        return re.sub(r"[^a-z0-9]+", "_", lowered).strip("_")
    if field_name in {"event_location", "city", "state", "country"}:
        return re.sub(r"\s+", " ", text).strip(" ,;")
    if field_name == "state_abrev":
        return text.upper()
    return text
