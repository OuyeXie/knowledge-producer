from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import arxiv

from knowledge_producer import Paper

ARXIV_CATEGORIES = ["cs.AI", "cs.LG", "cs.CL", "cs.CV", "cs.SE", "cs.MA"]


def _build_query(categories: list[str]) -> str:
    return " OR ".join(f"cat:{c}" for c in categories)


def fetch(days: int = 1, max_results: int = 500, ref_date: date | None = None) -> list[Paper]:
    """Fetch recent AI research papers from arXiv."""
    today = ref_date or datetime.now(timezone.utc).date()
    cutoff_date = today - timedelta(days=days)
    cutoff = datetime(cutoff_date.year, cutoff_date.month, cutoff_date.day, tzinfo=timezone.utc)

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
        if result.published.replace(tzinfo=timezone.utc) < cutoff:
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
