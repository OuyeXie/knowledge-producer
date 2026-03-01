from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone
from time import mktime

import feedparser

from knowledge_producer import Paper

NVIDIA_BLOG_FEED = "https://developer.nvidia.com/blog/feed/"

# Only keep posts related to AI/ML topics
AI_KEYWORDS = [
    "ai", "artificial intelligence", "machine learning", "deep learning",
    "neural network", "llm", "large language model", "transformer",
    "gpu", "cuda", "tensorrt", "inference", "training", "diffusion",
    "generative", "nlp", "computer vision", "reinforcement learning",
]


def _strip_html(text: str) -> str:
    clean = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", clean).strip()


def _is_ai_related(title: str, summary: str) -> bool:
    text = f"{title} {summary}".lower()
    return any(kw in text for kw in AI_KEYWORDS)


def _parse_date(entry: dict) -> datetime | None:
    for key in ("published_parsed", "updated_parsed"):
        parsed = entry.get(key)
        if parsed:
            return datetime.fromtimestamp(mktime(parsed), tz=timezone.utc)
    return None


def fetch(days: int = 1, max_results: int = 500, ref_date: date | None = None) -> list[Paper]:
    """Fetch recent AI-related posts from NVIDIA Developer Blog RSS."""
    today = ref_date or datetime.now(timezone.utc).date()
    cutoff_date = today - timedelta(days=days)

    feed = feedparser.parse(NVIDIA_BLOG_FEED)

    papers: list[Paper] = []

    for entry in feed.entries:
        published = _parse_date(entry)
        if not published or published.date() < cutoff_date:
            continue

        title = entry.get("title", "").strip()
        summary = _strip_html(entry.get("summary", entry.get("description", "")))
        link = entry.get("link", "")
        author = entry.get("author", "NVIDIA")

        if not title or not _is_ai_related(title, summary):
            continue

        papers.append(
            Paper(
                title=title,
                abstract=summary[:1000] if summary else "",
                authors=[author] if author else ["NVIDIA"],
                url=link,
                source="nvidia",
                published=published,
            )
        )

        if len(papers) >= max_results:
            break

    return papers
