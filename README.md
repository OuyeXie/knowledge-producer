# knowledge-producer

CLI tool that fetches recent AI research from multiple sources, categorizes them, and generates a Markdown report.

## Sources

| Source | Method | Auth Required |
|--------|--------|---------------|
| **arXiv** | `arxiv` Python package | No |
| **HuggingFace Daily Papers** | REST API | No |
| **Medium** | RSS feeds (AI/ML tags) | No |
| **NVIDIA Developer Blog** | RSS feed | No |
| **Google DeepMind** | Web scraping | No |
| **Meta AI (FAIR)** | Web scraping | No |
| **OpenAI Research** | Web scraping | No |
| **X (Twitter)** | `snscrape` (experimental) | No |
| **RedNote (Xiaohongshu)** | Web scraping (experimental) | No |

## Categories

Each paper/article is tagged with one or more categories (27 total) based on keyword matching:

**LLM Core**: Pretraining, SFT, RL, Alignment, Inference, Architecture, RAG, Agent, Coding, Reasoning, Evaluation

**Multimodal & Vision**: Multimodal, CV, Diffusion, 3D

**Domain Applications**: Autonomous Driving, Medical, Science, Robotics

**NLP & Speech**: NLP, Speech

**Data & Infrastructure**: Data, Training

**Other ML**: Graph, Recommendation, Time Series, Security

## Focus Topics

The report highlights papers matching **focus topics** at the top, before the full categorized listing. This helps you zero in on domains you care about most.

**How it works:**

1. **Keyword matching** finds papers relevant to each focus topic
2. **LLM summarization** (optional) calls an LLM to generate a "Why it matters" relevance summary for each matched paper and refine its category tags

**Defaults:** `GPU kernel optimization`, `agentic coding`, `LLM inference`, `autonomous driving`

**Pre-defined focus topics** (with expanded keyword sets): `GPU kernel optimization`, `agentic coding`, `LLM inference`, `multimodal LLM`, `autonomous driving`, `AI safety`, `robotics`, `diffusion models`. Any free-text string also works as a custom topic.

**LLM providers:**

| Provider | Model | Env variable | Flag |
|----------|-------|-------------|------|
| **Anthropic** (default) | `claude-haiku-4-5` | `ANTHROPIC_API_KEY` | `--llm-provider anthropic` |
| **OpenAI** | `gpt-4o-mini` | `OPENAI_API_KEY` | `--llm-provider openai` |

**Default behavior** — what happens based on which API keys you have set:

| Keys in `.env` | `--llm-provider` flag | Provider used |
|---------------|----------------------|---------------|
| `ANTHROPIC_API_KEY` only | *(none)* | Anthropic |
| `OPENAI_API_KEY` only | *(none)* | OpenAI |
| Both keys set | *(none)* | Anthropic (preferred) |
| Both keys set | `--llm-provider openai` | OpenAI (forced) |
| Neither key set | *(none)* | None (keyword-only fallback) |

**Controlling focus and LLM behavior:**

| Flag | Focus section | LLM summaries |
|------|:---:|:---:|
| *(default)* | Yes (default topics) | Yes (auto-detect from API keys) |
| `--focus "topic1,topic2"` | Yes (custom topics) | Yes (if API key set) |
| `--llm-provider openai` | Yes | Yes (force OpenAI) |
| `--llm-provider anthropic` | Yes | Yes (force Anthropic) |
| `--no-llm` | Yes | No (keyword matching only) |
| `--no-focus` | No | No |
| *(no API key set)* | Yes | No (automatic fallback) |

## Quick Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Run the CLI:

```bash
python -m knowledge_producer --help
```

For LLM-powered focus summaries, install the optional dependencies:
```bash
pip install -e ".[llm]"
```

Then add either or both API keys to `.env`:
```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

Optional, for X/Twitter support:
```bash
pip install snscrape
```

## OpenClaw Setup

To expose this repo's `ai-report` skill to OpenClaw, create a symlink into the OpenClaw workspace skills directory:

```bash
ln -s /Users/ouye/workspace/knowledge-producer/skills/ai_report /Users/ouye/.openclaw/workspace/skills/ai_report
```

## Usage

```bash
# Fetch from all sources, last 1 day (with default focus topics)
python -m knowledge_producer

# Fetch last 3 days
python -m knowledge_producer --days 3

# Fetch from a specific date (e.g. yesterday's papers)
python -m knowledge_producer --date 2026-02-28
python -m knowledge_producer --date 2026-02-28 --days 2  # Feb 26-28

# Custom focus topics with LLM summaries
python -m knowledge_producer --focus "LLM inference,autonomous driving"

# Force a specific LLM provider
python -m knowledge_producer --llm-provider openai
python -m knowledge_producer --llm-provider anthropic

# Focus section but no LLM calls (keyword matching only)
python -m knowledge_producer --no-llm

# No focus section at all — plain categorized report
python -m knowledge_producer --no-focus

# Fetch from specific sources only
python -m knowledge_producer --sources arxiv,huggingface,medium

# Custom output directory
python -m knowledge_producer --output my-reports

# Limit results per source
python -m knowledge_producer --max-results 100
```

## Output

**Reports** are saved to `reports/report-{date}-{days}d.md` (e.g. `report-2026-02-28-7d.md`).

**Logs** are saved to `logs/{date}-{days}d-{HHMMSS}.log` for each generation run.

## Report Format

Each report includes:
- **Generation info** — timestamp, parameters used, and AI disclaimer (if LLM summaries are enabled)
- **Summary** — total counts by category, source, and focus topic
- **Focus sections** (at the top) — papers matching your focus topics, with LLM-generated "Why it matters" blockquote summaries (if enabled)
- **Category sections** (27 categories) — papers grouped by tag
- Each paper shows: title, source, link, tags, authors, published date, and abstract
- Papers with multiple tags appear under each matching category

Example report header:
```
# AI Research Daily Report - 2026-02-28

> Generated on 2026-03-01 21:52:46 UTC | `days=7` `sources=all` `max_results=500` ...
>
> *"Why it matters" summaries are AI-generated by Anthropic claude-haiku-4-5.*

## Summary
- **Total items**: 566
- **By category**: Pretraining: 165 | SFT: 73 | RL: 50 | ...
- **By source**: arxiv: 500 | huggingface: 21 | medium: 34 | ...
- **Focus topics**: GPU kernel optimization: 5 | agentic coding: 6 | ...
```

## Project Structure

```
knowledge-producer/
├── pyproject.toml
├── .gitignore
├── .env                         # API keys (gitignored)
├── reports/                     # Generated reports (gitignored)
├── logs/                        # Generation logs (gitignored)
└── src/knowledge_producer/
    ├── __init__.py              # Paper dataclass
    ├── __main__.py              # python -m entry point
    ├── main.py                  # CLI (argparse) + log tee
    ├── categorizer.py           # Keyword-based multi-tag categorization (27 categories)
    ├── focus.py                 # Focus topic definitions + keyword matching
    ├── llm_summarizer.py        # Anthropic/OpenAI summarization (optional)
    ├── reporter.py              # Markdown report generation
    └── sources/
        ├── __init__.py           # Source registry + fetch_all_sources()
        ├── arxiv_source.py
        ├── huggingface_source.py
        ├── medium_source.py
        ├── nvidia_source.py
        ├── deepmind_source.py
        ├── meta_ai_source.py
        ├── openai_source.py
        ├── twitter_source.py     # experimental
        └── rednote_source.py     # experimental
```
