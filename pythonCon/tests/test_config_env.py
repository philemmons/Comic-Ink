from __future__ import annotations

import tempfile
from pathlib import Path

from convention_enricher.config import RuntimeConfig


def _scratch() -> Path:
    return Path(tempfile.mkdtemp(prefix="ce_test_", dir=Path.cwd()))


def test_runtime_config_paths() -> None:
    base = _scratch()
    cfg = RuntimeConfig(input_csv=base / "in.csv", output_csv=base / "out.csv", work_dir=base / ".work")
    assert cfg.checkpoint_path.name == "checkpoint.json"
    assert cfg.snapshots_dir.name == "snapshots"
    assert cfg.cache_dir.name == "cache"
