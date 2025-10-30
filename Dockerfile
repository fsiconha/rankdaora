FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
ENV POETRY_VERSION=1.8.3
ENV POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

COPY pyproject.toml poetry.lock* ./

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir "poetry==${POETRY_VERSION}" \
    && poetry install --no-interaction --no-ansi

COPY src ./src
COPY scripts ./scripts
COPY data ./data
COPY README.md ./

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
