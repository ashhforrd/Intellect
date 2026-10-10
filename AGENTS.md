# Intellect

Collaborative document intelligence: Python/FastAPI API and document worker in
`src/personal_document_intelligence_api/`, React/TypeScript/Vite UI in `frontend/`.

## References by task

- For setup or running services, use [README.md](README.md). The stack launcher
  is `bash scripts/dev.sh`; on Windows use Git Bash or configured WSL.
- For service boundaries, ingestion, authorization, persistence, or retrieval
  changes, use the relevant sections of [docs/architecture.md](docs/architecture.md).
  Update them when the architecture changes.
- Tooling and dependencies are defined in `pyproject.toml` and
  `frontend/package.json`; use uv for Python and npm for the frontend.

## Rules for changes

Backend paths below are relative to `src/personal_document_intelligence_api/`.

- Preserve project membership filtering in reads and retrieval, and role checks
  in writes. Client-supplied project/document IDs do not establish access.
- Keep HTTP contracts in `api/`, domain behavior in services, and database queries
  in `database/repositories/`. Extend existing provider interfaces and factories.
- Keep blocking SDK, parsing, OCR, and provider calls off the async event loop.
  Preserve transaction rollback and file cleanup on failures.
- Persisted uploads are processed by the worker. Preserve duplicate-job and
  deleted-document handling, evidence metadata, and the weak-evidence RAG fallback.
- Schema changes need matching SQLAlchemy models and a new Alembic revision in
  `migrations/versions/`. Embeddings use `Vector(1536)`; dimension changes also need
  coordinated provider configuration and regeneration of stored vectors.
- Keep frontend requests/types in `frontend/src/api/` aligned with backend
  schemas. When changing persistence, account for both browser-local chat state
  and database conversation records, including project/account scope.
- Add backend configuration in `core/config.py` and document variables in
  `.env.example`. Keep secrets and uploaded document contents out of commits/logs.

## Validation

Choose checks for the affected behavior; report results and checks not run.

| Change | Working directory | Checks |
| --- | --- | --- |
| Backend | Repository root | `uv run ruff check .`, `uv run ruff format --check .`, focused `uv run pytest <test-path>` |
| Frontend | `frontend/` | `npm run lint`, `npm run build` (includes TypeScript checking) |
| Documentation | Repository root | Verify links, paths, commands, and whitespace |

Use `uv run pytest` for broad backend changes. Retrieval evaluation prerequisites
and commands are in the architecture document; that runner uses real embedding
requests. Documentation edits do not require starting the stack or running
application tests.
