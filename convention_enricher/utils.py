from __future__ import annotations

from datetime import datetime
import hashlib
import json
import logging
from pathlib import Path
from typing import Any


def setup_logging(verbose: bool, log_dir: Path) -> Path:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"enrich_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    root_logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    return log_path


def clean_string(value: str | None) -> str:
    return (value or "").strip()


def sha1_text(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def read_json_file(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json_file(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
