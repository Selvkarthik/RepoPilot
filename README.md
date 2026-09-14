# RepoPilot

RepoPilot is an AI assistant for understanding GitHub repositories. It can read
repository metadata and files, synchronize supported source files into a
PostgreSQL/pgvector index, and retrieve relevant code for an agent response.

## How code search works

1. The agent sends implementation questions to `search_repository_code`.
2. The tool synchronizes the repository first, using the repository commit SHA
   and per-file content hashes to add, update, or delete indexed files.
3. The retriever searches the current code chunks and returns relevant context.

The database responsibilities are intentionally separate:

- `repositories`: branch and commit state
- `code_files`: per-file hashes and metadata
- `code_chunks`: embeddings and searchable code chunks

## Main components

- `agents/agent.py`: RepoPilot agent and its tool-use policy
- `tools/github_tools.py`: GitHub, synchronization, and code-search tools
- `rag/index_service.py`: repository and file-level synchronization
- `rag/retriever.py`: pgvector-backed code retrieval
- `app/main.py`: FastAPI application entry point

## Setup

Create a `.env` file with `OPENROUTER_API_KEY`, `GITHUB_TOKEN`, and `DB_URL`,
then install the packages in `requirements.txt`.

## Tests

Run the focused automated checks with:

```powershell
.\venv\Scripts\python.exe -m unittest rag.test_index_service tools.test_github_tools -v
```

## Technology

FastAPI, LangChain/LangGraph, OpenRouter, the GitHub API, PostgreSQL with
pgvector, and Sentence Transformers.
