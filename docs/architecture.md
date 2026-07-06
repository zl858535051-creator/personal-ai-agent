# Architecture

Personal AI Agent uses a frontend/backend split. The backend owns file parsing, database state, RAG retrieval, LLM calls, Agent execution, and report generation. The frontend is a Vue 3 workbench for daily use.

## Backend Layers

- `api`: FastAPI route handlers. They validate HTTP input and call services.
- `services`: Business workflows for files, chat, RAG, Agent, reports, LLM, and embeddings.
- `models`: SQLite persistence using SQLAlchemy.
- `schemas`: Pydantic DTOs for requests and responses.
- `parsers`: File-specific text extraction.
- `vectorstore`: ChromaDB adapter with JSON fallback for local MVP usage.
- `agent`: Planner, tool registry, and executor.

## Storage

- `storage/uploads`: original uploaded files.
- `storage/vector_db`: Chroma persistence or fallback vector JSON.
- `storage/reports`: generated Markdown and PDF files.
- `storage/app.db`: SQLite database.

## RAG Flow

```text
File Upload
-> Parser
-> TextSplitter
-> EmbeddingService
-> VectorStore
-> RAGService query
-> LLMService answer
```

The first embedding implementation is deterministic and local so the app can run without a model download. The vector layer can later be upgraded to sentence-transformers or a remote embedding API without changing API routes.

