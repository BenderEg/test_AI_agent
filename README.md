🚀 AI Repo Assistant (RAG over GitHub Repositories)

This project is an AI-powered agent that ingests GitHub repositories, stores code embeddings in a vector database, and enables contextual Q&A over the codebase using a local LLM.

🧠 Overview

The system implements a Retrieval-Augmented Generation (RAG) pipeline:

- Parse a public GitHub repository via HTTP
- Extract Python files and split them into chunks
- Store chunks in Qdrant (vector database)
- Retrieve relevant chunks based on a query
- Generate answers using a local LLM via Ollama

⚙️ Tech Stack
FastAPI — API layer
Qdrant — vector storage
Ollama — local LLM inference
Python — core logic

📦 Features
📥 GitHub repo ingestion (no cloning required)
✂️ Smart chunking of Python files
🧠 Vector search with Qdrant
💬 Context-aware answers using LLM
⚡ Fully local RAG pipeline

🏗 Architecture

```mermaid
flowchart TD
    A[GitHub Repo (HTTP)] --> B[Parser (Python files)]
    B --> C[Chunking]
    C --> D[Embeddings]
    D --> E[Qdrant]
    E --> F[Retrieval]
    F --> G[Ollama (LLM)]
    G --> H[Response]
```


🚀 Getting Started

Set GITHUB_TOKEN=your_token in .env
To launch just use: make up-local
Do not forget to: make pull-model (the model you are actually planning to use and set in .env file)

🔌 API Endpoints

/api/v1/repo_parser/query : Retrieves the most relevant chunks from Qdrant (if you provide repo, owner and branch chuks will be found inside this repo only)
/api/v1/repo_parser/ask : Retrieves relevant context from Qdrant and generates an answer using Ollama.
/api/v1/repo_parser/ingest : Fetches a GitHub repository, extracts Python files, splits them into chunks, and stores them in Qdrant

📌 Future Improvements

LLM is slow (and sukcs by the way), only python files are ingested.
The logic of repo versions tracking is not covered (but may be).
The purpose is only to demostrate core idea of specific context querying.