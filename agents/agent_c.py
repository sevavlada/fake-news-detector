"""Agent C: Contextual & Source Analysis.

Analyzes source reliability and logical coherence:
- Source assessment
- Contextual analysis
- Temporal context
- Security analysis (prompt injection detection)
"""

import re
from typing import Dict, Any, List
from langchain.messages import AIMessage

from ..state import FakeNewsAgentState
from ..config import get_llm
from ..prompts import AGENT_C_PROMPT
from .base import extract_query, parse_json_response, safe_get_confidence

CAUSAL_MARKERS = ["because", "therefore", "thus", "since", "потому что", "следовательно", "поэтому"]
CONTRAST_MARKERS = ["however", "but", "although", "nevertheless", "однако", "но", "хотя"]
ABSOLUTIST_MARKERS = ["always", "never", "definitely", "undoubtedly", "всегда", "никогда", "определённо"]


def compute_coherence_metrics(text: str) -> Dict[str, Any]:
    """Compute coherence and structural metrics for the text."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    sentence_lengths = [len(s.split()) for s in sentences]
    avg_length = sum(sentence_lengths) / max(len(sentence_lengths), 1)

    text_lower = text.lower()

    return {
        "sentence_count": len(sentences),
        "avg_sentence_length": round(avg_length, 2),
        "causal_marker_count": sum(text_lower.count(m) for m in CAUSAL_MARKERS),
        "contrast_marker_count": sum(text_lower.count(m) for m in CONTRAST_MARKERS),
        "absolutist_marker_count": sum(text_lower.count(m) for m in ABSOLUTIST_MARKERS),
    }


def detect_prompt_injection(text: str) -> List[str]:
    """Detect potential prompt injection patterns."""
    suspicious_patterns = [
        r"ignore\s+(previous|all)\s+instructions",
        r"forget\s+(everything|all)",
        r"you\s+are\s+now",
        r"new\s+instructions",
        r"override\s+",
        r"system\s*:\s*",
    ]

    findings = []
    text_lower = text.lower()

    for pattern in suspicious_patterns:
        if re.search(pattern, text_lower):
            findings.append(f"Potential injection pattern: {pattern}")

    return findings


def agent_c_node(state: FakeNewsAgentState) -> Dict[str, Any]:
    """
    Agent C node for LangGraph.

    Performs contextual and source analysis by:
    1. Computing coherence metrics
    2. Detecting prompt injection attempts
    3. Using LLM to assess source reliability
    """
    print("--- Agent C: Contextual & Source Analysis ---")

    text = extract_query(state)
    messages = state.get("messages", []) or []

    if not text:
        ai_msg = AIMessage(content="Agent C: empty text")
        return {
            "agent_c_result": "",
            "confidence": 0,
            "protocol": {"error": "Empty text"},
            "messages": messages + [ai_msg],
        }

    metrics = compute_coherence_metrics(text)
    security_findings = detect_prompt_injection(text)

    if security_findings:
        metrics["security_warnings"] = security_findings

    llm = get_llm()
    prompt = AGENT_C_PROMPT.format(text=text, metrics=metrics)

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
    risk_level = agent_report.get("coherence_risk_level", "unknown")
    reasoning = agent_report.get("reasoning", "")
    result_text = f"[Agent C] {verdict} ({confidence}%), risk: {risk_level}: {reasoning}"

    ai_msg = AIMessage(content=result_text)

    protocol = {
        "agent": "C",
        "method": "Contextual & Source Analysis",
        "metrics": metrics,
        "security_findings": security_findings,
        "agent_report": agent_report,
    }

    return {
        "agent_c_result": result_text,
        "confidence": confidence,
        "protocol": protocol,
        "messages": messages + [ai_msg],
    }
