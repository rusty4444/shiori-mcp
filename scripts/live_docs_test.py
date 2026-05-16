#!/usr/bin/env python3
"""Validate public Shiori API documentation and repository pages."""

from __future__ import annotations

import httpx

URLS = [
    "https://raw.githubusercontent.com/go-shiori/shiori/master/docs/API.md",
    "https://raw.githubusercontent.com/go-shiori/shiori/master/docs/APIv1.md",
    "https://github.com/go-shiori/shiori",
]

EXPECTED = [
    "/api/bookmarks",
    "/swagger/index.html",
    "Simple bookmark manager",
]


def main() -> int:
    with httpx.Client(timeout=30, follow_redirects=True) as client:
        for url, expected in zip(URLS, EXPECTED, strict=True):
            response = client.get(url)
            print(f"{response.status_code} {url}")
            response.raise_for_status()
            if expected.lower() not in response.text.lower():
                raise AssertionError(f"{url} did not contain expected text: {expected!r}")
    print(f"{len(URLS)}/{len(URLS)} public Shiori documentation checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
