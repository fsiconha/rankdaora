"""Generate a synthetic dataset of legal documents in JSONL format."""

from __future__ import annotations

import argparse
import json
import random
from datetime import date, timedelta
from pathlib import Path
from typing import List
from uuid import uuid4

DATASET_SIZE = 120
RANDOM_SEED = 2025
DEFAULT_OUTPUT = (
    Path(__file__).resolve().parents[1] / "data" / "documents.jsonl"
)

COURTS: List[str] = [
    "Tribunal Regional Federal da 1a Regiao",
    "Tribunal Regional do Trabalho da 2a Regiao",
    "Superior Tribunal de Justica",
    "Tribunal de Justica de Sao Paulo",
    "Juizado Especial Federal de Minas Gerais",
]

TOPICS: List[str] = [
    "direito civil",
    "direito penal",
    "direito tributario",
    "direito administrativo",
    "direito constitucional",
]

DOCUMENT_TYPES: List[str] = [
    "sentenca",
    "acordao",
    "peticao",
    "recurso ordinario",
    "mandado de seguranca",
]

LEGAL_REFERENCES: List[str] = [
    "artigo 5 da Constituicao Federal",
    "artigo 37 da Constituicao Federal",
    "codigo de processo civil",
    "codigo de processo penal",
    "estatuto da crianca e do adolescente",
]


def random_date() -> str:
    """Return a random ISO date string within the last 10 years."""

    start = date.today() - timedelta(days=365 * 10)
    delta_days = random.randint(0, 365 * 10)
    return (start + timedelta(days=delta_days)).isoformat()


def build_content(topic: str, document_type: str, legal_reference: str) -> str:
    """Craft a short document body using the provided fragments."""

    paragraphs = [
        (
            "Este documento aborda o tema de "
            f"{topic} em formato de {document_type}."
        ),
        (
            "O texto examina fundamentos constitucionais, com destaque para "
            f"{legal_reference}."
        ),
        (
            (
                "Sao apresentados argumentos, fatos e referencias "
                "jurisprudenciais que sustentam o pedido principal."
            )
        ),
    ]
    return "\n".join(paragraphs)


def generate_document(counter: int) -> dict[str, object]:
    """Create a single document structure with deterministic randomness."""

    topic = random.choice(TOPICS)
    document_type = random.choice(DOCUMENT_TYPES)
    legal_reference = random.choice(LEGAL_REFERENCES)

    title = f"{document_type.title()} sobre {topic} #{counter:03d}"
    content = build_content(topic, document_type, legal_reference)

    return {
        "id": f"doc-{uuid4().hex[:8]}",
        "title": title,
        "content": content,
        "court": random.choice(COURTS),
        "date": random_date(),
        "es_score": 0.0,
        "combined_score": 0.0,
    }


def main() -> None:
    """Parse arguments and write the dataset to disk."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path to the JSONL file that will be generated.",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=DATASET_SIZE,
        help="Number of synthetic documents to generate.",
    )
    args = parser.parse_args()

    random.seed(RANDOM_SEED)

    output_path: Path = args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        for counter in range(1, args.size + 1):
            document = generate_document(counter)
            json.dump(document, file, ensure_ascii=False)
            file.write("\n")

    print(f"Generated {args.size} documents at {output_path}")


if __name__ == "__main__":
    main()
