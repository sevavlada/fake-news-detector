"""Configuration for the fake news detection system."""

import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load .env from the same directory as this file
_THIS_DIR = Path(__file__).parent
load_dotenv(_THIS_DIR / ".env")

YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
# Yandex Cloud folder ID (from the AI Studio folder URL)
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID", "b1g847puonagq4c90lr4")
GOOGLE_FACTCHECK_API_KEY = os.getenv("GOOGLE_FACTCHECK_API_KEY")

YANDEX_BASE_URL = "https://llm.api.cloud.yandex.net/v1"

# YandexGPT 5 Pro: most capable Yandex model, best for Russian-language tasks.
# Alternatives: "yandexgpt-lite" (faster/cheaper), "llama" (open-weight).
DEFAULT_MODEL = "yandexgpt/latest"
DEFAULT_TEMPERATURE = 0

# --- Synthesis decision thresholds (Task 3) ---
# Minimum Agent-D confidence (0-100) for its evidence-based TRUE/FALSE to stand:
# if evidence exists, the synthesizer must NOT downgrade to UNVERIFIABLE out of
# caution. Lower THETA => the system commits to a verdict more readily.
DECISION_THETA = int(os.getenv("DECISION_THETA", "1"))
# If content is TRUE by evidence but the text is this manipulative or more,
# the final verdict becomes MANIPULATION (never flips TRUE<->FALSE).
MANIPULATION_SCORE_THRESHOLD = int(os.getenv("MANIPULATION_SCORE_THRESHOLD", "60"))


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
