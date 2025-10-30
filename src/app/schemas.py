"""Pydantic models for API requests and responses."""

from __future__ import annotations

from typing import Any, Iterable, List

from pydantic import BaseModel, Field


class Document(BaseModel):
    """Represents a ranked document returned from Elasticsearch."""

    id: str = Field(..., description="Unique identifier of the document.")
    title: str = Field(..., description="Document title.")
    content: str = Field(
        ...,
        description="Main textual content of the document.",
    )
    court: str = Field(..., description="Originating court or jurisdiction.")
    date: str = Field(..., description="ISO formatted publication date.")
    es_score: float = Field(
        ...,
        description="Score reported by Elasticsearch.",
    )
    combined_score: float = Field(
        ...,
        description="Score combining all ranking signals.",
    )
    click_count: int = Field(
        default=0,
        ge=0,
        description="Observed click volume associated with the document.",
    )

    @classmethod
    def from_hit(cls, hit: dict[str, Any]) -> "Document":
        """Build a document model from an Elasticsearch hit record."""

        source = hit.get("_source", {})
        score = float(hit.get("_score", 0.0))
        raw_clicks = source.get("click_count", 0)
        try:
            click_count = int(raw_clicks)
        except (TypeError, ValueError):
            click_count = 0
        click_count = max(0, click_count)
        return cls(
            id=str(source.get("id") or hit.get("_id")),
            title=source.get("title", "Untitled"),
            content=source.get("content", ""),
            court=source.get("court", "Unknown"),
            date=source.get("date", "1970-01-01"),
            es_score=score,
            combined_score=source.get("combined_score", score),
            click_count=click_count,
        )


class SearchResponse(BaseModel):
    """Response envelope returned by the search endpoint."""

    query: str = Field(..., description="Original query string.")
    results: List[Document] = Field(
        default_factory=list,
        description="Ordered list of search results.",
    )

    @classmethod
    def from_hits(
        cls,
        query: str,
        hits: Iterable[dict[str, Any]],
    ) -> "SearchResponse":
        """Construct a response instance from raw Elasticsearch hits."""

        documents = [Document.from_hit(hit) for hit in hits]
        return cls(query=query, results=documents)
