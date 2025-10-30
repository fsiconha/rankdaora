"""Load generated documents into Elasticsearch."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

from elasticsearch import Elasticsearch, helpers

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from app.config import get_settings  # noqa: E402


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
            }
        }
    }
    client.indices.create(index=index_name, **mappings)


def bulk_load(
    client: Elasticsearch,
    index_name: str,
    dataset_path: Path,
) -> None:
    """Bulk insert documents into Elasticsearch."""

    actions = (
        {
            "_op_type": "index",
            "_index": index_name,
            "_id": document.get("id"),
            "_source": {
                **document,
                "click_count": normalize_click_count(
                    document.get("click_count", 0)
                ),
            },
        }
        for document in iter_documents(dataset_path)
    )
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
