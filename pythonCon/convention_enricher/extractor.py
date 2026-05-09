from __future__ import annotations

import json
import html
import re
from typing import Iterable

from .crawler import CrawledDocument
from .models import ExtractionLayer, ExtractionResult, FieldEvidence, SourceRole
from .utils import clean_source_text


META_PATTERN = re.compile(r"<meta\s+[^>]*>", flags=re.IGNORECASE)
LINK_PATTERN = re.compile(r"<link\s+[^>]*>", flags=re.IGNORECASE)
ATTR_PATTERN = re.compile(r"([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*([\"'])(.*?)\2", flags=re.DOTALL)
TAG_CAPTURE_TEMPLATE = r"<{tag}[^>]*>(.*?)</{tag}>"

DATE_PATTERNS = [
    re.compile(
        r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|"
        r"Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:,\s*\d{4})?"
        r"(?:\s*(?:-|\u2013|to)\s*(?:\d{1,2}|(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
        r"Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2})(?:,\s*\d{4})?)?\b",
        flags=re.IGNORECASE,
    ),
    re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}(?:\s*(?:-|\u2013|to)\s*\d{1,2}/\d{1,2}/\d{2,4})?\b"),
    re.compile(r"\b\d{4}-\d{2}-\d{2}(?:\s*(?:-|\u2013|to)\s*\d{4}-\d{2}-\d{2})?\b"),
]

LABEL_PATTERNS = {
    "event_location": re.compile(r"\b(?:venue|location|where)\b\s*[:\-]\s*(.+)", flags=re.IGNORECASE),
    "city": re.compile(r"\bcity\b\s*[:\-]\s*(.+)", flags=re.IGNORECASE),
    "state": re.compile(r"\b(?:state|province|region)\b\s*[:\-]\s*(.+)", flags=re.IGNORECASE),
    "country": re.compile(r"\bcountry\b\s*[:\-]\s*(.+)", flags=re.IGNORECASE),
    "event_date": re.compile(r"\b(?:date|dates|when|event\s*date|schedule)\b\s*[:\-]\s*(.+)", flags=re.IGNORECASE),
}

JSONLD_PATTERN = re.compile(
    r"<script[^>]*type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>",
    flags=re.IGNORECASE | re.DOTALL,
)


def extract_from_document(document: CrawledDocument, convention_name: str) -> ExtractionResult:
    result = ExtractionResult()
    combined_blobs: list[str] = []

    _extract_priority_meta(document, convention_name, result, combined_blobs)
    _extract_priority_visible(document, convention_name, result, combined_blobs)
    _extract_priority_semantic(document, convention_name, result, combined_blobs)
    _extract_combined_date_blob(document, convention_name, result, combined_blobs)
    _extract_priority_structured(document, convention_name, result)

    return result


def _extract_priority_meta(
    document: CrawledDocument,
    convention_name: str,
    result: ExtractionResult,
    combined_blobs: list[str],
) -> None:
    html = document.html
    title = _capture_tag_content(html, "title")
    if title:
        _add(result, "convention_name", title, document, "meta", "title", "MEDIUM")

    meta_values: dict[str, str] = {}
    for tag in META_PATTERN.findall(html):
        attrs = _attrs(tag)
        key = clean_source_text(attrs.get("property") or attrs.get("name") or "").lower()
        value = clean_source_text(attrs.get("content") or "")
        if key and value:
            meta_values[key] = value
            combined_blobs.append(value)

    for key in ("og:title", "twitter:title"):
        if key in meta_values:
            _add(result, "convention_name", meta_values[key], document, "meta", key, "MEDIUM")

    for key in ("description", "og:description", "twitter:description"):
        if key in meta_values:
            _extract_date_from_text(
                text=meta_values[key],
                document=document,
                layer="meta",
                selector_hint=key,
                convention_name=convention_name,
                result=result,
            )
            _extract_labeled_location_fields(meta_values[key], document, "meta", key, result)

    if "og:url" in meta_values:
        _add(result, "website_url", meta_values["og:url"], document, "meta", "og:url", "HIGH", 0.95)

    canonical = _extract_canonical_link(html)
    if canonical:
        _add(result, "website_url", canonical, document, "meta", "link[rel=canonical]", "HIGH", 1.0)


def _extract_priority_visible(
    document: CrawledDocument,
    convention_name: str,
    result: ExtractionResult,
    combined_blobs: list[str],
) -> None:
    blocks: list[tuple[str, str]] = []
    for tag in ("h1", "h2", "h3"):
        for item in _capture_all_tag_content(document.html, tag):
            blocks.append((tag, item))

    lines = _visible_lines(document.html)
    for idx, line in enumerate(lines[:600]):
        blocks.append((f"line:{idx}", line))
        combined_blobs.append(line)

    for selector, text in blocks:
        if selector.startswith("h1"):
            _add(result, "convention_name", text, document, "visible", selector, "MEDIUM")

        _extract_labeled_location_fields(text, document, "visible", selector, result)
        _extract_date_from_text(
            text=text,
            document=document,
            layer="visible",
            selector_hint=selector,
            convention_name=convention_name,
            result=result,
        )


def _extract_priority_semantic(
    document: CrawledDocument,
    convention_name: str,
    result: ExtractionResult,
    combined_blobs: list[str],
) -> None:
    semantic_blocks = []
    semantic_blocks.extend(_capture_all_tag_content(document.html, "address"))
    semantic_blocks.extend(_capture_all_tag_content(document.html, "time"))
    semantic_blocks.extend(_capture_dl_pairs(document.html))

    for idx, text in enumerate(semantic_blocks):
        selector = f"semantic:{idx}"
        combined_blobs.append(text)
        _extract_labeled_location_fields(text, document, "semantic", selector, result)
        _extract_date_from_text(
            text=text,
            document=document,
            layer="semantic",
            selector_hint=selector,
            convention_name=convention_name,
            result=result,
        )


def _extract_combined_date_blob(
    document: CrawledDocument,
    convention_name: str,
    result: ExtractionResult,
    combined_blobs: list[str],
) -> None:
    if not combined_blobs:
        return
    joined = clean_source_text(" ".join(combined_blobs))
    if not joined:
        return
    _extract_date_from_text(
        text=joined,
        document=document,
        layer="visible",
        selector_hint="combined_blob",
        convention_name=convention_name,
        result=result,
    )


def _extract_priority_structured(document: CrawledDocument, convention_name: str, result: ExtractionResult) -> None:
    payloads: list[dict[str, object]] = []
    for script in JSONLD_PATTERN.findall(document.html):
        payload = _safe_json_load(script)
        if isinstance(payload, dict):
            payloads.append(payload)
        elif isinstance(payload, list):
            payloads.extend(item for item in payload if isinstance(item, dict))

    for payload in payloads:
        event_nodes = list(_iter_event_nodes(payload))
        for node in event_nodes:
            name = _node_str(node.get("name"))
            if name:
                _add(result, "convention_name", name, document, "structured", "jsonld:name", "LOW")

            date_text = _node_str(node.get("startDate"))
            if date_text:
                _add(result, "event_date", date_text, document, "structured", "jsonld:startDate", "LOW")

            location = node.get("location")
            if isinstance(location, dict):
                venue = _node_str(location.get("name"))
                if venue:
                    _add(result, "event_location", venue, document, "structured", "jsonld:location.name", "LOW")
                address = location.get("address")
                if isinstance(address, dict):
                    city = _node_str(address.get("addressLocality"))
                    state = _node_str(address.get("addressRegion"))
                    country = _node_str(address.get("addressCountry"))
                    if city:
                        _add(result, "city", city, document, "structured", "jsonld:addressLocality", "LOW")
                    if state:
                        _add(result, "state", state, document, "structured", "jsonld:addressRegion", "LOW")
                    if country:
                        _add(result, "country", country, document, "structured", "jsonld:addressCountry", "LOW")


def _extract_labeled_location_fields(
    text: str,
    document: CrawledDocument,
    layer: ExtractionLayer,
    selector_hint: str,
    result: ExtractionResult,
) -> None:
    cleaned = clean_source_text(text)
    if not cleaned:
        return

    for field_name, pattern in LABEL_PATTERNS.items():
        match = pattern.search(cleaned)
        if not match:
            continue
        value = clean_source_text(match.group(1))
        if not value:
            continue
        confidence = "HIGH" if field_name != "event_date" else "MEDIUM"
        score = 0.9 if confidence == "HIGH" else 0.65
        _add(result, field_name, value, document, layer, selector_hint, confidence, score)


def _extract_date_from_text(
    text: str,
    document: CrawledDocument,
    layer: ExtractionLayer,
    selector_hint: str,
    convention_name: str,
    result: ExtractionResult,
) -> None:
    cleaned = clean_source_text(text)
    if not cleaned:
        return

    best_phrase = ""
    best_score = -1.0
    for pattern in DATE_PATTERNS:
        for match in pattern.finditer(cleaned):
            phrase = clean_source_text(match.group(0))
            if not phrase:
                continue
            score = _date_phrase_score(cleaned, phrase, convention_name)
            if score > best_score:
                best_score = score
                best_phrase = phrase

    if not best_phrase:
        return

    confidence = "LOW"
    if best_score >= 0.8:
        confidence = "HIGH"
    elif best_score >= 0.45:
        confidence = "MEDIUM"

    _add(result, "event_date", best_phrase, document, layer, selector_hint, confidence, best_score)


def _date_phrase_score(context_text: str, phrase: str, convention_name: str) -> float:
    lowered = context_text.lower()
    score = 0.2
    if convention_name and convention_name.lower() in lowered:
        score += 0.3
    if any(token in lowered for token in ("registration", "register", "tickets")):
        score += 0.2
    if any(token in lowered for token in ("schedule", "dates", "when")):
        score += 0.2
    if any(token in lowered for token in ("venue", "location", "where")):
        score += 0.1
    if phrase.lower().startswith(("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")):
        score += 0.1
    return min(score, 1.0)


def _add(
    result: ExtractionResult,
    field_name: str,
    value: str,
    document: CrawledDocument,
    layer: ExtractionLayer,
    selector_hint: str,
    confidence: str,
    confidence_score: float = 0.0,
) -> None:
    cleaned_value = clean_source_text(value)
    if not cleaned_value:
        return
    result.evidences.append(
        FieldEvidence(
            field_name=field_name,
            value=cleaned_value,
            source_url=document.final_url,
            source_title=document.page_title,
            extraction_layer=layer,
            selector_hint=selector_hint,
            authority=document.source_role,
            confidence=confidence,  # type: ignore[arg-type]
            confidence_score=max(0.0, min(confidence_score, 1.0)),
        )
    )


def _capture_tag_content(html_text: str, tag: str) -> str:
    pattern = re.compile(TAG_CAPTURE_TEMPLATE.format(tag=tag), flags=re.IGNORECASE | re.DOTALL)
    match = pattern.search(html_text)
    if not match:
        return ""
    return clean_source_text(re.sub(r"<[^>]+>", " ", match.group(1)))


def _capture_all_tag_content(html_text: str, tag: str) -> list[str]:
    pattern = re.compile(TAG_CAPTURE_TEMPLATE.format(tag=tag), flags=re.IGNORECASE | re.DOTALL)
    out: list[str] = []
    for match in pattern.findall(html_text):
        text = clean_source_text(re.sub(r"<[^>]+>", " ", match))
        if text:
            out.append(text)
    return out


def _capture_dl_pairs(html_text: str) -> list[str]:
    dt_pattern = re.compile(r"<dt[^>]*>(.*?)</dt>\s*<dd[^>]*>(.*?)</dd>", flags=re.IGNORECASE | re.DOTALL)
    out: list[str] = []
    for dt, dd in dt_pattern.findall(html_text):
        left = clean_source_text(re.sub(r"<[^>]+>", " ", dt))
        right = clean_source_text(re.sub(r"<[^>]+>", " ", dd))
        if left and right:
            out.append(f"{left}: {right}")
    return out


def _attrs(tag: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, _, value in ATTR_PATTERN.findall(tag):
        out[key.lower()] = html.unescape(value)
    return out


def _extract_canonical_link(html_text: str) -> str:
    for tag in LINK_PATTERN.findall(html_text):
        attrs = _attrs(tag)
        rel = clean_source_text(attrs.get("rel", "")).lower()
        href = clean_source_text(attrs.get("href", ""))
        if rel == "canonical" and href:
            return href
    return ""


def _visible_lines(html_text: str) -> list[str]:
    no_scripts = re.sub(r"<script[^>]*>.*?</script>", " ", html_text, flags=re.IGNORECASE | re.DOTALL)
    no_styles = re.sub(r"<style[^>]*>.*?</style>", " ", no_scripts, flags=re.IGNORECASE | re.DOTALL)
    breaks = re.sub(r"</?(h1|h2|h3|h4|h5|h6|p|div|li|section|article|br|tr|td)[^>]*>", "\n", no_styles, flags=re.IGNORECASE)
    plain = re.sub(r"<[^>]+>", " ", breaks)
    lines = [clean_source_text(item) for item in plain.splitlines()]
    return [line for line in lines if line]


def _safe_json_load(text: str) -> object | None:
    raw = text.strip()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _iter_event_nodes(node: object) -> Iterable[dict[str, object]]:
    if isinstance(node, dict):
        node_type = node.get("@type")
        if isinstance(node_type, str) and "event" in node_type.lower():
            yield node
        elif isinstance(node_type, list) and any(isinstance(item, str) and "event" in item.lower() for item in node_type):
            yield node
        for value in node.values():
            yield from _iter_event_nodes(value)
    elif isinstance(node, list):
        for item in node:
            yield from _iter_event_nodes(item)


def _node_str(value: object) -> str:
    if isinstance(value, str):
        return clean_source_text(value)
    return ""
