"""Utility functions for the fake news detection system."""

import json
import sys
from typing import Dict, Any


def safe_str(text: str) -> str:
    """Convert text to be safely printable on Windows console."""
    if sys.platform == "win32":
        try:
            text.encode(sys.stdout.encoding or "utf-8")
            return text
        except (UnicodeEncodeError, LookupError):
            return text.encode("ascii", "replace").decode("ascii")
    return text


def format_result(state: Dict[str, Any], verbose: bool = False) -> str:
    """Format the final result for display."""
    lines = []
    lines.append("=" * 60)
    lines.append("FAKE NEWS DETECTION RESULT")
    lines.append("=" * 60)

    query = state.get("query", "N/A")
    lines.append(f"\nQuery: {query[:100]}{'...' if len(query) > 100 else ''}")

    if state.get("selected_agent"):
        lines.append(f"\nSelected Agent: {state['selected_agent']}")
        lines.append(f"Routing Reason: {state.get('routing_reason', 'N/A')}")

    lines.append(f"\n{'=' * 60}")
    lines.append("FINAL VERDICT")
    lines.append("=" * 60)
    lines.append(state.get("final_verdict", "No verdict"))

    if verbose:
        lines.append(f"\n{'=' * 60}")
        lines.append("DETAILED RESULTS")
        lines.append("=" * 60)

        if state.get("agent_d_result"):
            lines.append(f"\nAgent D: {state['agent_d_result']}")
        if state.get("agent_t_result"):
            lines.append(f"\nAgent T: {state['agent_t_result']}")
        if state.get("agent_c_result"):
            lines.append(f"\nAgent C: {state['agent_c_result']}")

        if state.get("protocol"):
            lines.append(f"\n{'=' * 60}")
            lines.append("PROTOCOL")
            lines.append("=" * 60)
            lines.append(json.dumps(state["protocol"], indent=2, ensure_ascii=False))

    lines.append("\n" + "=" * 60)
    return safe_str("\n".join(lines))


def display_graph(graph, filename: str = None):
    """Display or save the graph visualization."""
    try:
        from IPython.display import Image, display
        img = graph.get_graph().draw_mermaid_png()
        if filename:
            with open(filename, "wb") as f:
                f.write(img)
            print(f"Graph saved to {filename}")
        else:
            display(Image(img))
    except ImportError:
        print("IPython not available. Cannot display graph.")
    except Exception as e:
        print(f"Could not generate graph: {e}")
