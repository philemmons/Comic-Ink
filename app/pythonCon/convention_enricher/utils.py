from __future__ import annotations

from datetime import datetime
import hashlib
import html
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import urlparse, urlunparse


STATUS_MARKERS = {"cancelled", "canceled", "postponed", "rescheduled"}


def now_utc_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="ignore")).hexdigest()


def read_json(path: Path) -> object | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def canonicalize_url(url: str) -> str:
    text = collapse_accidental_whitespace(url.strip())
    if not text:
        return ""
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", text):
        text = f"https://{text}"
    try:
        parsed = urlparse(text)
    except ValueError:
        return ""
    if not parsed.netloc:
        return ""
    host = parsed.netloc.lower()
    if host.endswith(":80") and parsed.scheme.lower() == "http":
        host = host[:-3]
    if host.endswith(":443") and parsed.scheme.lower() == "https":
        host = host[:-4]
    host_name = host.split(":", 1)[0]
    if not re.fullmatch(r"[a-z0-9.-]+", host_name):
        return ""
    if "." not in host_name and host_name != "localhost":
        return ""
    if host_name.startswith(".") or host_name.endswith(".") or ".." in host_name:
        return ""
    path = parsed.path or "/"
    return urlunparse((parsed.scheme.lower() or "https", host, path, "", parsed.query, ""))


def get_domain(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    return host[4:] if host.startswith("www.") else host


def strip_tags(html_text: str) -> str:
    no_scripts = re.sub(r"<script[^>]*>.*?</script>", " ", html_text, flags=re.IGNORECASE | re.DOTALL)
    no_styles = re.sub(r"<style[^>]*>.*?</style>", " ", no_scripts, flags=re.IGNORECASE | re.DOTALL)
    no_tags = re.sub(r"<[^>]+>", " ", no_styles)
    return html.unescape(no_tags)


def collapse_accidental_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def clean_source_text(text: str) -> str:
    # Allowed cleanup: trim and collapse accidental duplicated whitespace.
    return collapse_accidental_whitespace(text)


def normalize_for_ranking(text: str) -> str:
    lowered = text.lower()
    normalized = unicodedata.normalize("NFKD", lowered)
    no_punct = re.sub(r"[^a-z0-9\s]", " ", normalized)
    collapsed = collapse_accidental_whitespace(no_punct)
    tokens = [token for token in collapsed.split() if token not in STATUS_MARKERS]
    return " ".join(tokens)


def token_overlap(left: str, right: str) -> float:
    lt = set(normalize_for_ranking(left).split())
    rt = set(normalize_for_ranking(right).split())
    if not lt or not rt:
        return 0.0
    return len(lt & rt) / max(len(lt), len(rt))
