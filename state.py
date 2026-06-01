"""State definitions for the fake news detection system."""

from typing import TypedDict, List, Any
from langchain.messages import AnyMessage


class FakeNewsAgentState(TypedDict):
    """State schema for the multi-agent fake news detection system."""

    query: str
    selected_agent: str
    routing_reason: str
    agent_d_result: str
    agent_t_result: str
    agent_c_result: str
    final_verdict: str
    confidence: int
    protocol: dict
    messages: List[AnyMessage]


def create_initial_state(query: str) -> FakeNewsAgentState:
    """Create an initial state with the given query."""
    return FakeNewsAgentState(
        query=query,
        selected_agent="",
        routing_reason="",
        agent_d_result="",
        agent_t_result="",
        agent_c_result="",
        final_verdict="",
        confidence=0,
        protocol={},
        messages=[],
    )
