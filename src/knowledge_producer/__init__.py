from dataclasses import dataclass, field
from datetime import datetime

__version__ = "0.1.0"


@dataclass
class Paper:
    title: str
    abstract: str
    authors: list[str]
    arxiv_url: str
    pdf_url: str | None
    published: datetime
    arxiv_categories: list[str]
    tags: list[str] = field(default_factory=list)
