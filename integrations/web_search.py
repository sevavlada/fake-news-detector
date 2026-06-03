"""Web-search fallback for Agent D.

Used ONLY when the primary sources (local index / Google Fact Check) return
too little evidence. The default provider is Wikipedia, which needs no API
key and is the source FEVER claims are built on. Tavily is supported as an
opt-in provider when WEB_SEARCH_PROVIDER=tavily and TAVILY_API_KEY is set.

Returns a list of evidence dicts: {"snippet", "url", "source"}.
"""

import os
import re
from typing import List, Dict, Any

import requests

_WIKI_API = "https://en.wikipedia.org/w/api.php"
_HEADERS = {"User-Agent": "fake-news-detector/1.0 (factcheck research)"}


def _strip_html(text: str) -> str:
    """Remove the <span class="searchmatch"> markup Wikipedia adds to snippets."""
    return re.sub(r"<[^>]+>", "", text or "").strip()


def _provider() -> str:
    return os.getenv("WEB_SEARCH_PROVIDER", "wikipedia").strip().lower()


def _wikipedia_search(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Search Wikipedia and return intro extracts of the top articles."""
    try:
        resp = requests.get(_WIKI_API, headers=_HEADERS, timeout=15, params={
            "action": "query", "list": "search", "srsearch": query,
            "format": "json", "srlimit": max_results,
        })
        if resp.status_code != 200:
            print(f"Wikipedia search error: {resp.status_code}")
            return []
        hits = resp.json().get("query", {}).get("search", [])
        if not hits:
            return []

        results: List[Dict[str, Any]] = []
        # 1) Matched-sentence snippets — these often contain the exact fact,
        #    even when it is buried in the article body (not the intro).
        for hit in hits:
            snippet = _strip_html(hit.get("snippet", ""))
            if snippet:
                results.append({
                    "snippet": snippet,
                    "url": "https://en.wikipedia.org/wiki/" + hit["title"].replace(" ", "_"),
                    "source": "wikipedia",
                })

        # 2) Intro extracts of the top articles for general context.
        titles = [hit["title"] for hit in hits]
        ext = requests.get(_WIKI_API, headers=_HEADERS, timeout=15, params={
            "action": "query", "prop": "extracts", "exintro": 1, "explaintext": 1,
            "exlimit": max_results, "titles": "|".join(titles), "format": "json",
        })
        pages = ext.json().get("query", {}).get("pages", {}) if ext.status_code == 200 else {}
        for page in pages.values():
            extract = (page.get("extract") or "").strip()
            if extract:
                results.append({
                    "snippet": extract[:500],
                    "url": "https://en.wikipedia.org/wiki/" + page.get("title", "").replace(" ", "_"),
                    "source": "wikipedia",
                })
        return results[: max_results * 2]
    except Exception as e:  # noqa: BLE001
        print(f"Wikipedia exception: {e}")
        return []


def _tavily_search(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Search the web via Tavily (requires TAVILY_API_KEY)."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        print("WEB_SEARCH_PROVIDER=tavily but TAVILY_API_KEY is not set; falling back to Wikipedia.")
        return _wikipedia_search(query, max_results)
    try:
        resp = requests.post("https://api.tavily.com/search", timeout=15, json={
            "api_key": api_key, "query": query, "max_results": max_results,
        })
        if resp.status_code != 200:
            print(f"Tavily error: {resp.status_code}")
            return []
        return [{
            "snippet": (r.get("content") or "")[:500],
            "url": r.get("url"),
            "source": "tavily",
        } for r in resp.json().get("results", [])]
    except Exception as e:  # noqa: BLE001
        print(f"Tavily exception: {e}")
        return []


def web_fallback(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Return web evidence for a claim/keywords. Dispatches by provider."""
    if not query or not query.strip():
        return []
    provider = _provider()
    if provider == "none":
        return []
    if provider == "tavily":
        return _tavily_search(query, max_results)
    return _wikipedia_search(query, max_results)
