from __future__ import annotations

from datetime import datetime, timedelta, timezone

import arxiv

from knowledge_producer import Paper

ARXIV_CATEGORIES = ["cs.AI", "cs.LG", "cs.CL", "cs.CV", "cs.SE", "cs.MA"]


def build_query(categories: list[str]) -> str:
    """Build an arXiv API query string for the given categories."""
    return " OR ".join(f"cat:{c}" for c in categories)


def fetch_papers(days: int = 1, max_results: int = 500) -> list[Paper]:
    """Fetch recent AI research papers from arXiv.

    Fetches papers sorted by submission date and filters to those
    published within the last `days` days. The arXiv submittedDate
    query field is unreliable, so we over-fetch and filter in Python.

    Args:
        days: Number of days to look back.
        max_results: Maximum number of papers to fetch from the API.

    Returns:
        Deduplicated list of Paper objects within the date window.
    """
    # Use calendar day boundaries since arXiv posts in daily batches (~18-20 UTC).
    # "1 day" means papers published today or yesterday.
    today = datetime.now(timezone.utc).date()
    cutoff_date = today - timedelta(days=days)
    cutoff = datetime(cutoff_date.year, cutoff_date.month, cutoff_date.day, tzinfo=timezone.utc)

    query = build_query(ARXIV_CATEGORIES)

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
        # Stop early if we've gone past the date window
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
                arxiv_url=entry_id,
                pdf_url=result.pdf_url,
                published=result.published,
                arxiv_categories=list(result.categories),
            )
        )

    return papers
