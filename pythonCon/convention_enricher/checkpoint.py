from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .models import ConventionOutputRow
from .utils import read_json, write_json


@dataclass(slots=True)
class CheckpointState:
    completed: dict[str, dict[str, str]]


class CheckpointManager:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.state = self._load()

    def _load(self) -> CheckpointState:
        raw = read_json(self.path)
        if not isinstance(raw, dict):
            return CheckpointState(completed={})
        completed_raw = raw.get("completed", {})
        if not isinstance(completed_raw, dict):
            return CheckpointState(completed={})
        completed: dict[str, dict[str, str]] = {}
        for key, value in completed_raw.items():
            if isinstance(key, str) and isinstance(value, dict):
                completed[key] = {str(k): str(v) for k, v in value.items()}
        return CheckpointState(completed=completed)

    def is_completed(self, convention_name: str) -> bool:
        return convention_name in self.state.completed

    def get_output(self, convention_name: str) -> ConventionOutputRow | None:
        row = self.state.completed.get(convention_name)
        if not isinstance(row, dict):
            return None
        return ConventionOutputRow(
            convention_name=row.get("convention_name", "**"),
            event_date=row.get("event_date", "**"),
            event_location=row.get("event_location", "**"),
            city=row.get("city", "**"),
            state=row.get("state", "**"),
            country=row.get("country", "**"),
            website_url=row.get("website_url", "**"),
        )

    def mark_completed(self, convention_name: str, output: ConventionOutputRow) -> None:
        self.state.completed[convention_name] = output.as_dict()
        write_json(self.path, {"completed": self.state.completed})
