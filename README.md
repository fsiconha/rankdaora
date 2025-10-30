# RankDaora

Projeto exemplo para demonstrar um pipeline simples de busca com FastAPI e Elasticsearch.

## Visao geral

- `compose.yaml` orquestra Elasticsearch e a API FastAPI.
- `scripts/generate_dataset.py` gera um dataset sintetico (~120 documentos).
- `scripts/load_documents.py` recria o indice `legal-docs` e faz bulk insert dos documentos.
- `src/app` contem a aplicacao FastAPI, modelos Pydantic e integracao com o cliente Elasticsearch.
- `tests/` possui testes com `pytest` utilizando um cliente fake para simular o backend.
- `.github/workflows/ci.yml` roda lint (`ruff`) e testes em PRs e pushes.

## Requisitos

- Docker e Docker Compose
- Python 3.11+ (opcional, para executar scripts utilitarios fora do container)

## Executando com Docker Compose

1. Gere o dataset sintetico (apenas uma vez ou quando quiser renovar os dados):

	```bash
	python scripts/generate_dataset.py
	```

2. Carregue os documentos no Elasticsearch (executar apos o servico estar de pe):

	```bash
	docker compose up -d elasticsearch
	python scripts/load_documents.py --recreate-index
	```

3. Suba a API com recarregamento automático:

	```bash
	docker compose up --build api
	```

		A API ficara disponivel em `http://localhost:8000`. A rota `/search?query=...` retorna a ordenacao baseada na relevancia do Elasticsearch.

## Executando testes e lint

```bash
python -m pip install --upgrade pip
python -m pip install .[dev]
ruff check .
pytest
```

## Próximos passos sugeridos

- Integrar metricas de clique ao `combined_score` para refinar o ranking.
- Adicionar pipelines de ingestao ou agendamento para atualizar dados periodicamente.
- Expandir a suite de testes com cenarios de erro e integracao end-to-end.