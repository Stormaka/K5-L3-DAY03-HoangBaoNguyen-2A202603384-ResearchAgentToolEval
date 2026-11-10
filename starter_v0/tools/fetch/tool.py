from __future__ import annotations

import html as html_lib
import os
import re
from typing import Any

import requests

from tools._shared import TIMEOUT, domain, err


def _fallback_enabled() -> bool:
    return os.getenv("KEYLESS_FALLBACKS", "").strip().lower() in {"1", "true", "yes"}


def _direct_read(url: str) -> dict[str, Any]:
    response = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; AI20kDay03ResearchAgent/1.0; educational lab)"},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    raw = response.text
    title_match = re.search(r"<title[^>]*>(.*?)</title>", raw, re.IGNORECASE | re.DOTALL)
    title = html_lib.unescape(title_match.group(1)).strip() if title_match else url
    text = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", raw)
    text = html_lib.unescape(re.sub(r"<[^>]+>", " ", text))
    text = re.sub(r"\s+", " ", text).strip()
    return {
        "tool": "read_url",
        "url": url,
        "items": [{
            "title": title or url,
            "url": url,
            "source": domain(url),
            "summary": text[:4000],
        }],
        "fallback": "direct_get",
        "note": "Keyless fallback (no FIRECRAWL_API_KEY). Plain-text extraction, no markdown rendering.",
    }


def read_url(url: str = "") -> dict[str, Any]:
    try:
        key = os.getenv("FIRECRAWL_API_KEY")
        if not key:
            # Demo fallback: read the URL directly and strip HTML when no Firecrawl key.
            if _fallback_enabled():
                return _direct_read(url)
            raise RuntimeError("Missing FIRECRAWL_API_KEY env var")
        response = requests.post(
            "https://api.firecrawl.dev/v1/scrape",
            json={"url": url, "formats": ["markdown"]},
            headers={"Authorization": f"Bearer {key}"},
            timeout=60,
        )
        response.raise_for_status()
        data = response.json().get("data", {})
        meta = data.get("metadata", {}) or {}
        return {"tool": "read_url", "url": url, "items": [{
            "title": meta.get("title") or url,
            "url": meta.get("sourceURL") or url,
            "source": domain(url),
            "summary": (data.get("markdown") or "")[:4000],
        }]}
    except Exception as exc:
        return err("read_url", exc)
