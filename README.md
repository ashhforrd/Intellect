# Intellect

Intellect is a collaborative document-intelligence platform for exploring
project knowledge through semantic search, grounded AI answers, citations,
interactive knowledge graphs, and actionable conversation insights.

It transforms uploaded PDF and DOCX files into searchable knowledge by combining
OCR, asynchronous document processing, OpenAI embeddings, PostgreSQL with
pgvector, and retrieval-augmented generation.

> This repository is a portfolio project focused on practical AI engineering,
> retrieval quality, inspectability, and maintainable backend architecture.

## Demo

<div>
  <a href="https://www.loom.com/share/8e08ae31ac224651be131ef4e2ec05fa">
    <img
      src="Thumbnail.png"
      alt="Watch the Intellect document intelligence demo"
      width="900"
    />
  </a>
</div>

[Watch the full demo on Loom →](https://www.loom.com/share/8e08ae31ac224651be131ef4e2ec05fa)

The demo covers document upload, asynchronous processing, grounded document
Q&A, source inspection, and conversational knowledge graphs.

## Features

- PDF and DOCX document ingestion
- Project workspaces with member roles and strict document isolation
- Dedicated multi-file document workspace with preview and processing status
- OCR for scanned content using Tesseract
- Asynchronous processing with Amazon SQS workers
- OpenAI embedding generation
- PostgreSQL and pgvector semantic search
- Grounded RAG answers with citations
- Relevance filtering and deterministic fallback behavior
- Inspectable retrieval chunks and similarity scores
- Interactive conversation knowledge graphs
- Key takeaways and priority-ranked next actions per conversation
- Document preview and management
- Authenticated team accounts, prompt attribution, and rate limiting
- Retrieval and generation evaluation runners

## Architecture

```mermaid
flowchart LR
    Browser[React project workspace] --> API[FastAPI API]
    API --> Access[Project membership boundary]
    API --> Storage[S3 or local storage]
    API --> Database[PostgreSQL and pgvector]
    API --> Queue[Amazon SQS]
    Queue --> Worker[Document worker]
    Worker --> Storage
    Worker --> OCR[Tesseract OCR]
    Worker --> Embeddings[OpenAI embeddings]
    Worker --> Database
    API --> Retrieval[Semantic retrieval]
    Retrieval --> Database
    Retrieval --> Generation[Grounded generation]
    Generation --> OpenAI[OpenAI API]
    API --> Graph[Knowledge graph extraction]
    Graph --> OpenAI
```

### Main components

| Component | Responsibility |
| --- | --- |
| React frontend | Project-scoped chat, document management, citations, insights, and graph visualization |
| FastAPI API | Projects, memberships, upload, semantic search, RAG, insights, and graph endpoints |
| Document worker | Parsing, OCR, chunking, embedding generation, and vector indexing |
| PostgreSQL | Projects, memberships, documents, sections, chunks, vectors, and saved insights |
| pgvector | Vector storage and similarity search |
| Amazon S3 | Original document storage |
| Amazon SQS | Asynchronous document-processing jobs |
| OpenAI | Embeddings, grounded answers, and structured graph extraction |
| Tesseract | OCR for scanned document content |

## Document processing flow

```text
Document upload
      │
      ├── Store original file
      ├── Save document metadata
      └── Publish processing job
                 │
                 ▼
            SQS worker
                 │
                 ├── Download document
                 ├── Parse text
                 ├── Run OCR when needed
                 ├── Create text chunks
                 ├── Generate embeddings
                 └── Store chunks and vectors in PostgreSQL
```

The upload endpoint returns before expensive extraction and embedding work is
completed. The worker processes those tasks independently so the API remains
responsive.

Every document and chunk carries a `project_id`. Retrieval joins project
membership before returning any chunk, so project isolation is enforced by the
backend rather than trusted to the frontend. Existing installations are
backfilled into a Personal project by the migration.

## RAG flow

```text
User question
      │
      ├── Generate query embedding
      ├── Search similar pgvector chunks
      ├── Filter low-relevance results
      ├── Build grounded context
      ├── Generate an answer
      └── Return answer, citations, and retrieval evidence
```

When no sufficiently relevant source is found, the service returns a
deterministic fallback instead of generating an unsupported answer.

## Knowledge graph

Intellect generates a structured knowledge graph from the current conversation.
The graph focuses on useful learning concepts and meaningful relationships rather
than raw source excerpts. The backend performs structured extraction, while the
frontend renders the result as an interactive React Flow graph.

## Conversation insights

The adjacent Insights view derives concise takeaways and priority-ranked next
actions from the current grounded conversation. Results are saved by project and
thread. Insight extraction is deterministic and does not send the conversation
to an additional external model.

## Inspectable AI

The interface exposes more than the generated answer:

- Source citations
- Similarity scores
- Retrieved text chunks
- Answer-construction details
- Interactive concept relationships

This makes retrieval failures and unsupported claims easier to identify than in
a black-box chat interface.

## Evaluation

The project contains repeatable evaluation runners for retrieval and generation.

Retrieval evaluation measures expected-content hits, expected-term coverage,
aggregate hit rate, and average term coverage. Generation evaluation covers
citation validity, citation completeness, grounded fallback behavior, and
unsupported-source rejection.

The current evaluation dataset is intentionally small and acts as a regression
suite rather than a production benchmark.

```bash
uv run python -m personal_document_intelligence_api.evaluation.runner \
  --project-id <project-uuid>
uv run pytest
```

Current backend test status:

```text
48 passed
```

## Technology stack

### Backend

- Python 3.12
- FastAPI
- SQLAlchemy and Alembic
- PostgreSQL and pgvector
- OpenAI API
- Tesseract OCR
- Amazon S3 and SQS
- pytest, Ruff, and uv

### Frontend

- React and TypeScript
- Vite
- assistant-ui
- React Flow
- JetBrains Mono
- oxlint

### Infrastructure

- Docker
- Amazon ECR
- AWS IAM
- AWS S3
- AWS SQS

The application is containerized and designed for cloud deployment. A complete
production deployment is not currently included in this repository.

## Project structure

```text
.
├── frontend/
│   ├── public/
│   └── src/
├── migrations/
├── src/
│   └── personal_document_intelligence_api/
│       ├── api/
│       ├── core/
│       ├── database/
│       ├── documents/
│       ├── embeddings/
│       ├── evaluation/
│       ├── generation/
│       ├── insights/
│       ├── jobs/
│       ├── knowledge/
│       ├── rag/
│       ├── search/
│       ├── storage/
│       └── workers/
├── tests/
├── Dockerfile
├── pyproject.toml
└── uv.lock
```

## Local development

### Prerequisites

- Python 3.12
- uv
- Node.js
- PostgreSQL with pgvector
- Tesseract OCR
- An OpenAI API key
- AWS credentials when using S3 and SQS

### 1. Clone and install

```bash
git clone https://github.com/ashhforrd/Intellect.git
cd Intellect
uv sync
```

### 2. Configure the environment

macOS, Linux, or Git Bash:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Generate a cryptographically secure session secret. This value signs login
session cookies and is required by the development startup script.

macOS or Linux:

```bash
openssl rand -hex 32
```

Windows PowerShell, or any platform with Python installed:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the generated value into `.env`:

```dotenv
ANONYMOUS_SESSION_SECRET=<generated-64-character-value>
```

Then update the remaining required database, OpenAI, storage, and queue
settings. Each developer should generate their own session secret. Never commit
`.env`, the generated secret, or any real credentials.

### 3. Run database migrations

```bash
uv run alembic upgrade head
```

### 4. Start the API

```bash
AWS_PROFILE=document-intelligence \
uv run uvicorn personal_document_intelligence_api.main:app --reload
```

API documentation is available at <http://127.0.0.1:8000/docs>.

### 5. Start the worker

Open a second terminal:

```bash
AWS_PROFILE=document-intelligence \
uv run python -m personal_document_intelligence_api.workers.runner
```

### 6. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend is available at <http://localhost:5173>.

### Run the complete development stack

After configuring `.env` and installing the backend and frontend dependencies,
start PostgreSQL, apply migrations, and run the API, document worker, and
frontend from one terminal:

```bash
./scripts/dev.sh
```

`dev.sh` is a Bash script. On Windows, run it through Git Bash or WSL:

```bash
bash scripts/dev.sh
```

If the script reports an incomplete environment setting, update that key in
`.env`; placeholder values from `.env.example` are intentionally rejected.

Press `Ctrl+C` to stop the API, worker, and frontend. PostgreSQL remains
available in Docker so subsequent starts do not need to recreate the database.

## Docker

Build the backend image:

```bash
docker build \
  --platform linux/amd64 \
  -t document-intelligence-api:local \
  .
```

The API and worker use the same image with different commands.

```text
API:    uv run --no-sync uvicorn personal_document_intelligence_api.main:app --host 0.0.0.0 --port 8000
Worker: uv run --no-sync python -m personal_document_intelligence_api.workers.runner
```

## Quality checks

```bash
uv run ruff format .
uv run ruff check . --fix
uv run pytest

cd frontend
npm run lint
npm run build
```

## Design decisions

### Asynchronous ingestion

OCR and embedding generation are not performed during the upload request. SQS
separates ingestion from processing and allows workers to scale independently.

### Storage and queue abstractions

Application services depend on storage and queue interfaces rather than directly
coupling business logic to AWS implementations.

### PostgreSQL as relational and vector storage

Document metadata and vectors remain in the same database. This simplifies
ownership filtering and avoids introducing a separate vector database
prematurely.

### Retrieval filtering

Vector similarity alone does not guarantee relevance. A minimum relevance
threshold prevents answer generation when retrieval evidence is too weak.

### Project isolation

Projects are the authorization boundary. Documents, chunks, retrieval, RAG,
graphs, and saved insights are resolved in the current project. Membership roles
are `owner`, `editor`, and `viewer`. Login sessions use signed, HttpOnly cookies,
and successful conversation turns retain the authenticated author so a team can
see who submitted each prompt.

### Inspectability

Sources, chunks, scores, and graph relationships are visible so users can inspect
how an answer was constructed.

## Current limitations

- The evaluation dataset is intentionally small.
- The in-memory rate limiter is designed for a single API process.
- Thread rendering state remains client-oriented; successful grounded turns are also persisted server-side for attribution.
- The Docker image is functional but not optimized for minimum size.
- A one-command Docker Compose environment is not yet included.
- Production monitoring, automated backups, and deployment remain future work.

## Future improvements

- Redis-backed distributed rate limiting
- Fully shared server-backed thread lists and history
- Hybrid keyword and vector retrieval
- Retrieval reranking
- Larger evaluation datasets
- Document-processing observability and retry metrics
- Docker Compose development environment
- Infrastructure as code
- Streaming answers
- Password reset and invitation email flows

## Author

**Atqiya Haydar**

GitHub: [@ashhforrd](https://github.com/ashhforrd)
