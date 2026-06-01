# Fake News Detector

Multi-agent system for fake news detection using LangGraph.

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
```

## Architectures

- **A (Router)**: Meta-LLM selects one agent (D, T, or C)
- **B (Parallel)**: All agents analyze, then synthesizer combines

## Agents

- **D**: Data-based cross-checking (fact verification via APIs)
- **T**: Textual & discourse analysis (manipulation markers)
- **C**: Contextual & source analysis (coherence, security)

## Structure

```
fake_news_detector/
├── run.py              # Entry point
├── config.py           # Prompts, API config
├── state.py            # State definition
├── agents/             # D, T, C agents
├── integrations/       # External APIs
└── graphs/             # LangGraph architectures
```
# fake-news-detector

