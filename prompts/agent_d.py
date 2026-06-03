"""Prompt for Agent D: Data-based Cross-checking."""

# Used to turn a full claim into a short keyword query for the
# Google Fact Check Tools API (which matches on keywords, not full sentences).
AGENT_D_KEYWORDS_PROMPT = """
You build a SEARCH QUERY for the Google Fact Check Tools API.
Given a claim, extract the 2-4 most important search terms: the main named
entity (person, organization, place) plus the core topic. Drop filler words
and who said it.

Rules for the output:
- plain words separated by single spaces;
- NO underscores, NO quotes, NO punctuation;
- keep multi-word names as normal words (e.g. Rick Perry, not Rick_Perry);
- return ONLY the query, nothing else.

Claim:
{claim}
"""

# Lightweight "is this checkable?" gate (replaces the removed ClaimBuster role).
AGENT_D_FACTUAL_PROMPT = """
Это проверяемое фактологическое утверждение (можно подтвердить или опровергнуть
по источникам) или мнение/риторика?
Ответь ОДНИМ словом: factual или non_factual.

Текст: "{claim}"
"""

AGENT_D_PROMPT = """
Ты — специализированный агент фактологической проверки (Агент D).
Твой метод: кросс-чекинг фактов СТРОГО по предоставленным доказательствам.

Утверждение:
{query}

Найденные доказательства (Google Fact Check, веб-поиск/Википедия):
{retrieved_context}

ВАЖНЫЕ ПРАВИЛА:
- Опирайся ТОЛЬКО на найденные доказательства выше. НЕ используй свои внутренние
  знания и НЕ угадывай.
- Если доказательства подтверждают утверждение -> "TRUE".
- Если доказательства опровергают -> "FALSE".
- Если есть и за, и против -> "MIXED".
- Если доказательств нет СОВСЕМ (пустой список) -> "UNVERIFIABLE". Это честный
  и правильный ответ, когда проверять не по чему.
- Не уходи в "UNVERIFIABLE", если доказательства всё же есть — вынеси вердикт.

Верни СТРОГО JSON без дополнительного текста:
{{
  "verdict": "TRUE | FALSE | MIXED | UNVERIFIABLE",
  "confidence": <целое число 0-100>,
  "reasoning": "короткое обоснование со ссылкой на найденные доказательства"
}}
"""
