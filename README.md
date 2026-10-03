# Personal Document Intelligence API

An API for asking grounded questions about personal documents, with verifiable
citations.

## Current scope

The first milestone establishes a small, testable FastAPI service. Document
ingestion, retrieval, embeddings, and answer generation will be added in later
milestones.

## Requirements

- Python 3.12
- [uv](https://docs.astral.sh/uv/)

## Run locally

```bash
uv sync
uv run uvicorn personal_document_intelligence_api.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`. Interactive documentation
is available at `http://127.0.0.1:8000/docs`.

## Quality checks

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

## Available endpoint

```text
GET /health
```

Expected response:

```json
{"status":"ok"}
```

