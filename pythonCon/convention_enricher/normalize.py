from __future__ import annotations

import re
import unicodedata


STATUS_MARKERS = {"cancelled", "canceled", "postponed", "rescheduled"}


def normalize_for_ranking(text: str) -> str:
    lowered = text.lower()
    normalized = unicodedata.normalize("NFKD", lowered)
    no_punct = re.sub(r"[^a-z0-9\s]", " ", normalized)
    collapsed = re.sub(r"\s+", " ", no_punct).strip()
    return " ".join(token for token in collapsed.split() if token not in STATUS_MARKERS)
