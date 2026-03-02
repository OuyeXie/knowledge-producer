from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import arxiv

from knowledge_producer import Paper
from knowledge_producer.time_utils import PACIFIC, today_pacific, to_pacific

ARXIV_CATEGORIES = [
    # Core AI & ML
    "cs.AI",   # Artificial Intelligence
    "cs.LG",   # Machine Learning (this IS "Computer Science > Machine Learning")
    "cs.CL",   # Computation and Language (NLP, LLMs, transformers)
    "cs.CV",   # Computer Vision and Pattern Recognition
    "cs.NE",   # Neural and Evolutionary Computing (architectures, training methods)
    # Robotics & Multi-agent
    "cs.RO",   # Robotics (embodied AI, manipulation, navigation)
    "cs.MA",   # Multi-Agent Systems (multi-agent, cooperative AI)
    # Software & Systems
    "cs.SE",   # Software Engineering (code generation, agentic coding)
    "cs.DC",   # Distributed Computing (distributed training, parallel systems)
    "cs.PF",   # Performance (GPU optimization, inference efficiency)
    # Safety & Information
    "cs.CR",   # Cryptography and Security (adversarial ML, AI safety)
    "cs.IR",   # Information Retrieval (RAG, search, recommendation)
    # Cross-disciplinary
    "stat.ML", # Machine Learning (statistics perspective, theory)
    "eess.AS", # Audio and Speech Processing (ASR, TTS, voice)
]


def _build_query(categories: list[str]) -> str:
    return " OR ".join(f"cat:{c}" for c in categories)


def fetch(days: int = 1, max_results: int = 500, ref_date: date | None = None) -> list[Paper]:
    """Fetch recent AI research papers from arXiv."""
    today = ref_date or today_pacific()
    cutoff_date = today - timedelta(days=days)
    cutoff = datetime(cutoff_date.year, cutoff_date.month, cutoff_date.day, tzinfo=PACIFIC)

    query = _build_query(ARXIV_CATEGORIES)

    client = arxiv.Client(delay_seconds=3.0, num_retries=3)
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )

    papers: list[Paper] = []
    seen: set[str] = set()

    for result in client.results(search):
        if to_pacific(result.published) < cutoff:
            break

        entry_id = result.entry_id
        if entry_id in seen:
            continue
        seen.add(entry_id)

        papers.append(
            Paper(
                title=result.title.replace("\n", " ").strip(),
                abstract=result.summary.replace("\n", " ").strip(),
                authors=[a.name for a in result.authors],
                url=entry_id,
                source="arxiv",
                published=result.published,
                pdf_url=result.pdf_url,
                source_categories=list(result.categories),
            )
        )

    return papers
