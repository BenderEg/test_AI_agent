# AI Repo Assistant — RAG over GitHub Repositories

![CI](https://github.com/BenderEg/test_AI_agent/actions/workflows/ci.yml/badge.svg)

An AI-powered assistant that ingests GitHub repositories, stores code embeddings in a vector database, and enables contextual Q&A over a codebase using a local LLM — fully local, no data leaves your machine.

---

## Overview

The system implements a two-stage Retrieval-Augmented Generation (RAG) pipeline:

1. Fetch Python files from a GitHub repository via the GitHub API (no cloning)
2. Parse each file with AST to extract functions and classes with full signatures
3. Embed each chunk with `all-MiniLM-L6-v2` (SentenceTransformer) and store in Qdrant
4. On query: retrieve candidate chunks by vector similarity (bi-encoder), then rerank with a Cross-Encoder for higher precision
5. Build a token-aware context window and generate an answer via a local Ollama LLM

---

## Tech Stack

| Component | Role |
|-----------|------|
| **FastAPI** | Async REST API |
| **Qdrant** | Vector database (cosine similarity search) |
| **Ollama** | Local LLM inference |
| **SentenceTransformers** | Bi-encoder embeddings (`all-MiniLM-L6-v2`, 384-dim) + Cross-Encoder reranking (`ms-marco-MiniLM-L-6-v2`) |
| **aiohttp** | Async GitHub API client |
| **Docker Compose** | Three-service local deployment |

---

## Features

- **GitHub repo ingestion** — fetches files via GitHub API with async concurrency (semaphore=20, exponential backoff)
- **AST-based chunking** — extracts functions and classes using `ast.unparse()` for complete signatures including type annotations, `*args`, `**kwargs`, and base classes
- **Idempotent ingest** — point IDs are deterministic SHA256 hashes of `(repo_id, file_path, symbol)`, so re-ingesting the same repo is a no-op; `force=true` triggers a full re-index
- **Two-stage retrieval** — vector search fetches `limit×3` candidates, a Cross-Encoder reranks them to `limit`; each result carries both `score` (cosine) and `rerank_score`
- **Token-aware context** — context is truncated to 8 000 characters (2 000 per chunk) before being sent to the LLM, avoiding context window overflows without a tokenizer dependency
- **Query rewriting** — optional LLM-powered query rewrite before retrieval (`adapt_user_query=true`)
- **Observability** — structured `key=value` log lines at every pipeline stage; `/health` and `/readiness` endpoints
- **Graceful error handling** — `VectorDBError` → 503, `LLMError` → 502, `PermanentGitHubError` (401/403) is not retried

---

## Architecture

```
GitHub API (HTTP)
      ↓
GitHubParser  — async fetch, base64 decode, exponential backoff
      ↓
AST Chunker   — ast.unparse() signatures, module-level + class methods
      ↓
SentenceTransformer (bi-encoder, 384-dim)
      ↓
Qdrant  — deterministic point IDs, batched upsert (100 pts/batch)
      ↓
Vector Search  — cosine similarity, score_threshold filter
      ↓
Cross-Encoder  — ms-marco-MiniLM-L-6-v2 reranking
      ↓
Context Builder  — char-based truncation (8k chars)
      ↓
Ollama LLM  — local inference, 150s timeout
      ↓
Answer
```

---

## Getting Started

```bash
cp .env.example .env          # set GITHUB_TOKEN and optionally LLM_MODEL
make up-local                 # start FastAPI (:8000), Qdrant (:6333), Ollama (:11434)
make pull-model               # pull the model specified in .env (once after first start)
```

To stop: `make down-local`

---

## API Endpoints

### `POST /api/v1/repo_parser/ingest`
Fetches a GitHub repository, parses Python files with AST, embeds each chunk, and stores in Qdrant.

```json
{ "owner": "tiangolo", "repo": "fastapi", "branch": "master", "force": false }
```

- `force: true` — deletes existing vectors for this repo before re-indexing (handles renamed/deleted symbols)

### `GET /api/v1/repo_parser/query`
Vector-searches the index and returns matching code chunks with similarity scores.

```
?query=how does dependency injection work&owner=tiangolo&repo=fastapi&branch=master&limit=5&score_threshold=0.3
```

Response includes `items`, `total`, and `score_threshold_used`.

### `GET /api/v1/repo_parser/ask`
Two-stage retrieval + LLM answer generation.

```
?query=how does dependency injection work&owner=tiangolo&repo=fastapi&adapt_user_query=false
```

- `adapt_user_query=true` — rewrites the query via Ollama before retrieval

Response:
```json
{ "answer": "...", "context_found": true }
```

- `context_found: false` — no matching code was found in the vector DB; the LLM answered from general knowledge without a RAG context constraint

### `GET /api/v1/repo_parser/ask/stream`
Same as `/ask` but streams tokens as they are generated (use `curl -N`).

The `X-Context-Found: true/false` response header signals whether vector DB results were used.

### `GET /api/v1/health` / `GET /api/v1/readiness`
Liveness and readiness probes (readiness checks Qdrant connectivity).

---

## Configuration

All settings are in `.env` (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `GITHUB_TOKEN` | — | GitHub personal access token (required) |
| `LLM_MODEL` | `qwen2.5-coder:1.5b` | Ollama model name |
| `QDRANT_HOST` | `qdrant` | Qdrant service hostname |
| `LLM_HOST` | `ollama` | Ollama service hostname |
| `RERANKER_ENABLED` | `true` | Enable Cross-Encoder reranking |

---

## Development

```bash
make check     # ruff lint + mypy type check + pytest
make format    # auto-format with ruff
make test      # run pytest only
```

### CI

GitHub Actions runs `make check` (lint → typecheck → tests) on every push and pull request to `master`. The workflow installs only `requirements-dev.txt` — no runtime dependencies — since tests cover pure-Python utilities and mypy is configured with `ignore_missing_imports = true`.
