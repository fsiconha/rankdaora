"""Application configuration module."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application settings."""

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        extra="ignore",
    )

    elasticsearch_url: str = Field(
        default="http://localhost:9200",
        alias="ELASTICSEARCH_URL",
        description="Base URL for the Elasticsearch cluster.",
    )
    elasticsearch_index: str = Field(
        default="legal-docs",
        alias="ELASTICSEARCH_INDEX",
        description="Primary index for legal documents.",
    )
    results_size: int = Field(
        default=10,
        alias="RESULTS_SIZE",
        ge=1,
        le=100,
        description=(
            "Default number of results returned by the search endpoint."
        ),
    )
    es_request_timeout: int = Field(
        default=10,
        alias="ES_REQUEST_TIMEOUT",
        ge=1,
        le=60,
        description="Timeout in seconds for Elasticsearch requests.",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()
