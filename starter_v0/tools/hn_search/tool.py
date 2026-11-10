from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT, domain, err


def search_hn(query: str = "", sort: str = "popular", limit: int = 5) -> dict[str, Any]:
    try:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")
        limit = max(1, min(int(limit or 5), 20))  # accepts "5", clamps 0 -> 1
        endpoint = "search_by_date" if sort == "latest" else "search"
        response = requests.get(
            f"https://hn.algolia.com/api/v1/{endpoint}",
            params={"query": query.strip(), "tags": "story", "hitsPerPage": limit},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        items = []
        for hit in response.json().get("hits", [])[:limit]:
            url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
            items.append({
                "title": hit.get("title"),
                "url": url,
                "source": domain(url) or "news.ycombinator.com",
                "points": hit.get("points"),
                "comments": hit.get("num_comments"),
                "created_at": hit.get("created_at"),
            })
        return {"tool": "hn_search", "query": query, "sort": "latest" if endpoint == "search_by_date" else "popular", "items": items}
    except Exception as exc:
        return err("hn_search", exc)