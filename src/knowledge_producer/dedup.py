"""Deduplicate papers against previously generated reports.

Parses existing report markdown files to extract paper URLs and titles,
then filters out papers that already appeared in those reports.
"""

from __future__ import annotations

import os
import re
from glob import glob

from knowledge_producer import Paper


def _normalize(text: str) -> str:
    """Normalize text for fuzzy title matching."""
    return re.sub(r"\s+", " ", text.lower().strip())


def extract_seen_from_report(filepath: str) -> set[str]:
    """Extract paper URLs and normalized titles from a report file.

    Returns a set of identifiers (URLs and normalized titles) for dedup.
    """
    seen: set[str] = set()
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Match: - **Link**: <url>
            if line.startswith("- **Link**:"):
                url = line.split(":", 1)[1].strip()
                # Handle "- **Link**: http://..." format
                url = line[len("- **Link**:"):].strip()
                if url:
                    seen.add(url)
            # Match: ### <title>
            elif line.startswith("### "):
                title = line[4:].strip()
                if title:
                    seen.add(_normalize(title))
    return seen


def load_seen_papers(
    report_dir: str = "reports",
    report_files: list[str] | None = None,
) -> set[str]:
    """Load all seen paper identifiers from previous reports.

    Args:
        report_dir: Directory containing report markdown files.
        report_files: Specific report files to scan. If None, scans all
                      *.md files in report_dir.

    Returns:
        Set of URLs and normalized titles from previous reports.
    """
    seen: set[str] = set()

    if report_files is not None:
        paths = report_files
    else:
        paths = sorted(glob(os.path.join(report_dir, "*.md")))

    for path in paths:
        if os.path.isfile(path):
            file_seen = extract_seen_from_report(path)
            seen.update(file_seen)

    return seen


def dedup_papers(papers: list[Paper], seen: set[str]) -> tuple[list[Paper], int]:
    """Filter out papers that already appeared in previous reports.

    Matches by URL (exact) and title (normalized fuzzy).

    Returns:
        (filtered_papers, num_removed)
    """
    if not seen:
        return papers, 0

    filtered: list[Paper] = []
    removed = 0

    for paper in papers:
        if paper.url in seen or _normalize(paper.title) in seen:
            removed += 1
        else:
            filtered.append(paper)

    return filtered, removed
