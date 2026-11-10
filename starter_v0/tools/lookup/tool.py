from __future__ import annotations

import os
import re
import xml.etree.ElementTree as ET
from typing import Any

import requests

from tools._shared import TIMEOUT, domain, err


def _fallback_enabled() -> bool:
    return os.getenv("KEYLESS_FALLBACKS", "").strip().lower() in {"1", "true", "yes"}


_TIMEFRAME_DAYS = {"day": 1, "week": 7, "month": 30, "year": 365}


def _google_news_rss(query: str, timeframe: str | None, max_results: int) -> dict[str, Any]:
    q = query or ""
    days = _TIMEFRAME_DAYS.get(timeframe or "")
    if days:
        q = f"{q} when:{days}d"
    response = requests.get(
        "https://news.google.com/rss/search",
        params={"q": q, "hl": "vi", "gl": "VN", "ceid": "VN:vi"},
        headers={"User-Agent": "AI20k-Day03-Research-Agent/1.0 (educational lab)"},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    root = ET.fromstring(response.content)
    items = []
    for item in root.findall("./channel/item")[: int(max_results or 5)]:
        title = (item.findtext("title") or "").strip()
        url = (item.findtext("link") or "").strip()
        source_tag = item.find("source")
        source = (source_tag.text or "").strip() if source_tag is not None else ""
        summary = re.sub(r"<[^>]+>", " ", item.findtext("description") or "").strip()
        items.append({
            "title": title,
            "url": url,
            "source": source or domain(url),
            "summary": summary or title,
            "score": None,
            "date": item.findtext("pubDate"),
        })
    return {
        "tool": "web_search",
        "query": query,
        "topic": "news",
        "timeframe": timeframe,
        "items": items,
        "fallback": "google_news_rss",
        "note": "Keyless fallback (no TAVILY_API_KEY). Results come from Google News RSS.",
    }


def web_search(query: str = "", topic: str = "general", timeframe: str | None = "week", max_results: int = 5) -> dict[str, Any]:
    try:
        key = os.getenv("TAVILY_API_KEY")
        if not key:
            # Demo fallback: news queries can be served keyless via Google News RSS.
            if _fallback_enabled() and topic == "news":
                return _google_news_rss(query, timeframe, max_results)
            raise RuntimeError("Missing TAVILY_API_KEY env var")
        body: dict[str, Any] = {"query": query, "topic": topic, "max_results": int(max_results or 5), "search_depth": "basic"}
        if timeframe:
            body["time_range"] = timeframe
        response = requests.post(
            "https://api.tavily.com/search",
            json=body,
            headers={"Authorization": f"Bearer {key}"},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        items = [{
            "title": item.get("title"),
            "url": item.get("url"),
            "source": domain(item.get("url", "")),
            "summary": item.get("content"),
            "score": item.get("score"),
        } for item in data.get("results", [])]
        return {"tool": "web_search", "query": query, "topic": topic, "timeframe": timeframe, "items": items}
    except Exception as exc:
        return err("web_search", exc)
