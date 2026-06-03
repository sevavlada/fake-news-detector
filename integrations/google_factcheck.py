"""Google Fact Check Tools API integration."""

from typing import List, Dict, Any
import requests

from ..config import GOOGLE_FACTCHECK_API_KEY


def google_factcheck_search(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Search Google Fact Check Tools API for fact-check articles.

    Args:
        query: Keywords to search for (works best as keywords, not a full sentence)
        max_results: Maximum number of claims to read from the response

    Returns:
        List of fact-check results with claim text, publisher, rating, and URL
    """
    if not GOOGLE_FACTCHECK_API_KEY or not query.strip():
        return []

    url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
    params = {
        "query": query,
        "key": GOOGLE_FACTCHECK_API_KEY,
        "languageCode": "en",
    }

    try:
        response = requests.get(url, params=params, timeout=10)

        if response.status_code != 200:
            print(f"Google API error: {response.status_code}")
            return []

        data = response.json()
        claims = data.get("claims", [])

        results = []
        for claim in claims[:max_results]:
            claim_text = claim.get("text", "")
            reviews = claim.get("claimReview", [])

            for review in reviews:
                results.append({
                    "claim_text": claim_text,
                    "publisher": review.get("publisher", {}).get("name"),
                    "rating": review.get("textualRating"),
                    "url": review.get("url"),
                })

        return results

    except Exception as e:
        print(f"Google API exception: {e}")
        return []


def google_factcheck_multi(queries: List[str], max_results: int = 5) -> List[Dict[str, Any]]:
    """Run several queries and merge their results, de-duplicated by URL.

    Lets Agent D try a keyword query first and fall back to others without
    returning the same fact-check article twice.
    """
    seen = set()
    merged: List[Dict[str, Any]] = []
    for q in queries:
        if not q or not q.strip():
            continue
        for item in google_factcheck_search(q, max_results=max_results):
            key = item.get("url") or (item.get("claim_text"), item.get("publisher"))
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)
        if len(merged) >= max_results:
            break
    return merged[:max_results]
