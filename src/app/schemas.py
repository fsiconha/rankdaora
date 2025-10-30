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
    click_count: int = Field(
        default=0,
        ge=0,
        description="Observed click volume associated with the document.",
    )
    click_position: int = Field(
        default=0,
        ge=0,
        description=(
            "Observed rank position from which the click was recorded."
        ),
    )
    click_impression: int = Field(
        default=0,
        ge=0,
        description="Total impressions observed for the document.",
    )
    click_timestamp: str | None = Field(
        default=None,
        description="Timestamp of the most recent click in ISO 8601 format.",
    )
    click_count_raw: int = Field(
        default=0,
        ge=0,
        description="Original click count prior to preprocessing.",
    )
    click_count_corrected: float = Field(
        default=0.0,
        ge=0.0,
        description="Position- and time-corrected click signal.",
    )
    click_impression_adjusted: float = Field(
        default=0.0,
        ge=0.0,
        description="Exposure volume adjusted by propensity weights.",
    )
    popularity_raw: float = Field(
        default=0.0,
        ge=0.0,
        description="Bayesian-smoothed popularity score.",
    )
    popularity_log: float = Field(
        default=0.0,
        ge=0.0,
        description="Log-scaled popularity for outlier mitigation.",
    )
    popularity_percentile: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Percentile rank of the log-scaled popularity.",
    )
    popularity_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Final blended popularity score used for ranking.",
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
        raw_position = source.get("click_position", 0)
        try:
            click_position = int(raw_position)
        except (TypeError, ValueError):
            click_position = 0
        click_position = max(0, click_position)
        raw_impression = source.get("click_impression", 0)
        try:
            click_impression = int(raw_impression)
        except (TypeError, ValueError):
            click_impression = 0
        click_impression = max(click_count, max(0, click_impression))
        raw_timestamp = source.get("click_timestamp")
        if isinstance(raw_timestamp, str) and raw_timestamp.strip():
            click_timestamp = raw_timestamp.strip()
        else:
            click_timestamp = None

        def _float_value(key: str, default: float = 0.0) -> float:
            value = source.get(key, default)
            try:
                return float(value)
            except (TypeError, ValueError):
                return default

        def _int_value(key: str, default: int = 0) -> int:
            value = source.get(key, default)
            try:
                return int(value)
            except (TypeError, ValueError):
                return default

        click_count_raw = _int_value("click_count_raw", click_count)
        click_count_corrected = _float_value("click_count_corrected")
        click_impression_adjusted = _float_value(
            "click_impression_adjusted",
            float(click_impression),
        )
        popularity_raw = _float_value("popularity_raw")
        popularity_log = max(0.0, _float_value("popularity_log"))
        popularity_percentile = min(
            1.0,
            max(0.0, _float_value("popularity_percentile")),
        )
        popularity_score = min(
            1.0,
            max(0.0, _float_value("popularity_score")),
        )

        return cls(
            id=str(source.get("id") or hit.get("_id")),
            title=source.get("title", "Untitled"),
            content=source.get("content", ""),
            court=source.get("court", "Unknown"),
            date=source.get("date", "1970-01-01"),
            es_score=score,
            click_count=click_count,
            click_position=click_position,
            click_impression=click_impression,
            click_timestamp=click_timestamp,
            click_count_raw=click_count_raw,
            click_count_corrected=click_count_corrected,
            click_impression_adjusted=click_impression_adjusted,
            popularity_raw=popularity_raw,
            popularity_log=popularity_log,
            popularity_percentile=popularity_percentile,
            popularity_score=popularity_score,
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
