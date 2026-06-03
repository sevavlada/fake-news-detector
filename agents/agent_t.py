"""Agent T: Textual & Discourse Analysis.

Analyzes linguistic patterns and manipulation markers:
- Sentiment analysis
- Toxicity detection
- Discursive markers
- Rhetorical structure
"""

import os
from typing import Dict, Any
from langchain.messages import AIMessage

from ..state import FakeNewsAgentState
from ..config import get_llm
from ..prompts import AGENT_T_PROMPT
from ..markers import detect_markers
from .base import extract_query, parse_json_response, safe_get_confidence

_sentiment_model = None
_toxicity_model = None


def _ml_models_enabled() -> bool:
    """The optional transformers/torch models are OFF by default.

    On some machines (notably macOS) loading torch can hard-crash the
    process with a "bus error" that Python cannot catch. The models are
    optional — Agent T works on lexical markers + the LLM without them.
    Set ENABLE_T_ML_MODELS=1 to opt back in.
    """
    return os.getenv("ENABLE_T_ML_MODELS", "").lower() in ("1", "true", "yes")


def _get_sentiment_model():
    """Lazy load sentiment analysis model (only if explicitly enabled)."""
    global _sentiment_model
    if not _ml_models_enabled():
        return None
    if _sentiment_model is None:
        try:
            from transformers import pipeline
            _sentiment_model = pipeline("sentiment-analysis")
        except Exception as e:
            print(f"Failed to load sentiment model: {e}")
            return None
    return _sentiment_model


def _get_toxicity_model():
    """Lazy load toxicity detection model (only if explicitly enabled)."""
    global _toxicity_model
    if not _ml_models_enabled():
        return None
    if _toxicity_model is None:
        try:
            from transformers import pipeline
            _toxicity_model = pipeline("text-classification", model="unitary/toxic-bert")
        except Exception as e:
            print(f"Failed to load toxicity model: {e}")
            return None
    return _toxicity_model


def compute_text_metrics(text: str) -> Dict[str, Any]:
    """Compute linguistic metrics for the text."""
    metrics = {
        "exclamation_count": text.count("!"),
        "uppercase_ratio": sum(1 for c in text if c.isupper()) / max(len(text), 1),
        "question_count": text.count("?"),
        "text_length": len(text),
    }

    marker_result = detect_markers(text)
    metrics["manipulation_markers"] = marker_result["markers_by_category"]
    metrics["marker_counts"] = marker_result["marker_counts"]
    metrics["total_markers"] = marker_result["total_markers"]

    sentiment_model = _get_sentiment_model()
    if sentiment_model:
        try:
            result = sentiment_model(text[:512])[0]
            metrics["sentiment_label"] = result["label"]
            metrics["sentiment_score"] = result["score"]
        except Exception:
            metrics["sentiment_label"] = "UNKNOWN"
            metrics["sentiment_score"] = 0.0

    toxicity_model = _get_toxicity_model()
    if toxicity_model:
        try:
            result = toxicity_model(text[:512])[0]
            metrics["toxicity_label"] = result["label"]
            metrics["toxicity_score"] = result["score"]
        except Exception:
            metrics["toxicity_label"] = "UNKNOWN"
            metrics["toxicity_score"] = 0.0

    return metrics


def agent_t_node(state: FakeNewsAgentState) -> Dict[str, Any]:
    """
    Agent T node for LangGraph.

    Performs textual and discourse analysis by:
    1. Computing sentiment and toxicity metrics
    2. Analyzing linguistic patterns
    3. Using LLM to assess manipulation risk
    """
    print("--- Agent T: Textual & Discourse Analysis ---")

    text = extract_query(state)
    messages = state.get("messages", []) or []

    if not text:
        ai_msg = AIMessage(content="Agent T: empty text")
        return {
            "agent_t_result": "",
            "confidence": 0,
            "protocol": {"error": "Empty text"},
            "messages": messages + [ai_msg],
        }

    metrics = compute_text_metrics(text)

    llm = get_llm()
    prompt = AGENT_T_PROMPT.format(text=text, metrics=metrics)

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
    risk_level = agent_report.get("linguistic_risk_level", "unknown")
    reasoning = agent_report.get("reasoning", "")
    result_text = f"[Agent T] {verdict} ({confidence}%), risk: {risk_level}: {reasoning}"

    ai_msg = AIMessage(content=result_text)

    protocol = {
        "agent": "T",
        "method": "Textual & Discourse Analysis",
        "metrics": metrics,
        "agent_report": agent_report,
    }

    return {
        "agent_t_result": result_text,
        "confidence": confidence,
        "protocol": protocol,
        "messages": messages + [ai_msg],
    }
