"""Architecture B: Synchronous multi-agent synthesis.

All three agents analyze the input in parallel, then a synthesizer
combines their findings into a unified verdict. This is more
thorough but computationally heavier.

Flow: START -> [D, T, C parallel] -> synthesizer -> END
"""

from typing import Dict, Any
from langgraph.graph import StateGraph, START, END
from langchain.messages import AIMessage

from ..state import FakeNewsAgentState
from ..config import get_llm
from ..prompts import SYNTHESIZER_PROMPT
from ..agents import agent_d_node, agent_t_node, agent_c_node
from ..agents.base import parse_json_response, safe_get_confidence


def synthesizer_node(state: FakeNewsAgentState) -> Dict[str, Any]:
    """
    Synthesizer node that combines all agent results.

    Takes the outputs from all three agents and produces a
    unified verdict with explanations of agreements/disagreements.
    """
    print("--- [Synthesizer] Combining agent results ---")

    messages = state.get("messages", []) or []

    agent_d_result = state.get("agent_d_result", "No result from Agent D")
    agent_t_result = state.get("agent_t_result", "No result from Agent T")
    agent_c_result = state.get("agent_c_result", "No result from Agent C")

    llm = get_llm()
    prompt = SYNTHESIZER_PROMPT.format(
        agent_d_result=agent_d_result,
        agent_t_result=agent_t_result,
        agent_c_result=agent_c_result,
    )

    try:
        response = llm.invoke(prompt)
        synthesis = parse_json_response(response.content)
    except Exception as e:
        synthesis = {
            "final_verdict": "UNVERIFIABLE",
            "confidence": 0,
            "reasoning": f"Synthesis error: {e}",
        }

    final_verdict = synthesis.get("final_verdict", "UNVERIFIABLE")
    confidence = safe_get_confidence(synthesis)
    agreement = synthesis.get("agent_agreement", "unknown")
    key_factors = synthesis.get("key_factors", [])
    reasoning = synthesis.get("reasoning", "")

    result_text = (
        f"[FINAL] {final_verdict} ({confidence}%)\n"
        f"Agent agreement: {agreement}\n"
        f"Key factors: {', '.join(key_factors) if key_factors else 'N/A'}\n"
        f"Reasoning: {reasoning}"
    )

    ai_msg = AIMessage(content=result_text)

    protocol = state.get("protocol", {})
    protocol["synthesis"] = synthesis

    return {
        **state,
        "final_verdict": result_text,
        "confidence": confidence,
        "protocol": protocol,
        "messages": messages + [ai_msg],
    }


def create_parallel_graph() -> StateGraph:
    """
    Create Architecture B: Parallel synthesis graph.

    Note: LangGraph doesn't natively support parallel execution
    in the same way as asyncio. This implementation runs agents
    sequentially but collects all results before synthesis.

    For true parallelism, consider using async nodes or
    ThreadPoolExecutor within a single node.

    Returns a compiled StateGraph.
    """
    builder = StateGraph(FakeNewsAgentState)

    builder.add_node("agent_d", agent_d_node)
    builder.add_node("agent_t", agent_t_node)
    builder.add_node("agent_c", agent_c_node)
    builder.add_node("synthesizer", synthesizer_node)

    builder.add_edge(START, "agent_d")
    builder.add_edge("agent_d", "agent_t")
    builder.add_edge("agent_t", "agent_c")
    builder.add_edge("agent_c", "synthesizer")
    builder.add_edge("synthesizer", END)

    return builder.compile()


def create_truly_parallel_graph() -> StateGraph:
    """
    Alternative: Create a parallel graph using fan-out/fan-in pattern.

    This uses LangGraph's ability to have multiple edges from START,
    though execution order depends on the runtime.
    """
    from langgraph.graph import StateGraph

    builder = StateGraph(FakeNewsAgentState)

    def combined_agents_node(state: FakeNewsAgentState) -> Dict[str, Any]:
        """Run all agents and combine results."""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(agent_d_node, state): "D",
                executor.submit(agent_t_node, state): "T",
                executor.submit(agent_c_node, state): "C",
            }

            results = {}
            for future in as_completed(futures):
                agent_name = futures[future]
                try:
                    results[agent_name] = future.result()
                except Exception as e:
                    print(f"Agent {agent_name} error: {e}")
                    results[agent_name] = {}

        combined_state = {**state}
        if "D" in results:
            combined_state["agent_d_result"] = results["D"].get("agent_d_result", "")
        if "T" in results:
            combined_state["agent_t_result"] = results["T"].get("agent_t_result", "")
        if "C" in results:
            combined_state["agent_c_result"] = results["C"].get("agent_c_result", "")

        all_messages = state.get("messages", []) or []
        for r in results.values():
            all_messages.extend(r.get("messages", []))
        combined_state["messages"] = all_messages

        return combined_state

    builder.add_node("parallel_agents", combined_agents_node)
    builder.add_node("synthesizer", synthesizer_node)

    builder.add_edge(START, "parallel_agents")
    builder.add_edge("parallel_agents", "synthesizer")
    builder.add_edge("synthesizer", END)

    return builder.compile()
