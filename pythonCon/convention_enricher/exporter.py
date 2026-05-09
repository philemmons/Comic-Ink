from __future__ import annotations

from pathlib import Path

from .csv_io import write_output_rows
from .models import ConventionOutputRow


class CsvExporter:
    def export(self, output_csv: Path, rows: list[ConventionOutputRow]) -> None:
        write_output_rows(output_csv, [row.as_dict() for row in rows])
