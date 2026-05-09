from __future__ import annotations

from pathlib import Path

from .utils import read_json, sha256_text, write_json


class FileCache:
    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, namespace: str, key: str, extension: str) -> Path:
        digest = sha256_text(key)
        return self.cache_dir / namespace / f"{digest}.{extension}"

    def get_text(self, namespace: str, key: str) -> str | None:
        path = self._path(namespace, key, "txt")
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def set_text(self, namespace: str, key: str, value: str) -> None:
        path = self._path(namespace, key, "txt")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")

    def get_json(self, namespace: str, key: str) -> object | None:
        path = self._path(namespace, key, "json")
        return read_json(path)

    def set_json(self, namespace: str, key: str, value: object) -> None:
        path = self._path(namespace, key, "json")
        write_json(path, value)
