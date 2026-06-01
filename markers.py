"""Manipulation marker loading and detection for Agent T.

Markers are discursive/linguistic cues (absolutive, causal, contrast,
evaluative-emotional) loaded from data/manipulation_markers.json. The
detector scans text for these markers and reports per-category hits, which
feed both the computed metrics and the Agent T prompt.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List

_MARKERS_PATH = Path(__file__).parent / "data" / "manipulation_markers.json"

_markers_cache: Dict[str, List[str]] | None = None


def load_markers() -> Dict[str, List[str]]:
    """Load marker words grouped by category (cached).

    Returns a mapping like {"absolutive": ["never", "always", ...], ...}
    with both English and Russian markers merged per category.
    """
    global _markers_cache
    if _markers_cache is not None:
        return _markers_cache

    with open(_MARKERS_PATH, encoding="utf-8") as f:
        raw = json.load(f)

    categories: Dict[str, List[str]] = {}
    for category, entries in raw.get("markers", {}).items():
        words: List[str] = []
        seen = set()
        for entry in entries:
            word = (entry.get("word") or "").strip().lower()
            if word and word not in seen:
                seen.add(word)
                words.append(word)
        categories[category] = words

    _markers_cache = categories
    return categories


def _compile(word: str) -> re.Pattern:
    """Compile a Unicode-aware, case-insensitive whole-word(s) pattern."""
    return re.compile(
        r"(?<!\w)" + re.escape(word) + r"(?!\w)",
        re.IGNORECASE | re.UNICODE,
    )


def detect_markers(text: str) -> Dict[str, Any]:
    """Scan text for manipulation markers.

    Returns per-category matched markers, counts, and an overall total so
    Agent T can reason about the density of manipulative discourse cues.
    """
    categories = load_markers()
    by_category: Dict[str, List[str]] = {}
    counts: Dict[str, int] = {}
    total = 0

    for category, words in categories.items():
        matched: List[str] = []
        for word in words:
            if _compile(word).search(text):
                matched.append(word)
        if matched:
            by_category[category] = matched
        counts[category] = len(matched)
        total += len(matched)

    return {
        "markers_by_category": by_category,
        "marker_counts": counts,
        "total_markers": total,
    }
