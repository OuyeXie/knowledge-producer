from dataclasses import dataclass, field
from datetime import datetime

__version__ = "0.1.0"


@dataclass
class Paper:
    title: str
    abstract: str
    authors: list[str]
    url: str
    source: str
    published: datetime
    pdf_url: str | None = None
    source_categories: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
