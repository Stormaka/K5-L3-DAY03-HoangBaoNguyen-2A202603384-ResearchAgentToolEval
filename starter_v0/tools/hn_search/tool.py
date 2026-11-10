from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT, domain, err


def search_hackernews(query: str = "", tags: str = "story", limit: int = 5) -> dict[str, Any]:
    try:
        query = (query or "").strip()
        if not query:
            raise ValueError("query must be a non-empty keyword (e.g. 'OpenAI', 'Rust')")
        response = requests.get(
            "https://hn.algolia.com/api/v1/search",
            params={"query": query, "tags": tags or "story", "hitsPerPage": int(limit or 5)},
            headers={"User-Agent": "AI20k-Day03-Research-Agent/1.0 (educational lab)"},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        items = []
        for hit in data.get("hits", [])[: int(limit or 5)]:
            if not hit.get("objectID"):
                continue
            url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit['objectID']}"
            items.append({
                "title": hit.get("title") or hit.get("story_title") or "",
                "url": url,
                "source": domain(url) or "news.ycombinator.com",
                "summary": (hit.get("story_text") or hit.get("comment_text") or "").strip()[:500] or None,
                "points": hit.get("points"),
                "comments": hit.get("num_comments"),
                "author": hit.get("author"),
                "date": hit.get("created_at"),
            })
        return {
            "tool": "search_hackernews",
            "query": query,
            "tags": tags,
            "total_hits": data.get("nbHits"),
            "items": items,
        }
    except Exception as exc:
        return err("search_hackernews", exc)
