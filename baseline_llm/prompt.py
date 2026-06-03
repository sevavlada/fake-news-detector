"""Prompt for the single-LLM baseline fact-checker.

A single, self-contained fact-checking prompt. Unlike the multi-agent
system, there is no router/agents/synthesizer — the one LLM does the
whole job. The required JSON output matches the shared canonical schema
(see ../verdict_format.py) so results are directly A/B-comparable.
"""

BASELINE_PROMPT = """
Ты — система проверки фактов (фактчекинг). Тебе дают утверждение, и ты
оцениваешь его достоверность, опираясь на свои знания и логический анализ.

Утверждение:
{query}

Проанализируй утверждение и верни СТРОГО JSON без какого-либо текста вокруг:
{{
  "verdict": "TRUE | FALSE | MIXED | UNVERIFIABLE",
  "confidence": <целое число 0-100>,
  "key_factors": ["ключевой фактор 1", "ключевой фактор 2"],
  "reasoning": "подробное обоснование вердикта"
}}

Где:
- TRUE — утверждение достоверно;
- FALSE — утверждение ложно;
- MIXED — частично верно, частично нет;
- UNVERIFIABLE — недостаточно данных для проверки.
"""
