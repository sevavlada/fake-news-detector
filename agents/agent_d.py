"""Agent D: Data-based Cross-checking.

Verifies factual claims using external databases and APIs:
- Google Fact Check Tools
- Local indices (FEVER/LIAR when available)
"""

import json
from typing import Dict, Any
from langchain.messages import AIMessage

from ..state import FakeNewsAgentState
from ..config import get_llm
from ..prompts import AGENT_D_PROMPT
from ..integrations import google_factcheck_search
from .base import extract_query, parse_json_response, safe_get_confidence


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

    google_results = google_factcheck_search(query)

    aggregated_data = {
        "google_factcheck": google_results,
    }
    retrieved_context = json.dumps(aggregated_data, ensure_ascii=False, indent=2)

    llm = get_llm()
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

    protocol = {
        "agent": "D",
        "method": "Data-based Cross-checking",
        "retrieved_context": aggregated_data,
        "agent_report": agent_report,
    }

    return {
        "query": query,
        "agent_d_result": result_text,
        "confidence": confidence,
        "protocol": protocol,
        "messages": messages + [ai_msg],
    }
