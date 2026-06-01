"""Base agent utilities and shared functionality."""

import json
from typing import Any, Dict

from ..state import FakeNewsAgentState


def extract_query(state: FakeNewsAgentState) -> str:
    """Extract the query text from state, checking multiple sources."""
    query = state.get("query") or ""
    if query.strip():
        return query.strip()

    for msg in reversed(state.get("messages", []) or []):
        content = getattr(msg, "content", None)
        if content is None and isinstance(msg, dict):
            content = msg.get("content")
        if content:
            return str(content).strip()

    return ""


def parse_json_response(raw: Any) -> Dict[str, Any]:
    """Parse LLM response as JSON, handling markdown code blocks."""
    if isinstance(raw, dict):
        return raw

    if not isinstance(raw, str):
        return {"verdict": "UNVERIFIABLE", "confidence": 0, "reasoning": str(raw)}

    text = raw.strip()

    if text.startswith("```"):
        text = text.strip("`")
        if "\n" in text:
            first_line, rest = text.split("\n", 1)
            if first_line.lower() in ("json", ""):
                text = rest
        if text.endswith("```"):
            text = text[:-3]

    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        return {"verdict": "UNVERIFIABLE", "confidence": 0, "reasoning": raw}


def safe_get_confidence(report: Dict[str, Any]) -> int:
    """Safely extract confidence value from agent report."""
    try:
        return int(report.get("confidence", 0))
    except (TypeError, ValueError):
        return 0


class BaseAgent:
    """Base class for specialized agents (for future extensibility)."""

    def __init__(self, llm=None):
        self.llm = llm

    def process(self, state: FakeNewsAgentState) -> FakeNewsAgentState:
        raise NotImplementedError
