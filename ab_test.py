#!/usr/bin/env python3
"""Batch A/B test runner.

Reads a JSON file of claims, runs EACH claim through both systems:
  - Baseline   : the single-LLM fact-checker (baseline_llm/)
  - Detector   : the multi-agent Fake News Detector, Architecture B
                 (all agents in sequence: D -> T -> C -> synthesizer)
and writes the side-by-side results to an Excel .xlsx file so they can be
compared in an A/B test. If the input contains a ground-truth `verdict`
(e.g. FEVER/LIAR datasets), accuracy of each system is also computed.

Usage:
    python3 ab_test.py claims.json
    python3 ab_test.py claims.json -o results.xlsx
    python3 ab_test.py claims.json --limit 5            # quick check
    python3 ab_test.py claims.json --field claim        # send plain claim
    python3 ab_test.py claims.json --field claim_with_context  # default

Accepted JSON shapes:
    ["claim 1", "claim 2", ...]
    [{"claim": "..."}, {"statement": "..."}, ...]
    {"claims": [ ... ]}   (or any object whose value is the list)
Dataset objects may also carry "verdict" (ground truth), "uid", "dataset".
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List

# Make the package importable (mirrors run.py).
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PARENT_DIR = os.path.dirname(_THIS_DIR)
if _PARENT_DIR not in sys.path:
    sys.path.insert(0, _PARENT_DIR)

from fake_news_detector.state import create_initial_state
from fake_news_detector.graphs.architecture_b import create_parallel_graph
from fake_news_detector.utils import state_to_verdict
from fake_news_detector.baseline_llm.chat import check_claim as baseline_check

# Keys we look for when claims are objects rather than plain strings.
_CLAIM_KEYS = ("claim", "statement", "text", "sentence", "utterance", "content")


def _claim_text(item: Any, field: str) -> str:
    """Pick the text to fact-check from one JSON element."""
    if isinstance(item, str):
        return item.strip()
    if isinstance(item, dict):
        # Preferred field first (e.g. claim_with_context), then the usual keys.
        for key in (field, *_CLAIM_KEYS):
            if key in item and str(item[key]).strip():
                return str(item[key]).strip()
        for value in item.values():
            if isinstance(value, str) and value.strip():
                return value.strip()
    return str(item).strip()


def load_records(path: str, field: str) -> List[Dict[str, Any]]:
    """Load claims as records: {claim, ground_truth, uid, dataset}."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    # Unwrap {"claims": [...]} / {"data": [...]} -> the inner list.
    if isinstance(data, dict):
        for value in data.values():
            if isinstance(value, list):
                data = value
                break

    if not isinstance(data, list):
        raise ValueError(
            "JSON must be a list of claims (or an object containing one). "
            f"Got: {type(data).__name__}"
        )

    records = []
    for idx, item in enumerate(data, start=1):
        text = _claim_text(item, field)
        if not text:
            continue
        meta = item if isinstance(item, dict) else {}
        records.append({
            "claim": text,
            "ground_truth": str(meta.get("verdict", "")).strip().lower(),
            "uid": meta.get("uid", idx),
            "dataset": meta.get("dataset", ""),
        })
    return records


def run_detector(claim: str) -> Dict[str, Any]:
    """Run one claim through the multi-agent detector (Architecture B)."""
    graph = create_parallel_graph()
    state = graph.invoke(create_initial_state(claim))
    return state_to_verdict(state)


def _factors(verdict: Dict[str, Any]) -> str:
    return "; ".join(verdict.get("key_factors", []))


def _correct(verdict: str, ground_truth: str) -> str:
    """Return YES/NO/'' comparing a system verdict to ground truth."""
    if not ground_truth:
        return ""
    return "YES" if str(verdict).strip().lower() == ground_truth else "NO"


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch A/B test: baseline vs. detector.")
    parser.add_argument("input", help="Path to the JSON file with claims")
    parser.add_argument("-o", "--output", default="ab_results.xlsx",
                        help="Output Excel file (default: ab_results.xlsx)")
    parser.add_argument("--limit", type=int, default=0,
                        help="Only process the first N claims (0 = all)")
    parser.add_argument("--field", default="claim_with_context",
                        help="Which field to send to the models "
                             "(default: claim_with_context; use 'claim' for the bare statement)")
    args = parser.parse_args()

    try:
        from openpyxl import Workbook
    except ImportError:
        print("Missing dependency. Install it with:\n    pip3 install openpyxl")
        sys.exit(1)

    records = load_records(args.input, args.field)
    if args.limit > 0:
        records = records[: args.limit]
    if not records:
        print("No claims found in the input file.")
        sys.exit(1)

    print(f"Loaded {len(records)} claim(s). Field: '{args.field}'. Running A/B test...\n")

    wb = Workbook()
    ws = wb.active
    ws.title = "results"
    ws.append([
        "uid", "dataset", "claim", "ground_truth",
        "baseline_verdict", "baseline_confidence",
        "baseline_correct", "baseline_key_factors", "baseline_reasoning",
        "detector_verdict", "detector_confidence",
        "detector_correct", "detector_key_factors", "detector_reasoning",
        "verdicts_match",
    ])

    base_correct = det_correct = scored = match = 0

    for i, rec in enumerate(records, start=1):
        claim, gt = rec["claim"], rec["ground_truth"]
        print(f"[{i}/{len(records)}] {claim[:70]}")

        try:
            base = baseline_check(claim)
        except Exception as e:  # noqa: BLE001
            base = {"verdict": "ERROR", "confidence": 0, "key_factors": [],
                    "reasoning": f"baseline error: {e}"}
        try:
            det = run_detector(claim)
        except Exception as e:  # noqa: BLE001
            det = {"verdict": "ERROR", "confidence": 0, "key_factors": [],
                   "reasoning": f"detector error: {e}"}

        bc = _correct(base.get("verdict"), gt)
        dc = _correct(det.get("verdict"), gt)
        same = base.get("verdict") == det.get("verdict")

        if gt:
            scored += 1
            base_correct += (bc == "YES")
            det_correct += (dc == "YES")
        match += same

        ws.append([
            rec["uid"], rec["dataset"], claim, gt,
            base.get("verdict"), base.get("confidence"),
            bc, _factors(base), base.get("reasoning"),
            det.get("verdict"), det.get("confidence"),
            dc, _factors(det), det.get("reasoning"),
            "YES" if same else "NO",
        ])

    # Summary sheet.
    total = len(records)
    summary = wb.create_sheet("summary")
    summary.append(["metric", "value"])
    summary.append(["total claims", total])
    summary.append(["scored against ground truth", scored])
    if scored:
        summary.append(["baseline correct", base_correct])
        summary.append(["baseline accuracy", round(100 * base_correct / scored, 1)])
        summary.append(["detector correct", det_correct])
        summary.append(["detector accuracy", round(100 * det_correct / scored, 1)])
    summary.append(["baseline/detector verdicts match", match])
    summary.append(["agreement rate %", round(100 * match / total, 1)])

    wb.save(args.output)

    print(f"\nDone. Results written to: {args.output}")
    if scored:
        print(f"  Baseline accuracy: {100 * base_correct / scored:.1f}%  "
              f"({base_correct}/{scored})")
        print(f"  Detector accuracy: {100 * det_correct / scored:.1f}%  "
              f"({det_correct}/{scored})")
    print(f"  Verdicts match:    {100 * match / total:.1f}%  ({match}/{total})")


if __name__ == "__main__":
    main()
