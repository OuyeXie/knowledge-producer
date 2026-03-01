"""LLM-powered summarization and classification for focus papers.

Supports OpenAI (gpt-4o-mini) and Anthropic (claude-haiku) providers.
Only called for the small set of focus papers (~3-10), not the full corpus.

Requires OPENAI_API_KEY or ANTHROPIC_API_KEY in environment or .env file.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from knowledge_producer import Paper

PROVIDERS = ["anthropic", "openai"]

_SYSTEM_PROMPT = """\
You are an AI research analyst. For each paper, you will:
1. Write a 2-3 sentence "relevance summary" explaining why this paper \
is relevant to the given focus topic and what its key contribution is.
2. Verify and refine the category tags from this list: \
Pretraining, SFT, RL, Alignment, Inference, Architecture, RAG, Agent, \
Coding, Reasoning, Evaluation, Multimodal, CV, Diffusion, 3D, \
Autonomous Driving, Medical, Science, Robotics, NLP, Speech, Data, \
Training, Graph, Recommendation, Time Series, Security.

Respond with valid JSON only — no markdown fences."""


def _load_env_key(name: str) -> str:
    """Load a key from environment or .env file."""
    key = os.environ.get(name, "")
    if key:
        return key

    for candidate in [Path.cwd() / ".env", Path(__file__).resolve().parents[2] / ".env"]:
        if candidate.is_file():
            for line in candidate.read_text().splitlines():
                line = line.strip()
                if line.startswith(f"{name}=") and not line.startswith("#"):
                    val = line.split("=", 1)[1].strip().strip("\"'")
                    if val:
                        return val
    return ""


def _detect_provider(provider: str | None) -> tuple[str, str]:
    """Detect which provider to use and return (provider_name, api_key).

    Priority: explicit --llm-provider flag > ANTHROPIC_API_KEY > OPENAI_API_KEY.
    """
    if provider == "anthropic":
        key = _load_env_key("ANTHROPIC_API_KEY")
        if key:
            return "anthropic", key
    elif provider == "openai":
        key = _load_env_key("OPENAI_API_KEY")
        if key:
            return "openai", key

    if provider is None:
        # Auto-detect: prefer Anthropic, then OpenAI
        key = _load_env_key("ANTHROPIC_API_KEY")
        if key:
            return "anthropic", key
        key = _load_env_key("OPENAI_API_KEY")
        if key:
            return "openai", key

    return "", ""


def _build_user_prompt(topic: str, papers: list[Paper]) -> str:
    entries = []
    for i, p in enumerate(papers):
        entries.append(
            f"[{i}] Title: {p.title}\n"
            f"    Abstract: {p.abstract[:600]}\n"
            f"    Current tags: {', '.join(p.tags) if p.tags else 'none'}"
        )
    papers_text = "\n\n".join(entries)

    return (
        f"Focus topic: \"{topic}\"\n\n"
        f"Papers:\n{papers_text}\n\n"
        f"For each paper, return a JSON array of objects with keys:\n"
        f'  "index" (int), "relevance_summary" (str, 2-3 sentences), '
        f'"refined_tags" (list of str from the allowed categories)\n'
        f"Return ONLY the JSON array."
    )


def _parse_json_response(content: str) -> list[dict]:
    """Parse JSON from LLM response, stripping markdown fences if present."""
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
    if content.endswith("```"):
        content = content.rsplit("```", 1)[0]
    return json.loads(content.strip())


def _call_openai(api_key: str, topic: str, papers: list[Paper]) -> list[dict]:
    try:
        from openai import OpenAI
    except ImportError:
        print("    [llm] openai package not installed. Install with: pip install openai")
        return []

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(topic, papers)},
        ],
        temperature=0.3,
        max_tokens=8000,
    )
    return _parse_json_response(response.choices[0].message.content or "")


def _call_anthropic(api_key: str, topic: str, papers: list[Paper]) -> list[dict]:
    try:
        from anthropic import Anthropic
    except ImportError:
        print("    [llm] anthropic package not installed. Install with: pip install anthropic")
        return []

    client = Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=8000,
        system=_SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": _build_user_prompt(topic, papers)},
        ],
    )
    text = response.content[0].text if response.content else ""
    return _parse_json_response(text)


def summarize_focus_papers(
    topic: str,
    papers: list[Paper],
    provider: str = "",
    api_key: str = "",
) -> list[dict]:
    """Call LLM to summarize and classify focus papers.

    Returns a list of dicts with keys: index, relevance_summary, refined_tags.
    """
    try:
        if provider == "anthropic":
            return _call_anthropic(api_key, topic, papers)
        else:
            return _call_openai(api_key, topic, papers)
    except Exception as e:
        print(f"    [llm] API call failed: {e}")
        return []


def enrich_focus_papers(
    focus_matches: dict[str, list[Paper]],
    provider: str | None = None,
) -> tuple[dict[str, list[tuple[Paper, str]]], str]:
    """Enrich focus papers with LLM summaries.

    Returns (enriched_dict, provider_name) where enriched_dict maps
    topic -> list of (paper, relevance_summary) tuples.
    If the LLM is unavailable, relevance_summary will be empty string.
    """
    detected_provider, api_key = _detect_provider(provider)
    enriched: dict[str, list[tuple[Paper, str]]] = {}

    for topic, papers in focus_matches.items():
        if not papers:
            enriched[topic] = []
            continue

        if not api_key:
            enriched[topic] = [(p, "") for p in papers]
            continue

        print(f"    [llm:{detected_provider}] Summarizing {len(papers)} papers for \"{topic}\"...")
        results = summarize_focus_papers(topic, papers, detected_provider, api_key)

        # Build lookup from LLM results
        summaries_by_idx: dict[int, dict] = {}
        for item in results:
            idx = item.get("index")
            if idx is not None:
                summaries_by_idx[idx] = item

        topic_enriched: list[tuple[Paper, str]] = []
        for i, paper in enumerate(papers):
            llm_data = summaries_by_idx.get(i, {})
            summary = llm_data.get("relevance_summary", "")
            refined_tags = llm_data.get("refined_tags")
            if refined_tags and isinstance(refined_tags, list):
                paper.tags = refined_tags
            topic_enriched.append((paper, summary))

        enriched[topic] = topic_enriched

    return enriched, detected_provider
