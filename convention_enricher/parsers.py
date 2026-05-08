from __future__ import annotations

from collections import defaultdict
from datetime import datetime
import html
import json
import re
from typing import Any

from .models import ExtractionOutput, FieldCandidate, SourceType
from .utils import clean_string


JSON_LD_PATTERN = re.compile(
    r"<script[^>]*type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>",
    flags=re.IGNORECASE | re.DOTALL,
)
META_TAG_PATTERN = re.compile(r"<meta\s+[^>]*>", flags=re.IGNORECASE)
ATTR_PATTERN = re.compile(r"([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*([\"'])(.*?)\2", flags=re.DOTALL)
OPEN_TAG_WITH_PROP_PATTERN = re.compile(
    r"<([a-zA-Z0-9:_-]+)\b[^>]*(itemprop|property)\s*=\s*([\"'])(.*?)\3[^>]*>",
    flags=re.IGNORECASE,
)

MONTH_PATTERN = (
    r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|"
    r"aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
)
AMBIGUOUS_DATE_PATTERN = re.compile(
    r"\b(tbd|to be announced|coming soon|spring\s+\d{4}|summer\s+\d{4}|autumn\s+\d{4}|fall\s+\d{4}|winter\s+\d{4})\b",
    flags=re.IGNORECASE,
)
STATUS_PATTERN = re.compile(
    r"\b(cancelled|canceled|postponed|rescheduled|on hold|sold out|coming soon|tbd)\b",
    flags=re.IGNORECASE,
)

DATE_RANGE_MONTH_DAY = re.compile(
    rf"\b({MONTH_PATTERN})\s+(\d{{1,2}})\s*[\-\u2013\u2014]\s*(\d{{1,2}}),?\s*(\d{{4}})\b",
    flags=re.IGNORECASE,
)
DATE_RANGE_MONTH_TO_MONTH = re.compile(
    rf"\b({MONTH_PATTERN})\s+(\d{{1,2}})\s*[\-\u2013\u2014]\s*({MONTH_PATTERN})\s+(\d{{1,2}}),?\s*(\d{{4}})\b",
    flags=re.IGNORECASE,
)
DATE_RANGE_DAY_MONTH = re.compile(
    rf"\b(\d{{1,2}})\s*[\-\u2013\u2014]\s*(\d{{1,2}})\s+({MONTH_PATTERN})\s+(\d{{4}})\b",
    flags=re.IGNORECASE,
)
DATE_SINGLE = re.compile(
    rf"\b({MONTH_PATTERN})\s+(\d{{1,2}}),?\s*(\d{{4}})\b",
    flags=re.IGNORECASE,
)
DATE_ISO = re.compile(r"\b(20\d{2}|19\d{2})-(\d{2})-(\d{2})\b")

MAX_PARSE_HTML_CHARS = 1_500_000
MAX_MICRODATA_SCAN_CHARS = 400_000
MAX_MICRODATA_VALUE_CHARS = 4000


def extract_candidates_from_html(html_text: str, source_url: str, source_type: SourceType) -> ExtractionOutput:
    if len(html_text) > MAX_PARSE_HTML_CHARS:
        html_text = html_text[:MAX_PARSE_HTML_CHARS]
    candidates: dict[str, list[FieldCandidate]] = defaultdict(list)
    warnings: dict[str, list[str]] = defaultdict(list)

    # Priority 1: JSON-LD Event schema.
    _extract_from_json_ld(html_text, source_url, source_type, candidates, warnings)

    # Priority 2: Microdata / RDFa.
    _extract_from_microdata_rdfa(html_text, source_url, source_type, candidates, warnings)

    # Priority 3: Open Graph + general meta tags.
    _extract_from_meta_tags(html_text, source_url, source_type, candidates, warnings)

    # Priority 4: Visible text.
    _extract_from_visible_text(html_text, source_url, source_type, candidates, warnings)

    # Priority 5: Third-party listing text (mostly search results pages).
    _extract_from_third_party_listing_text(html_text, source_url, source_type, candidates, warnings)

    return ExtractionOutput(candidates=dict(candidates), warnings=dict(warnings))


def _append_candidate(
    candidates: dict[str, list[FieldCandidate]],
    field_name: str,
    value: str,
    source_url: str,
    source_type: SourceType,
    confidence: float,
    reason: str,
    verified: bool = True,
) -> None:
    cleaned = clean_string(value)
    if not cleaned:
        return
    candidates[field_name].append(
        FieldCandidate(
            field_name=field_name,
            value=cleaned,
            source_url=source_url,
            source_type=source_type,
            confidence=confidence,
            verified=verified,
            reason=reason,
        )
    )


def _add_warning(warnings: dict[str, list[str]], field_name: str, message: str) -> None:
    if message not in warnings[field_name]:
        warnings[field_name].append(message)


def _extract_from_json_ld(
    html_text: str,
    source_url: str,
    source_type: SourceType,
    candidates: dict[str, list[FieldCandidate]],
    warnings: dict[str, list[str]],
) -> None:
    for payload in _extract_json_ld_payloads(html_text):
        for node in _walk_json(payload):
            if not isinstance(node, dict):
                continue
            if not _is_event_like(node):
                continue
            _extract_event_node(node, source_url, source_type, candidates, warnings, "JSON-LD Event schema", 1.0)


def _extract_from_microdata_rdfa(
    html_text: str,
    source_url: str,
    source_type: SourceType,
    candidates: dict[str, list[FieldCandidate]],
    warnings: dict[str, list[str]],
) -> None:
    content_props: dict[str, list[str]] = defaultdict(list)
    for tag in META_TAG_PATTERN.findall(html_text):
        attrs = _attrs_dict(tag)
        prop = clean_string(attrs.get("itemprop") or attrs.get("property"))
        content = clean_string(attrs.get("content"))
        if prop and content:
            content_props[prop].append(content)

    # Also capture non-meta tags with itemprop/property and inner text.
    scan_html = html_text[:MAX_MICRODATA_SCAN_CHARS]
    for match in OPEN_TAG_WITH_PROP_PATTERN.finditer(scan_html):
        tag_name = clean_string(match.group(1)).lower()
        prop = clean_string(match.group(4))
        if not tag_name or not prop:
            continue

        close_pattern = f"</{re.escape(tag_name)}>"
        close_match = re.search(close_pattern, scan_html[match.end() :], flags=re.IGNORECASE)
        if not close_match:
            continue

        inner_html = scan_html[match.end() : match.end() + close_match.start()]
        value = _strip_tags(inner_html[:MAX_MICRODATA_VALUE_CHARS])
        if prop and value:
            content_props[prop].append(value)

    _extract_event_node(content_props, source_url, source_type, candidates, warnings, "Microdata/RDFa", 0.88)


def _extract_from_meta_tags(
    html_text: str,
    source_url: str,
    source_type: SourceType,
    candidates: dict[str, list[FieldCandidate]],
    warnings: dict[str, list[str]],
) -> None:
    meta: dict[str, str] = {}
    for tag in META_TAG_PATTERN.findall(html_text):
        attrs = _attrs_dict(tag)
        key = clean_string(attrs.get("property") or attrs.get("name"))
        value = clean_string(attrs.get("content"))
        if key and value:
            meta[key.lower()] = value

    if "og:title" in meta:
        _append_candidate(candidates, "conName", meta["og:title"], source_url, source_type, 0.70, "Open Graph title")
    if "og:url" in meta:
        _append_candidate(candidates, "website", meta["og:url"], source_url, source_type, 0.78, "Open Graph URL")
    if "description" in meta:
        _append_candidate(candidates, "notes", meta["description"], source_url, source_type, 0.62, "Meta description")
        _extract_dates_from_snippet(meta["description"], "Open Graph/meta tags", source_url, source_type, 0.60, candidates, warnings, require_context=False)
    if "og:description" in meta:
        _append_candidate(candidates, "notes", meta["og:description"], source_url, source_type, 0.66, "Open Graph description")
        _extract_dates_from_snippet(meta["og:description"], "Open Graph/meta tags", source_url, source_type, 0.62, candidates, warnings, require_context=False)

    for key in ("description", "og:description"):
        value = meta.get(key, "")
        status = _extract_status(value)
        if status:
            _append_candidate(candidates, "status", status, source_url, source_type, 0.60, "Status inferred from meta description")


def _extract_from_visible_text(
    html_text: str,
    source_url: str,
    source_type: SourceType,
    candidates: dict[str, list[FieldCandidate]],
    warnings: dict[str, list[str]],
) -> None:
    lines = _visible_lines(html_text)
    snippet = "\n".join(lines)
    _extract_location_status_notes_from_text(
        snippet,
        "Visible page text",
        source_url,
        source_type,
        0.58,
        candidates,
    )
    _extract_dates_from_snippet(
        snippet,
        "Visible page text",
        source_url,
        source_type,
        0.56,
        candidates,
        warnings,
        require_context=True,
    )
    for line in lines:
        _extract_dates_from_snippet(
            line,
            "Visible page text",
            source_url,
            source_type,
            0.60,
            candidates,
            warnings,
            require_context=False,
        )


def _extract_from_third_party_listing_text(
    html_text: str,
    source_url: str,
    source_type: SourceType,
    candidates: dict[str, list[FieldCandidate]],
    warnings: dict[str, list[str]],
) -> None:
    if source_type != "search":
        return
    lines = _visible_lines(html_text)
    listing_lines = [line for line in lines if len(line) > 12]
    snippet = "\n".join(listing_lines)
    _extract_dates_from_snippet(
        snippet,
        "Third-party listing text",
        source_url,
        source_type,
        0.44,
        candidates,
        warnings,
        require_context=False,
    )
    for line in listing_lines:
        _extract_dates_from_snippet(
            line,
            "Third-party listing text",
            source_url,
            source_type,
            0.46,
            candidates,
            warnings,
            require_context=False,
        )
    _extract_location_status_notes_from_text(
        snippet,
        "Third-party listing text",
        source_url,
        source_type,
        0.42,
        candidates,
    )


def _extract_event_node(
    node: dict[str, Any],
    source_url: str,
    source_type: SourceType,
    candidates: dict[str, list[FieldCandidate]],
    warnings: dict[str, list[str]],
    source_label: str,
    base_confidence: float,
) -> None:
    name = _node_value(node, "name")
    if name:
        _append_candidate(candidates, "conName", name, source_url, source_type, base_confidence * 0.92, f"{source_label}: event name")

    event_url = _node_value(node, "url")
    if event_url:
        _append_candidate(candidates, "website", event_url, source_url, source_type, base_confidence * 0.98, f"{source_label}: event URL")

    status = _node_value(node, "eventStatus") or _node_value(node, "status")
    if status:
        _append_candidate(candidates, "status", status, source_url, source_type, base_confidence * 0.86, f"{source_label}: status")

    description = _node_value(node, "description")
    if description:
        _append_candidate(candidates, "notes", description, source_url, source_type, base_confidence * 0.68, f"{source_label}: description")

    # Microdata/RDFa can expose location fields as flat properties.
    flat_location = _node_value(node, "location")
    if flat_location:
        _append_candidate(candidates, "event_location", flat_location, source_url, source_type, base_confidence * 0.82, f"{source_label}: flat location")

    start = _parse_date_text(_node_value(node, "startDate"))
    end = _parse_date_text(_node_value(node, "endDate"))

    if start and start["kind"] == "exact":
        _append_candidate(candidates, "start_date", start["start"], source_url, source_type, base_confidence * 0.93, f"{source_label}: start date")
        _append_candidate(candidates, "year", start["year"], source_url, source_type, base_confidence * 0.93, f"{source_label}: year from start date")
    elif start and start["kind"] != "empty":
        _add_warning(warnings, "start_date", f"{source_label}: {start['warning']}")

    if end and end["kind"] == "exact":
        _append_candidate(candidates, "end_date", end["end"], source_url, source_type, base_confidence * 0.93, f"{source_label}: end date")
        if not start:
            _append_candidate(candidates, "year", end["year"], source_url, source_type, base_confidence * 0.90, f"{source_label}: year from end date")
    elif end and end["kind"] != "empty":
        _add_warning(warnings, "end_date", f"{source_label}: {end['warning']}")

    location = node.get("location")
    if isinstance(location, dict):
        place_name = _node_value(location, "name")
        if place_name:
            _append_candidate(candidates, "event_location", place_name, source_url, source_type, base_confidence * 0.90, f"{source_label}: venue")

        address = location.get("address")
        if isinstance(address, dict):
            city = _node_value(address, "addressLocality")
            state = _node_value(address, "addressRegion")
            country = _node_value(address, "addressCountry")
            if city:
                _append_candidate(candidates, "city", city, source_url, source_type, base_confidence * 0.85, f"{source_label}: city")
            if state:
                _append_candidate(candidates, "state", state, source_url, source_type, base_confidence * 0.84, f"{source_label}: state/province")
                upper = state.strip().upper()
                if 1 < len(upper) <= 3:
                    _append_candidate(candidates, "state_abrev", upper, source_url, source_type, base_confidence * 0.74, f"{source_label}: state abbreviation")
            if country:
                _append_candidate(candidates, "country", country, source_url, source_type, base_confidence * 0.80, f"{source_label}: country")

    # Additional flat address fields.
    root_city = _node_value(node, "addressLocality")
    root_state = _node_value(node, "addressRegion")
    root_country = _node_value(node, "addressCountry")
    if root_city:
        _append_candidate(candidates, "city", root_city, source_url, source_type, base_confidence * 0.75, f"{source_label}: flat city")
    if root_state:
        _append_candidate(candidates, "state", root_state, source_url, source_type, base_confidence * 0.75, f"{source_label}: flat state/province")
    if root_country:
        _append_candidate(candidates, "country", root_country, source_url, source_type, base_confidence * 0.75, f"{source_label}: flat country")


def _extract_dates_from_snippet(
    text: str,
    source_label: str,
    source_url: str,
    source_type: SourceType,
    confidence: float,
    candidates: dict[str, list[FieldCandidate]],
    warnings: dict[str, list[str]],
    require_context: bool,
) -> None:
    parsed = _parse_date_text(text)
    if not parsed or parsed["kind"] == "empty":
        return

    if parsed["kind"] == "vague":
        _add_warning(warnings, "start_date", f"{source_label}: {parsed['warning']}")
        _add_warning(warnings, "end_date", f"{source_label}: {parsed['warning']}")
        return

    if require_context and not _looks_event_contextual(text):
        _add_warning(
            warnings,
            "start_date",
            f"{source_label}: Date found but not clearly tied to the convention context.",
        )
        _add_warning(
            warnings,
            "end_date",
            f"{source_label}: Date found but not clearly tied to the convention context.",
        )
        return

    _append_candidate(candidates, "start_date", parsed["start"], source_url, source_type, confidence, f"{source_label}: parsed date range")
    _append_candidate(candidates, "end_date", parsed["end"], source_url, source_type, confidence, f"{source_label}: parsed date range")
    _append_candidate(candidates, "year", parsed["year"], source_url, source_type, confidence, f"{source_label}: parsed year")


def _extract_location_status_notes_from_text(
    text: str,
    source_label: str,
    source_url: str,
    source_type: SourceType,
    confidence: float,
    candidates: dict[str, list[FieldCandidate]],
) -> None:
    for line in text.splitlines():
        clean = clean_string(line)
        if not clean:
            continue

        venue_match = re.search(r"(?i)\b(?:venue|location|where)\b\s*[:\-]\s*(.+)", clean)
        if venue_match:
            _append_candidate(candidates, "event_location", venue_match.group(1), source_url, source_type, confidence, f"{source_label}: venue line")

        city_match = re.search(r"(?i)\bcity\b\s*[:\-]\s*(.+)", clean)
        if city_match:
            _append_candidate(candidates, "city", city_match.group(1), source_url, source_type, confidence * 0.98, f"{source_label}: city line")

        state_match = re.search(r"(?i)\b(?:state|province|region)\b\s*[:\-]\s*(.+)", clean)
        if state_match:
            state_value = state_match.group(1)
            _append_candidate(candidates, "state", state_value, source_url, source_type, confidence * 0.95, f"{source_label}: state/province line")
            upper = state_value.strip().upper()
            if 1 < len(upper) <= 3:
                _append_candidate(candidates, "state_abrev", upper, source_url, source_type, confidence * 0.82, f"{source_label}: state abbreviation line")

        country_match = re.search(r"(?i)\bcountry\b\s*[:\-]\s*(.+)", clean)
        if country_match:
            _append_candidate(candidates, "country", country_match.group(1), source_url, source_type, confidence * 0.95, f"{source_label}: country line")

        if any(token in clean.lower() for token in ("note:", "notes:", "update:", "important:", "announcement:")):
            _append_candidate(candidates, "notes", clean, source_url, source_type, confidence * 0.85, f"{source_label}: notes/update text")

    status = _extract_status(text)
    if status:
        _append_candidate(candidates, "status", status, source_url, source_type, confidence, f"{source_label}: status keyword")


def _extract_status(text: str) -> str:
    match = STATUS_PATTERN.search(text or "")
    if not match:
        return ""
    return match.group(1).lower()


def _parse_date_text(value: str | None) -> dict[str, str]:
    text = clean_string(value)
    if not text:
        return {"kind": "empty", "warning": ""}

    vague = AMBIGUOUS_DATE_PATTERN.search(text)
    if vague:
        return {
            "kind": "vague",
            "warning": f"Vague/ambiguous date detected ('{vague.group(1)}').",
            "start": "",
            "end": "",
            "year": "",
        }

    parsed = _parse_exact_date_range(text)
    if parsed:
        return {"kind": "exact", **parsed}

    if re.search(rf"\b{MONTH_PATTERN}\b", text, flags=re.IGNORECASE):
        return {
            "kind": "vague",
            "warning": "Date text contains month words but could not be parsed safely.",
            "start": "",
            "end": "",
            "year": "",
        }

    return {"kind": "empty", "warning": ""}


def _parse_exact_date_range(text: str) -> dict[str, str] | None:
    iso_dates = DATE_ISO.findall(text)
    if iso_dates:
        first = iso_dates[0]
        year, month, day = int(first[0]), int(first[1]), int(first[2])
        try:
            start_dt = datetime(year, month, day)
        except ValueError:
            return None
        if len(iso_dates) > 1:
            second = iso_dates[1]
            end_year, end_month, end_day = int(second[0]), int(second[1]), int(second[2])
            try:
                end_dt = datetime(end_year, end_month, end_day)
            except ValueError:
                return None
        else:
            end_dt = start_dt
        if end_dt < start_dt:
            return None
        return {
            "start": start_dt.strftime("%Y-%m-%d"),
            "end": end_dt.strftime("%Y-%m-%d"),
            "year": str(start_dt.year),
        }

    m1 = DATE_RANGE_MONTH_DAY.search(text)
    if m1:
        month, d1, d2, year = m1.groups()
        return _build_range(month, int(d1), month, int(d2), int(year))

    m2 = DATE_RANGE_MONTH_TO_MONTH.search(text)
    if m2:
        m_start, d_start, m_end, d_end, year = m2.groups()
        return _build_range(m_start, int(d_start), m_end, int(d_end), int(year))

    m3 = DATE_RANGE_DAY_MONTH.search(text)
    if m3:
        d_start, d_end, month, year = m3.groups()
        return _build_range(month, int(d_start), month, int(d_end), int(year))

    m4 = DATE_SINGLE.search(text)
    if m4:
        month, day, year = m4.groups()
        single = _build_range(month, int(day), month, int(day), int(year))
        return single

    return None


def _build_range(start_month_text: str, start_day: int, end_month_text: str, end_day: int, year: int) -> dict[str, str] | None:
    sm = _month_number(start_month_text)
    em = _month_number(end_month_text)
    if not sm or not em:
        return None
    try:
        start_dt = datetime(year, sm, start_day)
        end_dt = datetime(year, em, end_day)
    except ValueError:
        return None
    if end_dt < start_dt:
        return None
    return {
        "start": start_dt.strftime("%Y-%m-%d"),
        "end": end_dt.strftime("%Y-%m-%d"),
        "year": str(year),
    }


def _month_number(month_text: str) -> int | None:
    raw = clean_string(month_text).lower().replace(".", "")
    months = {
        "jan": 1,
        "january": 1,
        "feb": 2,
        "february": 2,
        "mar": 3,
        "march": 3,
        "apr": 4,
        "april": 4,
        "may": 5,
        "jun": 6,
        "june": 6,
        "jul": 7,
        "july": 7,
        "aug": 8,
        "august": 8,
        "sep": 9,
        "sept": 9,
        "september": 9,
        "oct": 10,
        "october": 10,
        "nov": 11,
        "november": 11,
        "dec": 12,
        "december": 12,
    }
    return months.get(raw)


def _looks_event_contextual(text: str) -> bool:
    return bool(
        re.search(
            r"(?i)\b(convention|comic|con|event|expo|festival|show|date|when|where|venue)\b",
            text,
        )
    )


def _extract_json_ld_payloads(html_text: str) -> list[Any]:
    payloads: list[Any] = []
    for raw in JSON_LD_PATTERN.findall(html_text):
        text = raw.strip()
        if not text:
            continue
        try:
            payloads.append(json.loads(text))
        except json.JSONDecodeError:
            continue
    return payloads


def _walk_json(value: Any) -> list[Any]:
    values = [value]
    if isinstance(value, dict):
        for nested in value.values():
            values.extend(_walk_json(nested))
    elif isinstance(value, list):
        for nested in value:
            values.extend(_walk_json(nested))
    return values


def _is_event_like(node: dict[str, Any]) -> bool:
    event_type = node.get("@type")
    if isinstance(event_type, str):
        return "event" in event_type.lower()
    if isinstance(event_type, list):
        return any("event" in str(item).lower() for item in event_type)
    return False


def _node_value(node: dict[str, Any], key: str) -> str:
    value = node.get(key)
    if isinstance(value, str):
        return clean_string(value)
    if isinstance(value, list):
        for item in value:
            if isinstance(item, str) and clean_string(item):
                return clean_string(item)
            if isinstance(item, dict):
                raw_item = item.get("@value")
                if isinstance(raw_item, str) and clean_string(raw_item):
                    return clean_string(raw_item)
    if isinstance(value, dict):
        # JSON-LD sometimes wraps values in {"@value": "..."}.
        raw = value.get("@value")
        if isinstance(raw, str):
            return clean_string(raw)
    return ""


def _attrs_dict(tag: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, _, value in ATTR_PATTERN.findall(tag):
        out[key.lower()] = html.unescape(value)
    return out


def _strip_tags(value: str) -> str:
    return clean_string(html.unescape(re.sub(r"<[^>]+>", " ", value)))


def _visible_lines(html_text: str) -> list[str]:
    no_scripts = re.sub(r"<script[^>]*>.*?</script>", " ", html_text, flags=re.IGNORECASE | re.DOTALL)
    no_styles = re.sub(r"<style[^>]*>.*?</style>", " ", no_scripts, flags=re.IGNORECASE | re.DOTALL)
    with_breaks = re.sub(r"</?(p|div|br|li|h[1-6]|tr|td|section|article|span)[^>]*>", "\n", no_styles, flags=re.IGNORECASE)
    no_tags = re.sub(r"<[^>]+>", " ", with_breaks)
    plain = html.unescape(no_tags)
    lines = [clean_string(line) for line in plain.splitlines()]
    return [line for line in lines if line]
