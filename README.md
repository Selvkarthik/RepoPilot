# RepoPilot

RepoPilot is an agentic AI assistant designed to navigate, understand, and answer complex architectural and implementation questions across GitHub repositories. It synchronizes repository files into a PostgreSQL/pgvector database, executes semantic code retrieval with deduplication, bounds search guardrails, accelerates queries via Redis caching, and offloads heavy synchronization jobs to Celery background workers.

---

## Architecture

```text
┌─────────────────┐        HTTP /ask        ┌─────────────────────────────────┐
│     Client      │ ──────────────────────> │           FastAPI App           │
└─────────────────┘                         └────────────────┬────────────────┘
                                                             │
                                                    Invoke LangChain Agent
                                                             │
                                                             ▼
                                            ┌─────────────────────────────────┐
                                            │         RepoPilot Agent         │
                                            │   (Model: OpenRouter / ling)    │
                                            └───────┬──────────────────┬──────┘
                                                    │                  │
                                 Guardrail Middleware                  │ GitHub Tools
                                 (Max 2 Search Calls &                 ▼
                                  Output Truncation)        ┌─────────────────────┐
                                            │               │    GitHub API       │
                                            ▼               │ (Metadata & Tree)   │
                               ┌─────────────────────────┐  └─────────────────────┘
                               │ search_repository_code  │
                               └────────────┬────────────┘
                                            │
                          ┌─────────────────┴─────────────────┐
                          │                                   │
                     Cache Check                         Cache Miss
                          ▼                                   ▼
             ┌─────────────────────────┐         ┌─────────────────────────┐
             │       Redis Cache       │         │      CodeRetriever      │
             │   (Key: repo:sha:query) │         │ (MiniLM-L6-v2 Embeddings│
             └─────────────────────────┘         └────────────┬────────────┘
                                                              │
                                                     pgvector Cosine Search
                                                              │
                                                              ▼
                                                 ┌─────────────────────────┐
                                                 │ PostgreSQL / pgvector   │
                                                 │ repositories            │
                                                 │ code_files              │
                                                 │ code_chunks             │
                                                 └─────────────────────────┘
```

```text
┌──────────────────┐    GitHub Webhook (push)    ┌───────────────────────────┐
│  GitHub Webhooks │ ──────────────────────────> │   /webhooks/github        │
└──────────────────┘    (HMAC SHA-256 Verified)  └─────────────┬─────────────┘
                                                               │
                                                      Enqueue sync task
                                                               │
                                                               ▼
                                                 ┌───────────────────────────┐
                                                 │    Redis Broker (Celery)  │
                                                 └─────────────┬─────────────┘
                                                               │
                                                               ▼
                                                 ┌───────────────────────────┐
                                                 │    Celery Sync Worker     │
                                                 │  (Incremental Indexer)    │
                                                 └───────────────────────────┘
```

---

## Features

- **Agentic Code Reasoning**: Uses a LangChain-powered agent configured with OpenRouter LLMs to intelligently decide whether to inspect repository metadata or perform semantic code search.
- **Incremental Repository Indexing**: Computes SHA-256 content hashes per file and compares them against GitHub commit SHAs to only index newly added or modified source files. Automatically deletes stale chunks when files are removed.
- **Semantic pgvector Retrieval**: Chunks code files and embeds them with `sentence-transformers/all-MiniLM-l6-v2`, performing cosine vector similarity search.
- **Multi-Level Redis Caching**: Hashes the repository, commit SHA, and normalized query to cache search results, providing sub-millisecond responses on repeat queries with automatic cache invalidation on new commits.
- **Controlled Search Guardrails**: Custom `SearchLimitMiddleware` caps search calls to at most 2 per user question and truncates oversized search outputs to protect LLM context windows.
- **Asynchronous Webhook Worker**: Accepts GitHub `push` webhooks validated via HMAC-SHA256 signatures, dispatching background synchronization via Celery.
- **Fail-Safe Resilience**: Gracefully handles transient Redis cache hiccups, malformed payloads, and external provider failures with detailed logging and sanitized API responses.

---

## Tech Stack

- **Application & Framework**: FastAPI, Pydantic v2, Uvicorn
- **AI & Agent Orchestration**: LangChain, LangChain-OpenRouter, Sentence-Transformers (`all-MiniLM-l6-v2`)
- **Database & Vector Store**: PostgreSQL with `pgvector` extension, Psycopg 3
- **Caching & Message Broker**: Redis 7, Celery 5
- **Testing & Tooling**: Pytest, Docker, Docker Compose

---

## How RepoPilot Works

### 1. Repository Synchronization
When indexing is triggered, RepoPilot queries GitHub for the current branch and HEAD commit SHA:
- If the repository commit SHA in the database matches GitHub, indexing short-circuits with `"status": "up_to_date"`.
- If new or updated, the repository file tree is fetched and filtered by supported programming languages (`.py`, `.js`, `.ts`, `.tsx`, `.jsx`, `.java`, `.cpp`, `.c`, `.go`, `.rs`, `.php`, `.cs`).

### 2. Incremental Indexing
- Hashes of all stored files are compared with GitHub file content hashes.
- **Deleted files**: Chunks and file records are immediately deleted from `code_chunks` and `code_files`.
- **Modified files**: Existing chunks for updated files are purged before new chunks are inserted.
- **New files**: Split and embedded using `HuggingFaceEmbeddings`.
- The database transaction commits updated commit SHA metadata to `repositories`.

### 3. Code Retrieval
Queries are embedded using `sentence-transformers/all-MiniLM-l6-v2`. The `CodeRetriever` invokes `CodeRepository.similarity_search` to query PostgreSQL:
```sql
SELECT file_path, chunk_index, content, language, embedding <=> %s::vector AS distance
FROM code_chunks
WHERE repository = %s
ORDER BY embedding <=> %s::vector
LIMIT %s
```
Deduplication is performed on file paths to prioritize relevant file coverage.

### 4. Agent Workflow
The RepoPilot agent is initialized with tools:
- `get_repository_info`: Repository stats, description, default branch, stars.
- `get_repository_structure`: Top-level and directory folder layouts.
- `get_directory_contents`: Specific directory contents.
- `search_repository_code`: Semantic retrieval over indexed code chunks.

The agent prompt instructs the model to ground answers strictly in retrieved repository code, use metadata tools for layout questions, and summarize technical implementations clearly.

### 5. Redis Caching
Search results are indexed by a SHA-256 key composed of:
```text
repopilot:search:sha256(repository + ":" + commit_sha + ":" + normalized_query)
```
- **Hit**: Returns cached result instantly with log `CACHE HIT: repo=<repo> query=<query>`.
- **Miss**: Executes vector search, caches response for 1 hour (`CACHE_TTL = 3600`), and logs `CACHE MISS`.
- If new commits are pushed, the commit SHA shifts, naturally invalidating stale cache entries.

### 6. Background Processing / Celery
Heavy repository synchronization operations run asynchronously:
- Celery worker tasks execute `index_repository(owner, repo)` with exponential backoff retries.
- Webhooks return `200 accepted` in milliseconds, while the background worker handles file fetching, embedding, and database persistence.

### 7. Guardrails
- **Execution Limits**: `SearchLimitMiddleware` counts prior search tool calls in the message history. If 2 searches have already run, subsequent search requests are blocked with an instructional `ToolMessage`.
- **Output Bounding**: Search results exceeding 12,000 characters are safely sliced with a `\n[Result truncated]` marker, preventing LLM token overflow.
- **Input Validation**: Strict regex validation on repository names (`owner/repo`) and bounded question lengths (1–2000 characters).

---

## Evaluation

RepoPilot includes an automated evaluation benchmark (`evals/retrieval_eval.py`) assessing code retrieval performance against a curated dataset of repository questions (`evals/dataset.py`).

### Retrieval Benchmark Metrics
Evaluated across 10 test cases on `Selvkarthik/DocQuery`:

| Metric | Score | Target | Description |
|:-------|:-----:|:------:|:------------|
| **Hit@1** | **60.00%** | >= 50% | Expected file is the #1 retrieved result |
| **Hit@3** | **90.00%** | >= 80% | Expected file is within the top 3 retrieved results |
| **MRR** | **0.717** | >= 0.70 | Mean Reciprocal Rank across all test cases |

To run the retrieval evaluation:
```powershell
python -m evals.retrieval_eval
```

---

## Project Structure

```text
RepoPilot/
├── agents/
│   ├── agent.py               # Agent definition and system prompt
│   └── middleware.py          # SearchLimitMiddleware (rate limits & truncation)
├── app/
│   ├── main.py                # FastAPI application and webhook endpoints
│   └── models.py              # Pydantic request/response validation schemas
├── core/
│   ├── config.py              # Centralized environment settings
│   └── logging_config.py      # Production structured logging setup
├── evals/
│   ├── dataset.py             # Evaluation benchmark question dataset
│   └── retrieval_eval.py      # Retrieval evaluation runner (Hit@1, Hit@3, MRR)
├── rag/
│   ├── cache.py               # Redis caching client and key generator
│   ├── database.py            # PostgreSQL connection manager
│   ├── documents.py           # Document transformation
│   ├── embeddings.py          # HuggingFace sentence transformer embedding model
│   ├── indexer.py             # GitHub file scraper and content hasher
│   ├── index_service.py       # Incremental indexing orchestrator
│   ├── repository.py          # Database queries (pgvector similarity, hashes)
│   ├── retriever.py           # LangChain BaseRetriever implementation
│   ├── splitter.py            # RecursiveCharacterTextSplitter configuration
│   └── vector_store.py        # Chunk vector embedding and storage
├── tests/
│   ├── test_api.py            # API validation and error handling tests
│   ├── test_cache.py          # Redis cache HIT/MISS and invalidation tests
│   ├── test_indexing.py       # Incremental indexing and file change tests
│   ├── test_middleware.py     # Search limit and truncation guardrail tests
│   └── test_webhook.py        # HMAC webhook signature verification tests
├── tools/
│   ├── github_client.py       # PyGithub client initialization
│   └── github_tools.py        # LangChain tools for GitHub inspection & search
├── workers/
│   ├── celery_app.py          # Celery worker initialization
│   └── repository_worker.py   # Background repository synchronization task
├── .env.example               # Example environment variable template
├── .gitignore                 # Git ignore specifications
├── docker-compose.yml         # Multi-container orchestration (FastAPI, Redis, Postgres, Celery)
├── Dockerfile                 # Container image specification
└── requirements.txt           # Python package dependencies
```

---

## Environment Variables

Copy `.env.example` to `.env` and supply your credentials:

```bash
cp .env.example .env
```

| Variable | Description | Example |
|:---------|:------------|:--------|
| `OPENROUTER_API_KEY` | OpenRouter API Key for LLM completion | `sk-or-v1-...` |
| `OPENROUTER_MODEL` | OpenRouter Model identifier | `inclusionai/ling-3.0-flash-fin:free` |
| `GITHUB_TOKEN` | GitHub Personal Access Token | `github_pat_...` |
| `GITHUB_WEBHOOK_SECRET` | Secret for verifying GitHub push webhooks | `your_secret_hash` |
| `DB_URL` | PostgreSQL connection string with pgvector | `postgresql://postgres:password@localhost:5432/repopilot` |
| `REDIS_BROKER_URL` | Celery broker URL | `redis://localhost:6379/0` |
| `REDIS_RESULT_BACKEND`| Celery results backend | `redis://localhost:6379/1` |
| `REDIS_CACHE_URL` | Redis search cache database | `redis://localhost:6379/2` |

---

## Local Setup

### 1. Prerequisites
- Python 3.11+
- PostgreSQL 15+ with `pgvector` extension enabled
- Redis server

### 2. Installation
```powershell
# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Initialization
Ensure PostgreSQL has the `vector` extension enabled and tables created:
```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS repositories (
    id SERIAL PRIMARY KEY,
    owner VARCHAR(255) NOT NULL,
    repo VARCHAR(255) NOT NULL,
    branch VARCHAR(255) NOT NULL,
    commit_sha VARCHAR(255) NOT NULL,
    last_indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(owner, repo)
);

CREATE TABLE IF NOT EXISTS code_files (
    id SERIAL PRIMARY KEY,
    repository VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    language VARCHAR(50),
    content_hash VARCHAR(64) NOT NULL,
    last_indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(repository, file_path)
);

CREATE TABLE IF NOT EXISTS code_chunks (
    id SERIAL PRIMARY KEY,
    repository VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    language VARCHAR(50),
    chunk_index INT NOT NULL,
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    embedding vector(384),
    UNIQUE(repository, file_path, chunk_index)
);
```

### 4. Running the Application
Start the FastAPI server:
```powershell
uvicorn app.main:app --reload --port 8000
```

### 5. Running the Celery Worker
In a separate terminal:
```powershell
celery -A workers.celery_app worker --loglevel=info -P solo
```

---

## Docker Setup

Run the entire stack (FastAPI, Celery worker, PostgreSQL with pgvector, and Redis) using Docker Compose:

```bash
docker compose up --build
```

Services exposed:
- FastAPI API: `http://localhost:8000`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

---

## API Usage

### Health Check
```bash
curl http://localhost:8000/
```
Response:
```json
{
  "msg": "RepoPilot is running"
}
```

### Ask Question (`POST /ask`)
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "repository": "selvkarthik/DocQuery",
    "question": "How does document ingestion process uploaded documents?"
  }'
```

Example Response:
```json
{
  "repository": "selvkarthik/DocQuery",
  "answer": "Document ingestion in DocQuery is handled in `rag/ingest.py`. Uploaded files are received by the endpoint, extracted for text, chunked using character splitters, and embedded into pgvector with associated metadata."
}
```

### GitHub Webhook (`POST /webhooks/github`)
Configure GitHub repository webhooks to send `push` events to:
`https://your-domain.com/webhooks/github` with your configured secret.

---

## Testing

Run the full automated test suite using `pytest`:

```powershell
pytest -v
```

The test suite contains 26 comprehensive automated tests covering:
- **API Tests**: Valid `/ask` requests, invalid repository formats, empty/oversized questions, error handling.
- **Cache Tests**: Cache misses, cache hits on repeated queries, cache key differentiation, new commit invalidation, Redis connection failure fallback.
- **Indexing Tests**: Fresh repository ingestion, unchanged commit bypass, modified file updates, deleted file cleanup.
- **Middleware Tests**: First and second search allowance, third search blocking, unrelated tool passthrough, oversized output truncation.
- **Webhook Tests**: Valid HMAC signatures, invalid signatures, missing signatures, non-push event filtering.

---

## Known Limitations / Future Improvements

- **Language-Specific AST Chunking**: Currently uses character splitting; tree-sitter AST-based parsing could preserve structural function boundaries more strictly.
- **BM25 Hybrid Search**: Combining pgvector cosine search with BM25 keyword matching could improve identifier lookups.
- **Multi-Branch Indexing**: Current index maps to the default branch; branch-specific indexing would allow comparing pull requests.
