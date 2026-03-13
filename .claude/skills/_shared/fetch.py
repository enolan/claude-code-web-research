"""Shared Amazon page fetcher using httpx."""

import json
import sys

import httpx

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch(url: str) -> str:
    """Fetch a URL with browser-like headers. Returns HTML string."""
    try:
        resp = httpx.get(url, headers=_HEADERS, timeout=30, follow_redirects=True)
        resp.raise_for_status()
        return resp.text
    except httpx.HTTPError as e:
        print(json.dumps({"error": f"HTTP request failed: {e}"}))
        sys.exit(1)


def check_captcha(html: str) -> None:
    """Exit with error JSON if Amazon returned a CAPTCHA page."""
    if "captcha" in html.lower():
        print(
            json.dumps(
                {
                    "error": "CAPTCHA detected. Amazon is rate-limiting requests. Wait a minute and retry."
                }
            )
        )
        sys.exit(1)
