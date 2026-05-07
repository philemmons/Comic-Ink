from __future__ import annotations

from pathlib import Path
from typing import Any

from .utils import read_json_file, sha1_text, write_json_file


class FileCache:
    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, namespace: str, key: str, extension: str) -> Path:
        digest = sha1_text(key)
        return self.cache_dir / namespace / f"{digest}.{extension}"

    def get_json(self, namespace: str, key: str) -> Any | None:
        path = self._path(namespace, key, "json")
        if not path.exists():
            return None
        return read_json_file(path)

    def set_json(self, namespace: str, key: str, value: Any) -> None:
        path = self._path(namespace, key, "json")
        write_json_file(path, value)

    def get_text(self, namespace: str, key: str) -> str | None:
        path = self._path(namespace, key, "txt")
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def set_text(self, namespace: str, key: str, value: str) -> None:
        path = self._path(namespace, key, "txt")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")
