from __future__ import annotations

from pathlib import Path

from .models import FetchedPage, SnapshotRecord
from .utils import now_utc_iso, sha256_text, write_json


class SnapshotStore:
    def __init__(self, snapshots_dir: Path) -> None:
        self.snapshots_dir = snapshots_dir
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

    def save(self, page: FetchedPage) -> SnapshotRecord:
        content_hash = sha256_text(page.html)
        stamp = now_utc_iso().replace(":", "-")
        snapshot_id = f"{stamp}_{content_hash[:12]}"
        html_path = self.snapshots_dir / f"{snapshot_id}.html"
        meta_path = self.snapshots_dir / f"{snapshot_id}.json"

        html_path.write_text(page.html, encoding="utf-8")
        record = SnapshotRecord(
            snapshot_id=snapshot_id,
            fetched_url=page.requested_url,
            final_url=page.final_url,
            timestamp_utc=page.fetched_at_utc,
            content_hash=content_hash,
            html_path=str(html_path),
        )
        write_json(meta_path, record.__dict__)
        return record
