from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from tools._shared import err, fold_text

# (keywords after accent folding, timeframe)
_RULES: list[tuple[tuple[str, ...], str]] = [
    (("hom nay", "today", "24h", "24 gio"), "day"),
    (("hom qua", "yesterday"), "day"),
    (("tuan nay", "tuan qua", "this week", "past week", "7 ngay"), "week"),
    (("thang nay", "thang qua", "this month", "past month", "30 ngay"), "month"),
    (("nam nay", "nam qua", "this year", "past year"), "year"),
]


def resolve_date_range(phrase: str = "", today: str = "") -> dict[str, Any]:
    try:
        if not isinstance(phrase, str) or not phrase.strip():
            raise ValueError("phrase must be a non-empty string")
        base = date.fromisoformat(today) if today else date.today()
        folded = fold_text(phrase)

        timeframe = None
        for keywords, tf in _RULES:
            if any(k in folded for k in keywords):
                timeframe = tf
                if "hom qua" in folded or "yesterday" in folded:
                    base = base - timedelta(days=1)
                break
        if timeframe is None:
            return {"tool": "date_range", "phrase": phrase, "timeframe": None, "start_date": None, "end_date": None,
                    "note": "Unrecognised time phrase; ask the user or omit timeframe."}

        if timeframe == "day":
            start = base
        elif timeframe == "week":
            start = base - timedelta(days=base.weekday())
        elif timeframe == "month":
            start = base.replace(day=1)
        else:
            start = base.replace(month=1, day=1)
        return {"tool": "date_range", "phrase": phrase, "timeframe": timeframe,
                "start_date": start.isoformat(), "end_date": base.isoformat()}
    except Exception as exc:
        return err("date_range", exc)