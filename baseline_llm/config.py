"""LLM configuration for the single-LLM baseline app.

Intentionally mirrors the Fake News Detector's config.py so that BOTH
apps run on the exact same model (YandexGPT via Yandex AI Studio) with
the same settings. The only difference between the two systems is the
orchestration around the model, not the model itself.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Reuse the SAME .env as the Fake News Detector (one directory up).
_THIS_DIR = Path(__file__).parent
_PARENT_DIR = _THIS_DIR.parent
load_dotenv(_PARENT_DIR / ".env")

YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID", "b1g847puonagq4c90lr4")

YANDEX_BASE_URL = "https://llm.api.cloud.yandex.net/v1"

# Same model and temperature as the Fake News Detector (see ../config.py).
DEFAULT_MODEL = "yandexgpt/latest"
DEFAULT_TEMPERATURE = 0


def _to_model_uri(model: str) -> str:
    """Expand a bare model id (e.g. 'yandexgpt/latest') to a Yandex gpt:// URI."""
    if model.startswith("gpt://") or model.startswith("ds://"):
        return model
    return f"gpt://{YANDEX_FOLDER_ID}/{model}"


def get_llm(model: str = DEFAULT_MODEL, temperature: float = DEFAULT_TEMPERATURE) -> ChatOpenAI:
    """Create and return a configured LLM instance backed by Yandex AI Studio."""
    return ChatOpenAI(
        api_key=YANDEX_API_KEY,
        base_url=YANDEX_BASE_URL,
        model=_to_model_uri(model),
        temperature=temperature,
    )
