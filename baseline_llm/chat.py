#!/usr/bin/env python3
"""Single-LLM baseline fact-checker — chat-bot interface.

Runs ONLY the YandexGPT model (same as the Fake News Detector), with no
agents/router/synthesizer. Output uses the shared canonical format so it
can be A/B-compared against the multi-agent system.

Usage:
    python baseline_llm/chat.py                 # interactive chat
    python baseline_llm/chat.py -q "claim"      # single claim
    python baseline_llm/chat.py -q "claim" -j   # raw canonical JSON output
"""

import argparse
import json
import os
import sys
from typing import Any, Dict

# Make the parent package importable so we can reuse the shared format.
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PARENT_DIR = os.path.dirname(_THIS_DIR)
if _PARENT_DIR not in sys.path:
    sys.path.insert(0, _PARENT_DIR)

from verdict_format import format_verdict, normalize_verdict, verdict_to_json  # noqa: E402

# Support both "python baseline_llm/chat.py" and "python -m baseline_llm.chat".
if __package__:
    from .config import get_llm
    from .prompt import BASELINE_PROMPT
else:
    from config import get_llm
    from prompt import BASELINE_PROMPT

SOURCE_LABEL = "Baseline LLM (single model)"


def _parse_json_response(raw: Any) -> Dict[str, Any]:
    """Parse an LLM response as JSON, tolerating markdown code fences."""
    if isinstance(raw, dict):
        return raw
    text = str(raw).strip()
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
        return {"verdict": "UNVERIFIABLE", "confidence": 0, "reasoning": str(raw)}


def check_claim(claim: str) -> Dict[str, Any]:
    """Fact-check a single claim with the lone LLM; return a canonical verdict."""
    claim = (claim or "").strip()
    if not claim:
        return normalize_verdict("", {"verdict": "UNVERIFIABLE",
                                       "reasoning": "Empty claim."})

    llm = get_llm()
    prompt = BASELINE_PROMPT.format(query=claim)
    try:
        response = llm.invoke(prompt)
        data = _parse_json_response(response.content)
    except Exception as e:  # noqa: BLE001
        data = {"verdict": "UNVERIFIABLE", "confidence": 0,
                "reasoning": f"LLM error: {e}"}

    return normalize_verdict(claim, data)


def interactive_mode(as_json: bool = False) -> None:
    print("=" * 60)
    print("BASELINE FACT-CHECKER (single LLM, no agents)")
    print("=" * 60)
    print("Введите утверждение для проверки. Команды: quit / exit\n")

    while True:
        try:
            claim = input("\nУтверждение: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        if not claim:
            continue
        if claim.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        verdict = check_claim(claim)
        if as_json:
            print(verdict_to_json(verdict))
        else:
            print("\n" + format_verdict(verdict, source=SOURCE_LABEL))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Single-LLM baseline fact-checker (A/B baseline)."
    )
    parser.add_argument("-q", "--query", type=str, help="Claim to fact-check")
    parser.add_argument("-j", "--json", action="store_true",
                        help="Output raw canonical JSON instead of text")
    args = parser.parse_args()

    if args.query:
        verdict = check_claim(args.query)
        if args.json:
            print(verdict_to_json(verdict))
        else:
            print(format_verdict(verdict, source=SOURCE_LABEL))
    else:
        interactive_mode(as_json=args.json)


if __name__ == "__main__":
    main()
