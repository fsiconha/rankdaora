"""Utilities for interacting with Elasticsearch."""

from fastapi import HTTPException, Request, status
from elasticsearch import AsyncElasticsearch

from .config import get_settings


async def get_es_client(request: Request) -> AsyncElasticsearch:
    """Return an initialized Elasticsearch client from application state."""

    client = getattr(request.app.state, "es_client", None)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Elasticsearch client not initialized.",
        )
    return client


async def create_es_client() -> AsyncElasticsearch:
    """Instantiate an Elasticsearch client configured via settings."""

    settings = get_settings()
    return AsyncElasticsearch(
        hosts=[settings.elasticsearch_url],
        request_timeout=settings.es_request_timeout,
    )
