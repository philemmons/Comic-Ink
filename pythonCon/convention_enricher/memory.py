from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from .utils import normalize_for_ranking, read_json, write_json


@dataclass(slots=True)
class DomainMemoryEntry:
    domain: str
    hits: int


class DomainMemory:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._data: dict[str, dict[str, int]] = self._load()

    def _load(self) -> dict[str, dict[str, int]]:
        raw = read_json(self.path)
        if not isinstance(raw, dict):
            return {}
        out: dict[str, dict[str, int]] = {}
        for key, value in raw.items():
            if isinstance(value, dict):
                normalized: dict[str, int] = {}
                for domain, count in value.items():
                    if isinstance(domain, str) and isinstance(count, int):
                        normalized[domain] = count
                out[str(key)] = normalized
        return out

    def remember(self, convention_name: str, domain: str) -> None:
        key = normalize_for_ranking(convention_name)
        if not key or not domain:
            return
        bucket = self._data.setdefault(key, {})
        bucket[domain] = bucket.get(domain, 0) + 1

    def preferred_domains(self, convention_name: str) -> list[DomainMemoryEntry]:
        key = normalize_for_ranking(convention_name)
        bucket = self._data.get(key, {})
        ranked = sorted(bucket.items(), key=lambda item: item[1], reverse=True)
        return [DomainMemoryEntry(domain=domain, hits=hits) for domain, hits in ranked]

    def save(self) -> None:
        write_json(self.path, self._data)
