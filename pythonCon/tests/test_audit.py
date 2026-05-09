from __future__ import annotations

import tempfile
from pathlib import Path

from convention_enricher.discovery import DiscoveryRanker
from convention_enricher.memory import DomainMemory
from convention_enricher.models import SearchResult


def _scratch() -> Path:
    return Path(tempfile.mkdtemp(prefix="ce_test_", dir=Path.cwd()))


def test_discovery_ranker_prefers_authoritative_domain() -> None:
    base = _scratch()
    memory = DomainMemory(base / "memory.json")
    memory.remember("Alpha Comic Con", "alphaofficial.com")

    ranker = DiscoveryRanker(memory)
    ranked = ranker.rank(
        "Alpha Comic Con",
        [
            SearchResult("google", "q", "https://facebook.com/alpha", "", ""),
            SearchResult("google", "q", "https://alphaofficial.com/convention", "", ""),
            SearchResult("bing", "q", "https://eventbrite.com/e/alpha", "", ""),
        ],
    )

    assert ranked
    assert ranked[0].url == "https://alphaofficial.com/convention"
