from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from .memory import DomainMemory
from .models import DiscoveredUrl, SearchResult, SourceRole
from .utils import get_domain, normalize_for_ranking, token_overlap


SPAM_HOST_MARKERS = {
    "pinterest.",
    "tumblr.",
    "blogspot.",
    "wordpress.",
    "medium.com",
    "fandom.com",
}

TRUSTED_LISTING_DOMAINS = {
    "10times.com",
    "fancons.com",
    "eventbrite.com",
    "allevents.in",
}

HIGH_VALUE_KEYWORDS = {
    "date",
    "schedule",
    "event",
    "convention",
    "venue",
    "location",
    "registration",
    "tickets",
    "attend",
    "faq",
    "about",
    "contact",
}


AUTHORITY_SCORES: dict[SourceRole, int] = {
    "convention": 100,
    "registration": 90,
    "organizer": 80,
    "venue": 70,
    "listing": 60,
    "unknown": 20,
}


def classify_source_role(url: str) -> SourceRole:
    domain = get_domain(url)
    path = urlparse(url).path.lower()
    text = f"{domain} {path}"
    if any(marker in text for marker in ("tickets", "register", "registration", "eventbrite")):
        return "registration"
    if any(marker in text for marker in ("convention", "comiccon", "comic-con", "expo", "fanexpo", "con")):
        return "convention"
    if any(marker in text for marker in ("organizer", "about-us", "our-team", "company")):
        return "organizer"
    if any(marker in text for marker in ("venue", "center", "conventioncenter", "hotel")):
        return "venue"
    if domain in TRUSTED_LISTING_DOMAINS:
        return "listing"
    return "unknown"


def is_low_trust(url: str) -> bool:
    domain = get_domain(url)
    if any(marker in domain for marker in SPAM_HOST_MARKERS):
        return True
    if "affiliate" in url.lower() or "utm_" in url.lower() and "redirect" in url.lower():
        return True
    return False


@dataclass(slots=True)
class DiscoveryRanker:
    domain_memory: DomainMemory

    def rank(self, convention_name: str, search_results: list[SearchResult]) -> list[DiscoveredUrl]:
        ranked: list[DiscoveredUrl] = []
        memory_domains = {entry.domain: entry.hits for entry in self.domain_memory.preferred_domains(convention_name)}

        for result in search_results:
            url = result.url
            if is_low_trust(url):
                continue

            authority = classify_source_role(url)
            trust = AUTHORITY_SCORES[authority]
            domain = get_domain(url)
            if domain in memory_domains:
                trust += min(25, memory_domains[domain] * 5)

            overlap = token_overlap(convention_name, f"{result.title} {result.snippet} {url}")
            path_bonus = 0.0
            lowered = url.lower()
            if any(keyword in lowered for keyword in HIGH_VALUE_KEYWORDS):
                path_bonus = 0.15

            rank_score = trust + overlap * 20.0 + path_bonus * 10.0
            ranked.append(
                DiscoveredUrl(
                    url=url,
                    provider=result.provider,
                    query=result.query,
                    authority=authority,
                    trust_score=trust,
                    relevance_score=overlap,
                    rank_score=rank_score,
                )
            )

        ranked.sort(key=lambda item: item.rank_score, reverse=True)

        # Deduplicate by canonical URL and domain preference.
        seen_urls: set[str] = set()
        seen_domains: dict[str, int] = {}
        filtered: list[DiscoveredUrl] = []
        for item in ranked:
            if item.url in seen_urls:
                continue
            seen_urls.add(item.url)

            domain = get_domain(item.url)
            domain_count = seen_domains.get(domain, 0)
            if domain_count >= 3:
                continue
            seen_domains[domain] = domain_count + 1
            filtered.append(item)
        return filtered
