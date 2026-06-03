"""Single-LLM baseline fact-checker (isolated app for A/B testing).

Uses ONLY the same LLM as the Fake News Detector (YandexGPT via Yandex
AI Studio), with no agents, no router and no synthesizer — a plain
chat-style fact-checker. Its output uses the shared canonical format
(see verdict_format.py) so it can be compared against the multi-agent
system in an A/B test.
"""
