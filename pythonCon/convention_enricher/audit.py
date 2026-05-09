from __future__ import annotations

from pathlib import Path

from .utils import write_json


def write_internal_provenance(path: Path, records: list[dict[str, str]]) -> None:
    write_json(path, {"provenance": records})
