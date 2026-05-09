from __future__ import annotations

import tempfile
from pathlib import Path

from convention_enricher.checkpoint import CheckpointManager
from convention_enricher.models import ConventionOutputRow


def _scratch() -> Path:
    return Path(tempfile.mkdtemp(prefix="ce_test_", dir=Path.cwd()))


def test_checkpoint_round_trip() -> None:
    base = _scratch()
    checkpoint = CheckpointManager(base / "checkpoint.json")
    row = ConventionOutputRow(convention_name="Alpha", event_date="**", website_url="**")
    checkpoint.mark_completed("Alpha", row)

    loaded = CheckpointManager(base / "checkpoint.json")
    assert loaded.is_completed("Alpha")
    output = loaded.get_output("Alpha")
    assert output is not None
    assert output.convention_name == "Alpha"
    assert output.event_date == "**"
