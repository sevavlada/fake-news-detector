"""Shared verdict format for A/B testing.

This module defines a SINGLE canonical output schema and formatter used by
BOTH the multi-agent Fake News Detector and the single-LLM baseline app,
so their answers can be compared side by side in an A/B test.

Canonical schema (JSON):
{
  "claim": "<the checked statement>",
  "verdict": "TRUE | FALSE | MIXED | UNVERIFIABLE",
  "confidence": <int 0-100>,
  "key_factors": ["factor 1", "factor 2", ...],
  "reasoning": "<explanation>"
}
"""

import json
from typing import Any, Dict, List

VERDICTS = ("TRUE", "FALSE", "MIXED", "MANIPULATION", "UNVERIFIABLE")


def normalize_verdict(claim: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Coerce an arbitrary LLM/agent result dict into the canonical schema.

    Accepts both keys used across the codebase ("verdict" and "final_verdict").
    """
    verdict = str(
        data.get("verdict") or data.get("final_verdict") or "UNVERIFIABLE"
    ).strip().upper()
    if verdict not in VERDICTS:
        verdict = "UNVERIFIABLE"

    try:
        confidence = int(data.get("confidence", 0))
    except (TypeError, ValueError):
        confidence = 0
    confidence = max(0, min(100, confidence))

    factors = data.get("key_factors") or []
    if isinstance(factors, str):
        factors = [factors]
    key_factors: List[str] = [str(f).strip() for f in factors if str(f).strip()]

    reasoning = str(data.get("reasoning", "")).strip()

    return {
        "claim": claim,
        "verdict": verdict,
        "confidence": confidence,
        "key_factors": key_factors,
        "reasoning": reasoning,
    }


def verdict_to_json(verdict: Dict[str, Any]) -> str:
    """Serialize a canonical verdict to a stable JSON string."""
    return json.dumps(normalize_verdict(verdict.get("claim", ""), verdict),
                      ensure_ascii=False, indent=2)


def format_verdict(verdict: Dict[str, Any], source: str = "") -> str:
    """Render a canonical verdict as a human-readable text block.

    `source` is an optional label (e.g. "Fake News Detector (Arch B)"
    or "Baseline LLM") shown in the header so A/B outputs are easy to tell apart.
    """
    v = normalize_verdict(verdict.get("claim", ""), verdict)

    header = "FACT-CHECK RESULT" + (f" — {source}" if source else "")
    factors = v["key_factors"]
    factors_block = (
        "\n".join(f"  - {f}" for f in factors) if factors else "  - N/A"
    )

    lines = [
        "=" * 60,
        header,
        "=" * 60,
        f"Claim:      {v['claim']}",
        f"Verdict:    {v['verdict']}",
        f"Confidence: {v['confidence']}%",
        "Key factors:",
        factors_block,
        "Reasoning:",
        f"  {v['reasoning']}",
        "=" * 60,
    ]
    return "\n".join(lines)
