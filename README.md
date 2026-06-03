# Fake News Detector

Multi-agent system for fake news detection using LangGraph.

## Model

The whole system runs on a single LLM — **YandexGPT** (`yandexgpt/latest`,
`temperature=0`) from Yandex AI Studio, accessed via its OpenAI-compatible
API. Agents D/T/C, the router and the synthesizer all call the same model
(`config.py`); only the prompts and orchestration differ.

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure API key in `.env`:
```
YANDEX_API_KEY=your_yandex_api_key_here
YANDEX_FOLDER_ID=b1g847puonagq4c90lr4
```

3. Run:
```bash
python run.py
```

## Usage

```bash
python run.py                    # Interactive mode
python run.py -a -q "claim"      # Architecture A (router)
python run.py -b -q "claim"      # Architecture B (parallel)
python run.py -s                 # Sample queries
python run.py -v                 # Verbose output
python run.py -a -q "claim" -c   # Canonical A/B format (text)
python run.py -b -q "claim" -j   # Canonical A/B format (JSON)
```

## Architectures

- **A (Router)**: Meta-LLM selects one agent (D, T, or C)
- **B (Parallel)**: All agents analyze, then synthesizer combines

## Agents

- **D**: Data-based cross-checking (fact verification via APIs)
- **T**: Textual & discourse analysis (manipulation markers)
- **C**: Contextual & source analysis (coherence, security)

## A/B Testing vs. single-LLM baseline

`baseline_llm/` is an isolated app that uses ONLY the same model
(YandexGPT) as a plain chat-style fact-checker — no agents, router or
synthesizer. Both apps share one canonical output format
(`verdict_format.py`), so their answers are directly comparable.

```bash
# Baseline (single LLM)
python baseline_llm/chat.py                  # interactive chat
python baseline_llm/chat.py -q "claim"       # text output
python baseline_llm/chat.py -q "claim" -j    # canonical JSON

# Fake News Detector in the same canonical format
python run.py -a -q "claim" -c               # text output (Arch A)
python run.py -b -q "claim" -j               # canonical JSON (Arch B)
```

Canonical schema: `{ claim, verdict, confidence, key_factors, reasoning }`.

### Batch A/B test (many claims at once)

`ab_test.py` runs a whole JSON file of claims through BOTH systems and
writes the side-by-side results to an Excel file.

```bash
python3 ab_test.py claims.json                  # -> ab_results.xlsx
python3 ab_test.py claims.json -o results.xlsx   # custom output name
python3 ab_test.py claims.json --limit 5         # quick check on first 5
python3 ab_test.py claims.json --field claim     # send the bare claim
```

Input JSON may be a list of strings (`["claim 1", "claim 2"]`) or a list of
objects with a `claim`/`statement`/`text` field. The detector runs through
Architecture B (all agents in sequence).

If the objects also carry a ground-truth `verdict` (e.g. FEVER/LIAR), the
Excel file gets `baseline_correct` / `detector_correct` columns plus a
`summary` sheet with each system's accuracy. By default the
`claim_with_context` field is sent to the models (use `--field claim` for
the bare statement).

## Structure

```
fake_news_detector/
├── run.py              # Entry point
├── config.py           # LLM (YandexGPT) + API config
├── state.py            # State definition
├── verdict_format.py   # Shared canonical output format (A/B testing)
├── agents/             # D, T, C agents
├── prompts/            # Agent / router / synthesizer prompts
├── integrations/       # External APIs (Google Fact Check)
├── graphs/             # LangGraph architectures (A, B)
└── baseline_llm/       # Isolated single-LLM fact-checker (A/B baseline)
```

