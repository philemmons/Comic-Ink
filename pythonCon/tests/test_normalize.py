from __future__ import annotations

from convention_enricher.normalize import normalize_for_ranking


def test_normalize_for_ranking_removes_status_markers_and_punctuation() -> None:
    text = "Grand Rapids Comic-Con (Postponed)!"
    normalized = normalize_for_ranking(text)
    assert normalized == "grand rapids comic con"
