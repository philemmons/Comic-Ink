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
        normalized_value = normalize_field_value(field_name, candidate.value) or candidate.value
        normalized = normalize_for_compare(normalized_value)
        grouped[normalized].append(candidate)

    if len(grouped) > 1:
        group_rankings: list[tuple[float, int, list[FieldCandidate]]] = []
        for group in grouped.values():
            best_conf = max(item.confidence for item in group)
            group_rankings.append((best_conf, len(group), group))
        group_rankings.sort(key=lambda item: (item[0], item[1]), reverse=True)

        top_best_conf, top_count, top_group = group_rankings[0]
        next_best_conf = group_rankings[1][0] if len(group_rankings) > 1 else 0.0
        next_count = group_rankings[1][1] if len(group_rankings) > 1 else 0
        top_verified = [item for item in top_group if item.verified]
        top_verified_count = len(top_verified)
        top_source_count = len({item.source_url for item in top_verified})

        # Allow a dominant, high-confidence consensus to win only with corroboration.
        top_dominates = (
            top_best_conf >= minimum_confidence
            and top_verified_count >= 2
            and top_source_count >= 2
            and (
                next_best_conf < (minimum_confidence - 0.10)
                or (top_best_conf - next_best_conf) >= 0.15
                or (top_count >= 2 and top_count >= (next_count * 2))
            )
        )
        if top_dominates:
            if top_verified:
                best = max(top_verified, key=lambda item: item.confidence)
                normalized_value = normalize_field_value(field_name, best.value)
                if normalized_value:
                    return (
                        normalized_value,
                        f"Resolved conflicting candidates by confidence dominance ({best.reason}).",
                        _level(best.confidence),
                    )
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
