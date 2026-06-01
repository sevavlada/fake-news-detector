"""Google Fact Check Tools API integration."""

from typing import List, Dict, Any
import requests

from ..config import GOOGLE_FACTCHECK_API_KEY


def google_factcheck_search(query: str) -> List[Dict[str, Any]]:
    """
    Search Google Fact Check Tools API for fact-check articles.

    Args:
        query: The claim or text to search for

    Returns:
        List of fact-check results with claim text, publisher, rating, and URL
    """
    if not GOOGLE_FACTCHECK_API_KEY:
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
        for claim in claims[:3]:
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
