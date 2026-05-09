from __future__ import annotations

from collections import defaultdict

from .models import ConventionOutputRow, FieldEvidence, UNKNOWN_VALUE


AUTHORITY_ORDER = {
    "convention": 5,
    "registration": 4,
    "organizer": 3,
    "venue": 2,
    "listing": 1,
    "unknown": 0,
}

CONFIDENCE_ORDER = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}

LAYER_ORDER = {"meta": 4, "visible": 3, "semantic": 2, "structured": 1}


def resolve_output(convention_name: str, evidences: list[FieldEvidence]) -> ConventionOutputRow:
    grouped: dict[str, list[FieldEvidence]] = defaultdict(list)
    for evidence in evidences:
        grouped[evidence.field_name].append(evidence)

    row = ConventionOutputRow(convention_name=convention_name)

    row.event_date = _pick("event_date", grouped)
    row.event_location = _pick("event_location", grouped)
    row.city = _pick("city", grouped)
    row.state = _pick("state", grouped)
    row.country = _pick("country", grouped)

    chosen_website = _pick("website_url", grouped)
    if chosen_website == UNKNOWN_VALUE:
        # Fallback to authoritative source page URL when explicit website field is unavailable.
        page_choice = _pick_evidence(grouped.get("convention_name", []) + grouped.get("event_date", []))
        if page_choice:
            chosen_website = page_choice.source_url

    row.website_url = chosen_website if chosen_website else UNKNOWN_VALUE
    return row


def _pick(field_name: str, grouped: dict[str, list[FieldEvidence]]) -> str:
    evidence = _pick_evidence(grouped.get(field_name, []))
    return evidence.value if evidence else UNKNOWN_VALUE


def _pick_evidence(items: list[FieldEvidence]) -> FieldEvidence | None:
    if not items:
        return None
    ranked = sorted(
        items,
        key=lambda item: (
            AUTHORITY_ORDER.get(item.authority, 0),
            CONFIDENCE_ORDER.get(item.confidence, 0),
            item.confidence_score,
            LAYER_ORDER.get(item.extraction_layer, 0),
        ),
        reverse=True,
    )
    return ranked[0]
