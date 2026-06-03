"""Agent D: Data-based Cross-checking.

Verifies factual claims using external sources:
- Google Fact Check Tools (keyword search)
- Web-search fallback (Wikipedia by default) when Google returns too little
"""

import json
from typing import Dict, Any
from langchain.messages import AIMessage

from ..state import FakeNewsAgentState
from ..config import get_llm
from ..prompts import AGENT_D_PROMPT, AGENT_D_KEYWORDS_PROMPT, AGENT_D_FACTUAL_PROMPT
from ..integrations import google_factcheck_multi, web_fallback
from .base import extract_query, parse_json_response, safe_get_confidence

# Minimum number of solid results before we trust the primary sources;
# below this, Agent D asks the web-search fallback for more evidence.
MIN_PRIMARY_RESULTS = 2


def classify_factual(query: str, llm) -> str:
    """Replaces the removed ClaimBuster: is this claim checkable or just opinion?

    Returns "factual" or "non_factual" (defaults to "factual" on any error).
    """
    try:
        response = llm.invoke(AGENT_D_FACTUAL_PROMPT.format(claim=query))
        answer = str(response.content).strip().lower()
        return "non_factual" if "non_factual" in answer or "non-factual" in answer else "factual"
    except Exception as e:
        print(f"Factual classification error: {e}")
        return "factual"


# Phrases that signal the LLM refused the topic (e.g. Yandex's safety filter on
# political claims) instead of returning keywords. We must not search for these.
_REFUSAL_MARKERS = (
    "не могу", "поговорим о", "обсуждать эту тему", "не буду",
    "as an ai", "i cannot", "i can't", "i'm sorry", "cannot discuss",
)


def extract_keywords(query: str, llm) -> str:
    """Turn a full claim into a short keyword query for Google Fact Check.

    Falls back to the raw claim if the LLM call fails, returns nothing, or
    refuses the topic (so we don't search for a refusal message).
    """
    try:
        response = llm.invoke(AGENT_D_KEYWORDS_PROMPT.format(claim=query))
        keywords = str(response.content).strip()
        # Keep only the first line and strip surrounding quotes.
        keywords = keywords.splitlines()[0].strip().strip('"').strip("'") if keywords else ""
        # Underscores/extra spaces hurt keyword search.
        keywords = " ".join(keywords.replace("_", " ").split())
        # If the model refused instead of giving keywords, search the raw claim.
        if any(marker in keywords.lower() for marker in _REFUSAL_MARKERS):
            print("    -> keyword step refused by model; using raw claim for search")
            return query
        return keywords or query
    except Exception as e:
        print(f"Keyword extraction error: {e}")
        return query


def agent_d_node(state: FakeNewsAgentState) -> Dict[str, Any]:
    """
    Agent D node for LangGraph.

    Performs data-based cross-checking by:
    1. Querying Google Fact Check API
    2. Aggregating results
    3. Using LLM to synthesize a verdict
    """
    print("--- Agent D: Data-based Cross-checking ---")

    query = extract_query(state)
    messages = state.get("messages", []) or []

    if not query:
        ai_msg = AIMessage(content="Agent D: empty query")
        return {
            "query": "",
            "agent_d_result": "",
            "confidence": 0,
            "protocol": {"error": "Empty query"},
            "messages": messages + [ai_msg],
        }

    llm = get_llm()

    # Is this a checkable factual claim at all? (replaces ClaimBuster)
    claim_type = classify_factual(query, llm)

    # Search Google Fact Check by extracted keywords (best match), then fall
    # back to the raw claim. Results are merged and de-duplicated.
    keywords = extract_keywords(query, llm)
    print(f"    -> Google Fact Check keywords: {keywords}")
    google_results = google_factcheck_multi([keywords, query])

    # Web fallback: only when the primary sources gave too little evidence.
    web_results = []
    web_used = len(google_results) < MIN_PRIMARY_RESULTS
    if web_used:
        web_results = web_fallback(keywords or query)

    # Task 5: log how much each source returned.
    retrieval_trace = {
        "claim_type": claim_type,
        "search_keywords": keywords,
        "google_factcheck_count": len(google_results),
        "web_fallback_used": web_used,
        "web_results_count": len(web_results),
    }
    print(f"    -> Retrieval: google={len(google_results)}, "
          f"web_fallback={'on' if web_used else 'off'}({len(web_results)})")

    aggregated_data = {
        "search_keywords": keywords,
        "google_factcheck": google_results,
        "web_search": web_results,
    }
    retrieved_context = json.dumps(aggregated_data, ensure_ascii=False, indent=2)

    prompt = AGENT_D_PROMPT.format(query=query, retrieved_context=retrieved_context)

    try:
        response = llm.invoke(prompt)
        agent_report = parse_json_response(response.content)
    except Exception as e:
        agent_report = {
            "verdict": "UNVERIFIABLE",
            "confidence": 0,
            "reasoning": f"LLM error: {e}",
        }

    confidence = safe_get_confidence(agent_report)
    verdict = agent_report.get("verdict", "UNVERIFIABLE")
    reasoning = agent_report.get("reasoning", "")
    result_text = f"[Agent D] {verdict} ({confidence}%): {reasoning}"

    ai_msg = AIMessage(content=result_text)

    # Top evidence sources for the verification protocol.
    sources = []
    for r in google_results:
        if r.get("url"):
            sources.append({"url": r["url"], "publisher": r.get("publisher"),
                            "rating": r.get("rating")})
    for r in web_results:
        if r.get("url"):
            sources.append({"url": r["url"], "publisher": r.get("source")})

    d_protocol = {
        "method": "Data-based Cross-checking",
        "verdict": verdict,
        "confidence": confidence,
        "reasoning": reasoning,
        "sources": sources[:5],
        "retrieval_trace": retrieval_trace,
        "agent_report": agent_report,
    }
    # Accumulate per-agent reports (don't overwrite other agents' protocols).
    protocol = {**(state.get("protocol") or {}), "D": d_protocol}

    return {
        "query": query,
        "agent_d_result": result_text,
        "confidence": confidence,
        "protocol": protocol,
        "messages": messages + [ai_msg],
    }
