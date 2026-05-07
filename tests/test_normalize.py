from convention_enricher.normalize import (
    format_month_day,
    is_missing,
    normalize_field_value,
    normalize_url,
    parse_datetime,
    parse_year,
)


def test_normalize_url_adds_scheme() -> None:
    assert normalize_url("example.com/path") == "https://example.com/path"


def test_parse_year_extracts_year() -> None:
    assert parse_year("November 3, 2026") == 2026


def test_is_missing_recognizes_unknown_marker() -> None:
    assert is_missing("**")
    assert is_missing(" TBD ")
    assert is_missing("TBA")
    assert not is_missing("Comic-Con")


def test_parse_datetime_and_format_month_day() -> None:
    dt = parse_datetime("2026-11-03")
    assert dt is not None
    assert format_month_day(dt) == "November 3"


def test_location_normalization_state_abbrev_uppercases() -> None:
    assert normalize_field_value("state_abrev", "on") == "ON"
