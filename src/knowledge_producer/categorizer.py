from __future__ import annotations

import re

from knowledge_producer import Paper

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "Inference": [
        "inference",
        "serving",
        "quantization",
        "pruning",
        "distillation",
        "latency",
        "throughput",
        "kv cache",
        "speculative decoding",
        "deployment",
        "gguf",
        "vllm",
        "tensorrt",
        "onnx",
        "efficient inference",
        "acceleration",
        "token generation",
        "model compression",
    ],
    "RL": [
        "reinforcement learning",
        "rlhf",
        "ppo",
        "dpo",
        "grpo",
        "reward model",
        "policy optimization",
        "preference learning",
        "human feedback",
        "rlaif",
        "online learning",
        "reward shaping",
        "value function",
    ],
    "SFT": [
        "supervised fine-tuning",
        "fine-tuning",
        "instruction tuning",
        "alignment",
        "lora",
        "qlora",
        "adapter",
        "peft",
        "parameter-efficient",
        "training data",
        "dataset curation",
        "finetuning",
    ],
    "Agent": [
        "agent",
        "tool use",
        "function calling",
        "planning",
        "reasoning",
        "chain-of-thought",
        "multi-agent",
        "autonomous",
        "agentic",
        "self-reflection",
        "tool-augmented",
        "web agent",
    ],
    "Coding": [
        "code generation",
        "programming",
        "software engineering",
        "code completion",
        "debugging",
        "code review",
        "repository",
        "compiler",
        "program synthesis",
        "code llm",
        "software development",
        "code repair",
        "automated programming",
    ],
}

_SHORT_KEYWORD_THRESHOLD = 5


def _match_keyword(keyword: str, text: str) -> bool:
    """Match keyword in text. Uses word-boundary regex for short keywords."""
    if len(keyword) < _SHORT_KEYWORD_THRESHOLD:
        return bool(re.search(r"\b" + re.escape(keyword) + r"\b", text))
    return keyword in text


def categorize_paper(paper: Paper) -> list[str]:
    """Assign category tags to a paper based on keyword matching."""
    text = f"{paper.title} {paper.abstract}".lower()
    matched: list[str] = []
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(_match_keyword(kw, text) for kw in keywords):
            matched.append(category)
    return matched


def categorize_papers(papers: list[Paper]) -> list[Paper]:
    """Apply categorization to all papers, populating each paper's tags field."""
    for paper in papers:
        paper.tags = categorize_paper(paper)
    return papers
