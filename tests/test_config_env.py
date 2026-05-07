from pathlib import Path

from convention_enricher.config import RuntimeConfig, apply_env_overrides


def test_env_overrides_are_applied(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("CONVENTION_ENRICHER_USER_AGENT", "TestAgent/9.9")
    monkeypatch.setenv("CONVENTION_ENRICHER_TIMEOUT_SECONDS", "4.5")
    monkeypatch.setenv("CONVENTION_ENRICHER_MAX_SEARCH_RESULTS", "7")
    monkeypatch.setenv("CONVENTION_ENRICHER_RETRY_TOTAL", "5")
    monkeypatch.setenv("CONVENTION_ENRICHER_RETRY_BACKOFF_SECONDS", "1.1")
    monkeypatch.setenv("CONVENTION_ENRICHER_RATE_LIMIT_PER_SECOND", "3.0")

    cfg = RuntimeConfig(
        input_csv=tmp_path / "in.csv",
        output_csv=tmp_path / "out.csv",
        audit_csv=tmp_path / "audit.csv",
        year=2026,
    )
    updated = apply_env_overrides(cfg)
    assert updated.user_agent == "TestAgent/9.9"
    assert updated.timeout_seconds == 4.5
    assert updated.max_search_results == 7
    assert updated.retry_total == 5
    assert updated.retry_backoff_seconds == 1.1
    assert updated.rate_limit_per_second == 3.0
