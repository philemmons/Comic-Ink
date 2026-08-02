from __future__ import annotations

from pathlib import Path

from .csv_io import load_search_targets


class InputLoader:
    def load(self, input_csv: Path) -> list[str]:
        return load_search_targets(input_csv)
