"""Load generated documents into Elasticsearch."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from elasticsearch import Elasticsearch, helpers

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from app.config import get_settings  # noqa: E402
from preprocessing.bayesian_smoothing import (  # noqa: E402
    BayesianSmoother,
    adjusted_impressions,
)
from preprocessing.bias_correction import PositionBiasCorrector  # noqa: E402
from preprocessing.ips import (  # noqa: E402
    ImpressionEvent,
    corrected_clicks,
)
from preprocessing.log_transformation import (  # noqa: E402
    log_transform,
    percentile_rank,
)


def normalize_click_count(raw: object) -> int:
    """Convert raw inputs into a bounded non-negative click count."""

    if isinstance(raw, bool):
        return int(raw)
    if isinstance(raw, (int, float)):
        return max(0, min(876, int(raw)))
    if isinstance(raw, str):
        stripped = raw.strip()
        if not stripped:
            return 0
        try:
            value = float(stripped)
        except ValueError:
            return 0
        return max(0, min(876, int(value)))
    return 0


def normalize_click_position(raw: object) -> int:
    """Convert inputs to a non-negative click position."""

    if isinstance(raw, bool):
        return int(raw)
    if isinstance(raw, (int, float)):
        return max(0, min(100, int(raw)))
    if isinstance(raw, str):
        stripped = raw.strip()
        if not stripped:
            return 0
        try:
            value = float(stripped)
        except ValueError:
            return 0
        return max(0, min(100, int(value)))
    return 0


def normalize_click_impression(raw: object) -> int:
    """Convert inputs to a non-negative impression count."""

    if isinstance(raw, bool):
        return int(raw)
    if isinstance(raw, (int, float)):
        return max(0, min(10000, int(raw)))
    if isinstance(raw, str):
        stripped = raw.strip()
        if not stripped:
            return 0
        try:
            value = float(stripped)
        except ValueError:
            return 0
        return max(0, min(10000, int(value)))
    return 0


def normalize_click_timestamp(raw: object) -> str | None:
    """Return a best-effort ISO timestamp string."""

    if raw is None:
        return None
    if isinstance(raw, str):
        stripped = raw.strip()
        return stripped or None
    return None


def iter_documents(dataset_path: Path) -> Iterable[dict[str, object]]:
    """Yield documents from a JSONL dataset."""

    with dataset_path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                yield json.loads(line)


def recreate_index(client: Elasticsearch, index_name: str) -> None:
    """Drop and recreate the target index with deterministic mappings."""

    if client.indices.exists(index=index_name):
        client.indices.delete(index=index_name)

    mappings = {
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "title": {"type": "text", "analyzer": "standard"},
                "content": {"type": "text", "analyzer": "standard"},
                "court": {"type": "keyword"},
                "date": {"type": "date"},
                "es_score": {"type": "float"},
                "combined_score": {"type": "float"},
                "click_count": {"type": "integer"},
                "click_position": {"type": "integer"},
                "click_impression": {"type": "integer"},
                "click_timestamp": {"type": "date"},
                "click_count_raw": {"type": "integer"},
                "click_count_corrected": {"type": "float"},
                "click_impression_adjusted": {"type": "float"},
                "popularity_raw": {"type": "float"},
                "popularity_log": {"type": "float"},
                "popularity_percentile": {"type": "float"},
            }
        }
    }
    client.indices.create(index=index_name, body=mappings)


def bulk_load(
    client: Elasticsearch,
    index_name: str,
    dataset_path: Path,
) -> None:
    """Bulk insert documents into Elasticsearch."""

    documents: list[dict[str, Any]] = []
    for document in iter_documents(dataset_path):
        source = {**document}
        click_count = normalize_click_count(source.get("click_count", 0))
        click_position = normalize_click_position(
            source.get("click_position", 0)
        )
        click_impression = normalize_click_impression(
            source.get("click_impression", click_count)
        )
        if click_impression < click_count:
            click_impression = click_count
        click_timestamp = normalize_click_timestamp(
            source.get("click_timestamp")
        )

        source.update(
            {
                "click_count": click_count,
                "click_position": click_position,
                "click_impression": click_impression,
            }
        )
        if click_timestamp is not None:
            source["click_timestamp"] = click_timestamp
        else:
            source.pop("click_timestamp", None)

        documents.append(source)

    if not documents:
        return

    corrector = PositionBiasCorrector()
    for document in documents:
        impressions = normalize_click_impression(
            document.get("click_impression", 0)
        )
        clicks = normalize_click_count(document.get("click_count", 0))
        position = normalize_click_position(
            document.get("click_position", 0)
        )
        if impressions <= 0 and clicks <= 0:
            continue
        corrector.ingest([(position, impressions, clicks)])

    reference_time = datetime.now(timezone.utc)
    document_metrics: list[dict[str, Any]] = []
    total_corrected_clicks = 0.0
    total_adjusted_impressions = 0.0

    for document in documents:
        clicks_value = normalize_click_count(document.get("click_count", 0))
        impressions_value = normalize_click_impression(
            document.get("click_impression", 0)
        )
        position_value = normalize_click_position(
            document.get("click_position", 0)
        )
        timestamp_raw = document.get("click_timestamp")
        timestamp = (
            timestamp_raw
            if isinstance(timestamp_raw, str)
            else None
        )

        document["click_count"] = clicks_value
        document["click_impression"] = impressions_value
        document["click_position"] = position_value
        if timestamp is not None:
            document["click_timestamp"] = timestamp
        else:
            document.pop("click_timestamp", None)

        event = ImpressionEvent(
            position=position_value,
            clicks=float(clicks_value),
            impressions=float(impressions_value),
            timestamp=timestamp,
        )
        corrected = corrected_clicks(
            [event],
            corrector,
            now=reference_time,
        )
        adjusted = adjusted_impressions(
            [event],
            corrector,
            now=reference_time,
        )

        document_metrics.append(
            {
                "source": document,
                "corrected_clicks": corrected,
                "adjusted_impressions": adjusted,
                "raw_clicks": clicks_value,
                "raw_impressions": impressions_value,
            }
        )
        total_corrected_clicks += corrected
        total_adjusted_impressions += adjusted

    if total_adjusted_impressions <= 0:
        prior = 0.0
    else:
        prior = total_corrected_clicks / total_adjusted_impressions

    smoother = BayesianSmoother(prior=prior, pseudocount=10.0)

    raw_scores: list[float] = []
    for metrics in document_metrics:
        score = smoother.score_from_stats(
            float(metrics["corrected_clicks"]),
            float(metrics["adjusted_impressions"]),
        )
        metrics["popularity_raw"] = score
        raw_scores.append(score)

    log_scores = log_transform(raw_scores)
    percentile_scores = percentile_rank(log_scores)

    for index, metrics in enumerate(document_metrics):
        document = metrics["source"]
        document["click_count_raw"] = int(metrics["raw_clicks"])
        document["click_count_corrected"] = float(
            metrics["corrected_clicks"]
        )
        document["click_impression_adjusted"] = float(
            metrics["adjusted_impressions"]
        )
        document["popularity_raw"] = float(metrics["popularity_raw"])
        document["popularity_log"] = float(log_scores[index])
        document["popularity_percentile"] = float(
            percentile_scores[index]
        )

    actions = [
        {
            "_op_type": "index",
            "_index": index_name,
            "_id": document.get("id"),
            "_source": document,
        }
        for document in documents
    ]

    helpers.bulk(client, actions)


def main() -> None:
    """Parse command line arguments and load the dataset."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset",
        type=Path,
        default=ROOT_DIR / "data" / "documents.jsonl",
        help="Path to the JSONL dataset to load.",
    )
    parser.add_argument(
        "--recreate-index",
        action="store_true",
        help="Drop the index before inserting documents.",
    )
    args = parser.parse_args()

    settings = get_settings()
    client = Elasticsearch(hosts=[settings.elasticsearch_url])

    if args.recreate_index:
        recreate_index(client, settings.elasticsearch_index)

    bulk_load(client, settings.elasticsearch_index, args.dataset)
    print(
        f"Loaded documents from {args.dataset} into index "
        f"{settings.elasticsearch_index}"
    )


if __name__ == "__main__":
    main()
