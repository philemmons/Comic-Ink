from pythonCon.convention_enricher.confidence import resolve_field_value
from pythonCon.convention_enricher.models import FieldCandidate


def test_confidence_selects_best_verified_candidate() -> None:
    candidates = [
        FieldCandidate("city", "Seattle", "https://a", "website", 0.7, True, "A"),
        FieldCandidate("city", "Seattle", "https://b", "search", 0.9, True, "B"),
    ]
    value, reason, level = resolve_field_value("city", candidates, unknown_value="**")
    assert value == "Seattle"
    assert "Selected verified value" in reason
    assert level in {"LOW", "MEDIUM", "HIGH"}


def test_confidence_marks_ambiguous_values_unknown() -> None:
    candidates = [
        FieldCandidate("city", "Seattle", "https://a", "website", 0.9, True, "A"),
        FieldCandidate("city", "Portland", "https://b", "search", 0.9, True, "B"),
    ]
    value, reason, level = resolve_field_value("city", candidates, unknown_value="**")
    assert value == "**"
    assert "Ambiguous" in reason
    assert level == "NONE"


def test_confidence_normalizes_location_abbrev_output() -> None:
    candidates = [
        FieldCandidate("state_abrev", "on", "https://a", "website", 0.95, True, "A"),
    ]
    value, _, level = resolve_field_value("state_abrev", candidates, unknown_value="**")
    assert value == "ON"
    assert level == "HIGH"
