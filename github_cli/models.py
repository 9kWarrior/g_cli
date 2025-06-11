from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict

@dataclass
class Repository:
    name: str
    url: str
    description: str
    stars: int


@dataclass
class Commit:
    sha: str
    url: str
    author: str
    date: datetime
    message: str


@dataclass
class IssueLabelStats:
    label: str
    open_count: int
    closed_count: int


@dataclass
class RepositoryWithStats(Repository):
    issues_stats: List[IssueLabelStats]


@dataclass
class CommitSearchResult:
    sha: str
    url: str
    author: str
    date: datetime
    message: str