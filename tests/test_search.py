"""Tests for the search endpoint."""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.es_client import get_es_client


class FakeElasticsearch:
    """In-memory replacement for Elasticsearch during tests."""

    async def search(
        self,
        index: str,
        query: Dict[str, Any],
        size: int,
    ) -> Dict[str, Any]:
        """Return a canned response that mimics Elasticsearch output."""

        return {
            "hits": {
                "hits": [
                    {
                        "_id": "doc-123",
                        "_score": 1.23,
                        "_source": {
                            "id": "doc-123",
                            "title": "Sentenca sobre direito civil",
                            "content": "Corpo sintetico",
                            "court": "Tribunal de Justica",
                            "date": "2024-01-10",
                            "click_count": 17,
                            "click_position": 2,
                            "click_impression": 120,
                            "click_timestamp": "2025-01-10T12:34:00Z",
                            "click_count_raw": 15,
                            "click_count_corrected": 21.5,
                            "click_impression_adjusted": 180.0,
                            "popularity_raw": 0.6,
                            "popularity_log": 0.47,
                            "popularity_percentile": 0.8,
                            "popularity_score": 0.73,
                        },
                    }
                ]
            }
        }


@pytest.fixture
def test_client() -> Iterator[TestClient]:
    """Provide a TestClient with the Elasticsearch dependency overridden."""

    async def dependency_override() -> AsyncIterator[FakeElasticsearch]:
        yield FakeElasticsearch()

    app.dependency_overrides[get_es_client] = dependency_override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_search_returns_results(test_client: TestClient) -> None:
    """The search endpoint should return documents in the expected format."""

    response = test_client.get("/search", params={"query": "direito"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "direito"
    assert len(payload["results"]) == 1
    document = payload["results"][0]
    assert document["id"] == "doc-123"
    assert document["es_score"] == pytest.approx(1.23)
    assert document["click_count"] == 17
    assert document["click_position"] == 2
    assert document["click_impression"] == 120
    assert document["click_timestamp"] == "2025-01-10T12:34:00Z"
    assert document["click_count_raw"] == 15
    assert document["click_count_corrected"] == pytest.approx(21.5)
    assert document["click_impression_adjusted"] == pytest.approx(180.0)
    assert document["popularity_raw"] == pytest.approx(0.6)
    assert document["popularity_log"] == pytest.approx(0.47)
    assert document["popularity_percentile"] == pytest.approx(0.8)
    assert document["popularity_score"] == pytest.approx(0.73)
