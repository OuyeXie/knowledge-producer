"""Focus topic matching for highlighted report sections.

Each focus topic is a free-text domain (e.g. "GPU kernel optimization")
that expands into a set of search keywords. Unknown topics are used
directly as keyword phrases.
"""

from __future__ import annotations

import re

from knowledge_producer import Paper

# Pre-defined focus topics with expanded keyword sets.
# Keys are canonical topic names (case-insensitive match).
FOCUS_TOPIC_KEYWORDS: dict[str, list[str]] = {
    "GPU kernel optimization": [
        "gpu kernel",
        "cuda kernel",
        "kernel optimization",
        "kernel fusion",
        "gpu programming",
        "gpu optimization",
        "warp scheduling",
        "shared memory",
        "gpu compute",
        "triton kernel",
        "cuda programming",
        "gpu acceleration",
        "tensor core",
        "gpu memory",
        "kernel launch",
        "gpu performance",
        "parallel computing",
        "gpu architecture",
        "thread block",
        "memory coalescing",
        "occupancy",
        "gpu profiling",
    ],
    "agentic coding": [
        "agentic coding",
        "code agent",
        "coding agent",
        "ai coding assistant",
        "automated coding",
        "swe-bench",
        "software engineering agent",
        "code generation agent",
        "autonomous coding",
        "ai developer",
        "ai programmer",
        "repository-level",
        "pull request",
        "bug fixing agent",
        "code repair agent",
        "agentic software",
        "ai software engineer",
        "computer use",
        "browser agent",
        "ide agent",
    ],
    "LLM inference": [
        "llm inference",
        "model serving",
        "vllm",
        "tensorrt-llm",
        "speculative decoding",
        "kv cache",
        "continuous batching",
        "token generation",
        "inference optimization",
        "quantization",
        "model compression",
        "gguf",
        "flash attention",
        "paged attention",
        "inference throughput",
        "inference latency",
        "batch inference",
        "prefix caching",
    ],
    "multimodal LLM": [
        "multimodal llm",
        "vision language model",
        "visual instruction",
        "image understanding",
        "multimodal reasoning",
        "visual question answering",
        "multimodal agent",
        "video understanding",
        "omni-modal",
        "any-to-any",
        "visual grounding",
        "multimodal alignment",
        "image-text",
    ],
    "autonomous driving": [
        "autonomous driving",
        "self-driving",
        "autonomous vehicle",
        "end-to-end driving",
        "trajectory prediction",
        "motion planning",
        "lidar",
        "bird's eye view",
        "driving simulation",
        "ego vehicle",
        "lane detection",
        "waymo",
        "nuscenes",
        "carla",
    ],
    "AI safety": [
        "ai safety",
        "alignment",
        "red teaming",
        "jailbreak",
        "guardrail",
        "harmful content",
        "value alignment",
        "safety evaluation",
        "adversarial attack",
        "prompt injection",
        "content moderation",
        "machine unlearning",
        "trustworthy ai",
    ],
    "robotics": [
        "robot learning",
        "robotic manipulation",
        "embodied ai",
        "sim-to-real",
        "robot policy",
        "humanoid",
        "dexterous manipulation",
        "visuomotor",
        "imitation learning",
        "teleoperation",
        "robot navigation",
        "locomotion",
    ],
    "diffusion models": [
        "diffusion model",
        "stable diffusion",
        "text-to-image",
        "text-to-video",
        "image generation",
        "flow matching",
        "rectified flow",
        "consistency model",
        "controllable generation",
        "latent diffusion",
        "video generation",
        "dit",
        "image editing",
    ],
}

DEFAULT_FOCUS_TOPICS = ["GPU kernel optimization", "agentic coding", "LLM inference", "autonomous driving"]

_SHORT_KEYWORD_THRESHOLD = 5


def _match_keyword(keyword: str, text: str) -> bool:
    if len(keyword) < _SHORT_KEYWORD_THRESHOLD:
        return bool(re.search(r"\b" + re.escape(keyword) + r"\b", text))
    return keyword in text


def _get_keywords(topic: str) -> list[str]:
    """Get keywords for a topic. Falls back to using the topic string itself."""
    # Case-insensitive lookup in pre-defined topics
    for name, keywords in FOCUS_TOPIC_KEYWORDS.items():
        if name.lower() == topic.lower():
            return keywords
    # Unknown topic — use the raw string as a keyword
    return [topic.lower()]


def match_focus(papers: list[Paper], topics: list[str]) -> dict[str, list[Paper]]:
    """Match papers against focus topics.

    Returns a dict mapping each topic name to its matching papers.
    """
    results: dict[str, list[Paper]] = {}

    for topic in topics:
        keywords = _get_keywords(topic)
        matched: list[Paper] = []

        for paper in papers:
            text = f"{paper.title} {paper.abstract}".lower()
            if any(_match_keyword(kw, text) for kw in keywords):
                matched.append(paper)

        results[topic] = matched

    return results
