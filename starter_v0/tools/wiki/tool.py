from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT, domain, err


def wiki_lookup(topic: str = "", lang: str = "vi") -> dict[str, Any]:
    try:
        topic = (topic or "").strip()
        if not topic:
            raise ValueError("topic must be a non-empty string (e.g. 'Tesla', 'Transformer')")
        lang = (lang or "vi").strip().lower() or "vi"
        response = requests.get(
            f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(topic)}",
            headers={"User-Agent": "AI20k-Day03-Research-Agent/1.0 (educational lab)"},
            timeout=TIMEOUT,
        )
        if response.status_code == 404:
            return {
                "tool": "wiki_lookup",
                "topic": topic,
                "lang": lang,
                "error": "not_found",
                "message": f"No Wikipedia page for {topic!r} in '{lang}' wiki. Try another wording or lang='en'.",
            }
        response.raise_for_status()
        data = response.json()
        page_url = ((data.get("content_urls") or {}).get("desktop") or {}).get("page") or ""
        return {
            "tool": "wiki_lookup",
            "topic": topic,
            "lang": lang,
            "title": data.get("title"),
            "description": data.get("description"),
            "summary": data.get("extract"),
            "url": page_url,
            "source": domain(page_url) or f"{lang}.wikipedia.org",
        }
    except Exception as exc:
        return err("wiki_lookup", exc)
