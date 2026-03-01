from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import requests

from knowledge_producer import Paper

HF_DAILY_PAPERS_URL = "https://huggingface.co/api/daily_papers"


def fetch(days: int = 1, max_results: int = 500, ref_date: date | None = None) -> list[Paper]:
    """Fetch recent papers from HuggingFace Daily Papers API."""
    today = ref_date or datetime.now(timezone.utc).date()
    cutoff_date = today - timedelta(days=days)

    resp = requests.get(HF_DAILY_PAPERS_URL, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    papers: list[Paper] = []

    for entry in data[:max_results]:
        paper_data = entry.get("paper", {})
        paper_id = paper_data.get("id", "")

        # publishedAt is at top level of entry
        published_str = entry.get("publishedAt", "")
        if published_str:
            published = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
        else:
            published = datetime.now(timezone.utc)

        if published.date() < cutoff_date:
            continue

        # title/summary available at both top level and in paper
        title = entry.get("title", "") or paper_data.get("title", "")
        title = title.strip()
        abstract = (entry.get("summary", "") or paper_data.get("summary", "")).replace("\n", " ").strip()
        authors = [a.get("name", "") for a in paper_data.get("authors", [])]

        if not title:
            continue

        papers.append(
            Paper(
                title=title,
                abstract=abstract,
                authors=authors,
                url=f"https://huggingface.co/papers/{paper_id}",
                source="huggingface",
                published=published,
                pdf_url=f"https://arxiv.org/pdf/{paper_id}" if paper_id else None,
            )
        )

    return papers
