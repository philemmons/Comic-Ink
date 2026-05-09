from __future__ import annotations

from convention_enricher.confidence import confidence_rank


def test_confidence_rank_ordering() -> None:
    assert confidence_rank("HIGH") > confidence_rank("MEDIUM") > confidence_rank("LOW") > confidence_rank("NONE")
