"""
Data model representing a bibliographic citation record.
"""

from typing import List, Optional

class CitationRecord:
    def __init__(
        self,
        paper_id: str,
        ambiguous_group: str,
        author_name: str,
        coauthors: List[str],
        title: str,
        abstract: str = "",
        keywords: Optional[List[str]] = None,
        venue: str = "",
        year: str = "",
        ground_truth_label: str = "",
        source_dataset: str = ""
    ):
        self.paper_id = paper_id
        self.ambiguous_group = ambiguous_group
        self.author_name = author_name
        self.coauthors = coauthors or []
        self.title = title
        self.abstract = abstract
        self.keywords = keywords or []
        self.venue = venue
        self.year = year
        self.ground_truth_label = ground_truth_label
        self.source_dataset = source_dataset

    def to_dict(self) -> dict:
        return {
            "paper_id": self.paper_id,
            "ambiguous_group": self.ambiguous_group,
            "author_name": self.author_name,
            "coauthors": self.coauthors,
            "title": self.title,
            "abstract": self.abstract,
            "keywords": self.keywords,
            "venue": self.venue,
            "year": self.year,
            "ground_truth_label": self.ground_truth_label,
            "source_dataset": self.source_dataset
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'CitationRecord':
        return cls(
            paper_id=d.get("paper_id", ""),
            ambiguous_group=d.get("ambiguous_group", ""),
            author_name=d.get("author_name", ""),
            coauthors=d.get("coauthors", []),
            title=d.get("title", ""),
            abstract=d.get("abstract", ""),
            keywords=d.get("keywords", []),
            venue=d.get("venue", ""),
            year=d.get("year", ""),
            ground_truth_label=d.get("ground_truth_label", ""),
            source_dataset=d.get("source_dataset", "")
        )

    def __repr__(self) -> str:
        return f"<CitationRecord {self.paper_id}: '{self.title[:30]}...' ({self.author_name})>"
