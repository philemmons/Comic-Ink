from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from .models import AnalyzerStats
from .utils import write_json


class Analyzer:
    def __init__(self) -> None:
        self.stats = AnalyzerStats()

    def write(self, path: Path) -> None:
        write_json(path, asdict(self.stats))
