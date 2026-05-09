from __future__ import annotations

from .http_client import HttpClient
from .models import FetchedPage
from .utils import canonicalize_url


class Scraper:
    def __init__(self, http_client: HttpClient) -> None:
        self.http_client = http_client

    def fetch(self, url: str) -> FetchedPage:
        normalized = canonicalize_url(url)
        if not normalized:
            return FetchedPage(
                requested_url=url,
                final_url=url,
                status_code=None,
                ok=False,
                html="",
                fetched_at_utc="",
                error="invalid_url",
            )
        return self.http_client.fetch(normalized)
