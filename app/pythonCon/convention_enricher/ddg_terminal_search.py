from __future__ import annotations

import requests

DDG_HTML_ENDPOINT = "https://html.duckduckgo.com/html/"
QUERY = "\"NWA Comic Con 2026\""


def main() -> int:
    session = requests.Session()
    session.trust_env = False

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://duckduckgo.com/",
    }

    response = session.post(
        DDG_HTML_ENDPOINT,
        headers=headers,
        data={"q": QUERY},
        timeout=15,
        allow_redirects=True,
    )

    print(f"query: {QUERY}")
    print(f"status_code: {response.status_code}")
    print(f"final_url: {response.url}")
    print("--- response_preview_start ---")
    print(response.text[:800])
    print("--- response_preview_end ---")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
