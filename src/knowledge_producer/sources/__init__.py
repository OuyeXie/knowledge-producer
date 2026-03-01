from __future__ import annotations

import re
from datetime import date
from typing import Callable

from knowledge_producer import Paper

# Each source module exposes a fetch(days, max_results, ref_date) -> list[Paper] function.
# Sources are registered here and called by fetch_all_sources().

_SOURCES: dict[str, Callable[..., list[Paper]]] = {}


def _register_sources() -> None:
    """Lazily import and register all source modules."""
    if _SOURCES:
        return

    from knowledge_producer.sources.arxiv_source import fetch as arxiv_fetch
    from knowledge_producer.sources.huggingface_source import fetch as hf_fetch
    from knowledge_producer.sources.medium_source import fetch as medium_fetch
    from knowledge_producer.sources.nvidia_source import fetch as nvidia_fetch
    from knowledge_producer.sources.deepmind_source import fetch as deepmind_fetch
    from knowledge_producer.sources.meta_ai_source import fetch as meta_fetch
    from knowledge_producer.sources.openai_source import fetch as openai_fetch
    from knowledge_producer.sources.twitter_source import fetch as twitter_fetch
    from knowledge_producer.sources.rednote_source import fetch as rednote_fetch

    _SOURCES.update(
        {
            "arxiv": arxiv_fetch,
            "huggingface": hf_fetch,
            "medium": medium_fetch,
            "nvidia": nvidia_fetch,
            "deepmind": deepmind_fetch,
            "meta_ai": meta_fetch,
            "openai": openai_fetch,
            "twitter": twitter_fetch,
            "rednote": rednote_fetch,
        }
    )


def available_sources() -> list[str]:
    """Return list of all registered source names."""
    _register_sources()
    return list(_SOURCES.keys())


def _normalize_title(title: str) -> str:
    """Normalize title for deduplication."""
    return re.sub(r"\s+", " ", title.lower().strip())


def _deduplicate(papers: list[Paper]) -> list[Paper]:
    """Remove duplicate papers across sources by normalized title."""
    seen: set[str] = set()
    unique: list[Paper] = []
    for paper in papers:
        key = _normalize_title(paper.title)
        if key not in seen:
            seen.add(key)
            unique.append(paper)
    return unique


def fetch_all_sources(
    days: int = 1,
    max_results: int = 500,
    sources: list[str] | None = None,
    ref_date: date | None = None,
) -> list[Paper]:
    """Fetch papers from all (or selected) sources.

    Each source is called independently — one failure won't stop others.
    Results are deduplicated across sources by title.

    Args:
        ref_date: Reference date to fetch from (default: today UTC).
                  e.g. ref_date=2026-02-28 with days=1 fetches Feb 27-28.
    """
    _register_sources()

    selected = sources if sources else list(_SOURCES.keys())
    all_papers: list[Paper] = []

    for name in selected:
        if name not in _SOURCES:
            print(f"  [!] Unknown source: {name}, skipping")
            continue

        print(f"  [{name}] Fetching...", flush=True)
        try:
            papers = _SOURCES[name](days, max_results, ref_date)
            print(f"  [{name}] Found {len(papers)} items")
            all_papers.extend(papers)
        except Exception as e:
            print(f"  [{name}] Error: {e}")

    return _deduplicate(all_papers)
