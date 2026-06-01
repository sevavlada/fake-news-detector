"""Architecture A: Router-based adaptive agent selection.

The meta-LLM router analyzes the input and selects the single most
appropriate agent for verification. This is efficient but relies
heavily on the router's judgment.

Flow: START -> router -> (D | T | C) -> END
"""

from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, START, END

from ..state import FakeNewsAgentState
from ..config import get_llm
from ..prompts import ROUTER_PROMPT
from ..agents import agent_d_node, agent_t_node, agent_c_node


def router_node(state: FakeNewsAgentState) -> Dict[str, Any]:
    """
    Router node that selects the most appropriate agent.

    Analyzes the input text and decides which verification method
    would be most effective:
    - D: for factual claims with verifiable data
    - T: for manipulative language and emotional content
    - C: for source/context-related concerns
    """
    print("--- [Router] Analyzing content type ---")

    query = state.get("query", "").strip()
    messages = state.get("messages", []) or []

    if not query:
        return {
            **state,
            "selected_agent": "D",
            "routing_reason": "Default (empty query)",
            "messages": messages + ["router: default selection D (empty query)"],
        }

    llm = get_llm()
    prompt = ROUTER_PROMPT.format(news_text=query)

    try:
        response = llm.invoke(prompt)
        raw_output = response.content
    except Exception as e:
        print(f"Router LLM error: {e}")
        raw_output = ""

    selected = "D"
    reason = "Default selection"

    for line in raw_output.split("\n"):
        if "ВЫБРАННЫЙ АГЕНТ:" in line or "SELECTED AGENT:" in line.upper():
            agent_letter = line.split(":")[-1].strip().upper()
            if agent_letter in ["D", "T", "C"]:
                selected = agent_letter
        if "ПРИЧИНА:" in line or "REASON:" in line.upper():
            reason = line.split(":", 1)[-1].strip()

    print(f"    -> Selected agent: {selected}")
    try:
        print(f"    -> Reason: {reason}")
    except UnicodeEncodeError:
        print(f"    -> Reason: {reason.encode('ascii', 'replace').decode()}")

    return {
        **state,
        "selected_agent": selected,
        "routing_reason": reason,
        "messages": messages + [f"router: selected agent {selected} - {reason}"],
    }


def route_to_agent(state: FakeNewsAgentState) -> Literal["agent_d", "agent_t", "agent_c"]:
    """Conditional routing function based on selected agent."""
    selected = state.get("selected_agent", "D")
    if selected == "T":
        return "agent_t"
    elif selected == "C":
        return "agent_c"
    return "agent_d"


def finalize_node(state: FakeNewsAgentState) -> Dict[str, Any]:
    """Finalize the result from whichever agent was selected."""
    selected = state.get("selected_agent", "D")

    if selected == "D":
        result = state.get("agent_d_result", "")
    elif selected == "T":
        result = state.get("agent_t_result", "")
    else:
        result = state.get("agent_c_result", "")

    return {
        **state,
        "final_verdict": result,
    }


def create_router_graph() -> StateGraph:
    """
    Create Architecture A: Router-based graph.

    Returns a compiled StateGraph with conditional routing.
    """
    builder = StateGraph(FakeNewsAgentState)

    builder.add_node("router", router_node)
    builder.add_node("agent_d", agent_d_node)
    builder.add_node("agent_t", agent_t_node)
    builder.add_node("agent_c", agent_c_node)
    builder.add_node("finalize", finalize_node)

    builder.add_edge(START, "router")
    builder.add_conditional_edges("router", route_to_agent)
    builder.add_edge("agent_d", "finalize")
    builder.add_edge("agent_t", "finalize")
    builder.add_edge("agent_c", "finalize")
    builder.add_edge("finalize", END)

    return builder.compile()
