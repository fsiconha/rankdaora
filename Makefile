# Simple make targets mirroring CI checks

POETRY ?= poetry

.PHONY: pre-commit lint test install

pre-commit: lint test

lint:
	$(POETRY) run ruff check .

test:
	$(POETRY) run pytest

install:
	$(POETRY) install --no-interaction --with dev
