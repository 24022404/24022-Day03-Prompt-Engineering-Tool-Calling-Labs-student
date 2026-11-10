from __future__ import annotations

from typing import Any
from urllib.parse import quote

import requests

from tools._shared import TIMEOUT, err

HEADERS = {"User-Agent": "AI20k-Day03-Research-Agent/1.0 (educational lab)"}


def wiki_summary(title: str = "", lang: str = "en") -> dict[str, Any]:
    try:
        if not isinstance(title, str) or not title.strip():
            raise ValueError("title must be a non-empty string")
        lang = lang if lang in ("en", "vi") else "en"
        url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{quote(title.strip().replace(' ', '_'))}"
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if response.status_code == 404:
            return {"tool": "wiki", "title": title, "lang": lang, "found": False, "summary": None, "url": None}
        response.raise_for_status()
        data = response.json()
        return {
            "tool": "wiki",
            "title": data.get("title") or title,
            "lang": lang,
            "found": True,
            "summary": data.get("extract"),
            "url": ((data.get("content_urls") or {}).get("desktop") or {}).get("page"),
        }
    except Exception as exc:
        return err("wiki", exc)