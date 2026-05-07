from __future__ import annotations

from collections import defaultdict

from .models import ConfidenceLevel, FieldCandidate
from .normalize import normalize_field_value, normalize_for_compare


def resolve_field_value(
    field_name: str,
    candidates: list[FieldCandidate],
    unknown_value: str = "**",
    minimum_confidence: float = 0.70,
) -> tuple[str, str, ConfidenceLevel]:
    if not candidates:
        return unknown_value, "No candidates found.", "NONE"

    grouped: dict[str, list[FieldCandidate]] = defaultdict(list)
    for candidate in candidates:
        normalized = normalize_for_compare(candidate.value)
        grouped[normalized].append(candidate)

    if len(grouped) > 1:
        return unknown_value, "Ambiguous values across sources.", "NONE"

    group = next(iter(grouped.values()))
    best = max(group, key=lambda item: item.confidence)
    if not best.verified:
        return unknown_value, "Top candidate is unverified.", "NONE"
    if best.confidence < minimum_confidence:
        return unknown_value, "Top candidate confidence below threshold.", _level(best.confidence)

    normalized_value = normalize_field_value(field_name, best.value)
    if not normalized_value:
        return unknown_value, "Top candidate normalized to empty value.", "NONE"
    return normalized_value, f"Selected verified value ({best.reason}).", _level(best.confidence)


def _level(confidence: float) -> ConfidenceLevel:
    if confidence >= 0.9:
        return "HIGH"
    if confidence >= 0.75:
        return "MEDIUM"
    if confidence >= 0.5:
        return "LOW"
    return "NONE"
