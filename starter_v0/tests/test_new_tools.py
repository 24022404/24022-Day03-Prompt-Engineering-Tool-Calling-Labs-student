"""Unit tests for the team's new tools: handle_resolve, date_range, wiki, hn_search."""
from __future__ import annotations

import requests

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS

handle_resolve = TOOL_FUNCTIONS["handle_resolve"]
date_range = TOOL_FUNCTIONS["date_range"]
wiki = TOOL_FUNCTIONS["wiki"]
hn_search = TOOL_FUNCTIONS["hn_search"]


# ---------------- handle_resolve ----------------

def test_handle_resolve_maps_known_name_case_and_accent_insensitive() -> None:
    assert handle_resolve(name="Sam Altman")["handle"] == "sama"
    assert handle_resolve(name="  ANDREJ   karpathy ")["handle"] == "karpathy"


def test_handle_resolve_strips_at_sign_from_existing_handle() -> None:
    result = handle_resolve(name="@elonmusk")
    assert result["found"] is True
    assert result["handle"] == "elonmusk"


def test_handle_resolve_unknown_name_returns_not_found_instead_of_guessing() -> None:
    result = handle_resolve(name="Nguyen Van A")
    assert result["found"] is False
    assert result["handle"] is None


def test_handle_resolve_empty_or_wrong_type_does_not_raise() -> None:
    assert handle_resolve(name="")["found"] is False
    assert handle_resolve(name=123)["error"] == "TypeError"


# ---------------- date_range ----------------

def test_date_range_today_vietnamese() -> None:
    result = date_range(phrase="Tin AI hôm nay", today="2026-11-10")
    assert result["timeframe"] == "day"
    assert result["start_date"] == result["end_date"] == "2026-11-10"


def test_date_range_this_week_starts_on_monday() -> None:
    result = date_range(phrase="tuần này", today="2026-11-12")  # Thursday
    assert result["timeframe"] == "week"
    assert result["start_date"] == "2026-11-09"
    assert result["end_date"] == "2026-11-12"


def test_date_range_month_and_year() -> None:
    assert date_range(phrase="this month", today="2026-11-10")["start_date"] == "2026-11-01"
    assert date_range(phrase="năm nay", today="2026-11-10")["start_date"] == "2026-01-01"


def test_date_range_bad_input_returns_error_or_none() -> None:
    assert date_range(phrase="")["error"] == "ValueError"
    assert date_range(phrase="hôm nay", today="not-a-date")["error"] == "ValueError"
    assert date_range(phrase="lúc nào đó")["timeframe"] is None


# ---------------- wiki ----------------

def test_wiki_sends_expected_request_and_maps_summary(fake_http) -> None:
    calls = fake_http(FakeResponse({
        "title": "Sam Altman", "extract": "American entrepreneur.",
        "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Sam_Altman"}},
    }))
    result = wiki(title="Sam Altman")

    assert calls[0]["method"] == "GET"
    assert calls[0]["url"] == "https://en.wikipedia.org/api/rest_v1/page/summary/Sam_Altman"
    assert "User-Agent" in calls[0]["headers"]
    assert result["found"] is True
    assert result["summary"] == "American entrepreneur."
    assert result["url"] == "https://en.wikipedia.org/wiki/Sam_Altman"


def test_wiki_404_returns_not_found(fake_http) -> None:
    fake_http(FakeResponse(status_code=404))
    result = wiki(title="Không tồn tại xyz", lang="vi")
    assert result["found"] is False
    assert result["lang"] == "vi"


def test_wiki_empty_title_and_bad_lang(fake_http) -> None:
    calls = fake_http(FakeResponse({"title": "AI", "extract": "x"}))
    assert wiki(title="")["error"] == "ValueError"
    assert calls == []
    wiki(title="AI", lang="fr")
    assert calls[0]["url"].startswith("https://en.wikipedia.org/")


def test_wiki_http_error_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=500))
    assert wiki(title="AI")["error"] == "HTTPError"


# ---------------- hn_search ----------------

def test_hn_search_sends_expected_request_and_maps_hits(fake_http) -> None:
    calls = fake_http(FakeResponse({"hits": [
        {"title": "Show HN: X", "url": "https://www.example.com/x", "points": 120, "num_comments": 30,
         "created_at": "2026-11-10T01:00:00Z", "objectID": "1"},
        {"title": "Ask HN: Y", "url": None, "points": 5, "num_comments": 2, "created_at": "2026-11-10", "objectID": "42"},
    ]}))
    result = hn_search(query="Rust", sort="popular", limit=2)

    assert calls[0]["url"] == "https://hn.algolia.com/api/v1/search"
    assert calls[0]["params"] == {"query": "Rust", "tags": "story", "hitsPerPage": 2}
    assert result["items"][0]["source"] == "example.com"
    assert result["items"][0]["points"] == 120
    assert result["items"][1]["url"] == "https://news.ycombinator.com/item?id=42"


def test_hn_search_latest_uses_search_by_date_and_clamps_limit(fake_http) -> None:
    calls = fake_http(FakeResponse({"hits": []}))
    hn_search(query="AI", sort="latest", limit="0")
    assert calls[0]["url"] == "https://hn.algolia.com/api/v1/search_by_date"
    assert calls[0]["params"]["hitsPerPage"] == 1


def test_hn_search_empty_query_does_not_call_network(fake_http) -> None:
    calls = fake_http(FakeResponse({"hits": []}))
    assert hn_search(query="  ")["error"] == "ValueError"
    assert calls == []


def test_hn_search_network_error_returns_error_dict(fake_http) -> None:
    fake_http(requests.ConnectionError("down"))
    assert hn_search(query="AI")["error"] == "ConnectionError"