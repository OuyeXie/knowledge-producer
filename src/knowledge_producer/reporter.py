from __future__ import annotations

import os
from collections import defaultdict
from datetime import datetime, timezone

from knowledge_producer import Paper

CATEGORY_ORDER = ["Inference", "RL", "SFT", "Agent", "Coding"]


def _format_authors(authors: list[str], max_authors: int = 5) -> str:
    if len(authors) <= max_authors:
        return ", ".join(authors)
    return ", ".join(authors[:max_authors]) + " et al."


def _paper_section(paper: Paper) -> str:
    authors_str = _format_authors(paper.authors)
    tags_str = ", ".join(paper.tags) if paper.tags else "Uncategorized"
    lines = [
        f"### {paper.title}",
        f"- **Link**: {paper.arxiv_url}",
        f"- **Tags**: {tags_str}",
        f"- **Authors**: {authors_str}",
        f"- **Published**: {paper.published.strftime('%Y-%m-%d')}",
        f"- **Abstract**: {paper.abstract}",
        "",
        "---",
        "",
    ]
    return "\n".join(lines)


def generate_report(papers: list[Paper], report_date: str) -> str:
    """Generate a full Markdown report from categorized papers."""
    lines: list[str] = []

    # Header
    lines.append(f"# AI Research Daily Report - {report_date}")
    lines.append("")

    # Summary
    category_counts = {cat: 0 for cat in CATEGORY_ORDER}
    uncategorized_count = 0
    for paper in papers:
        if not paper.tags:
            uncategorized_count += 1
        for tag in paper.tags:
            if tag in category_counts:
                category_counts[tag] += 1

    stats = " | ".join(f"{cat}: {count}" for cat, count in category_counts.items())
    lines.append("## Summary")
    lines.append(f"- **Total papers**: {len(papers)}")
    lines.append(f"- {stats} | Uncategorized: {uncategorized_count}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Group papers by category
    category_papers: dict[str, list[Paper]] = defaultdict(list)
    uncategorized: list[Paper] = []

    for paper in papers:
        if not paper.tags:
            uncategorized.append(paper)
        else:
            for tag in paper.tags:
                category_papers[tag].append(paper)

    # Category sections
    for category in CATEGORY_ORDER:
        cat_papers = category_papers.get(category, [])
        lines.append(f"## {category} ({len(cat_papers)} papers)")
        lines.append("")
        if not cat_papers:
            lines.append("*No papers found in this category.*")
            lines.append("")
        else:
            for paper in cat_papers:
                lines.append(_paper_section(paper))

    # Uncategorized section
    if uncategorized:
        lines.append(f"## Uncategorized ({len(uncategorized)} papers)")
        lines.append("")
        for paper in uncategorized:
            lines.append(_paper_section(paper))

    # Footer
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines.append("---")
    lines.append(f"*Report generated on {now} by knowledge-producer v0.1.0*")
    lines.append("")

    return "\n".join(lines)


def save_report(content: str, output_dir: str = "reports") -> str:
    """Write the report to a file and return the file path."""
    os.makedirs(output_dir, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filename = f"report-{date_str}.md"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return os.path.abspath(filepath)
