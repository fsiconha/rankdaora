"""FastAPI application exposing Elasticsearch-backed search functionality."""

from __future__ import annotations

from contextlib import asynccontextmanager

from elasticsearch import AsyncElasticsearch, exceptions as es_exceptions
from fastapi import Depends, FastAPI, HTTPException, Query, status

from .config import Settings, get_settings
from .es_client import create_es_client, get_es_client
from .schemas import SearchResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources when the application starts."""

    app.state.es_client = await create_es_client()
    try:
        yield
    finally:
        es_client: AsyncElasticsearch = getattr(app.state, "es_client", None)
        if es_client is not None:
            await es_client.close()


app = FastAPI(title="RankDaora Search API", lifespan=lifespan)


@app.get("/health", tags=["Health"])
async def health(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    """Return application health information."""

    return {
        "status": "ok",
        "index": settings.elasticsearch_index,
    }


@app.get("/search", response_model=SearchResponse, tags=["Search"])
async def search(
    query: str = Query(
        ...,
        min_length=1,
        description="Search query to execute.",
    ),
    settings: Settings = Depends(get_settings),
    es_client: AsyncElasticsearch = Depends(get_es_client),
) -> SearchResponse:
    """Perform a query against the configured Elasticsearch index."""

    try:
        response = await es_client.search(
            index=settings.elasticsearch_index,
            query={
                "multi_match": {
                    "query": query,
                    "fields": ["title^2", "content"],
                }
            },
            size=settings.results_size,
        )
    except es_exceptions.NotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Index '{settings.elasticsearch_index}' not found.",
        ) from error
    except es_exceptions.ElasticsearchException as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Search backend is unavailable.",
        ) from error

    hits = response.get("hits", {}).get("hits", [])
    return SearchResponse.from_hits(query=query, hits=hits)
