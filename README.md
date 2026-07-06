# Personal AI Agent

本项目是一个可本地运行的个人 AI Agent 智能助手，支持文件知识库、RAG 问答、多轮聊天、Agent 任务分析，以及 Markdown/PDF 报告生成。

## Features

- 上传并解析 PDF、Word、TXT、Markdown 文件
- 自动文本切片并写入本地向量库
- 基于知识库进行聊天问答并返回引用来源
- 保存聊天会话和历史消息
- Agent 自动识别任务类型，例如漏洞报告分析
- 生成 Markdown 或 PDF 报告
- Vue 3 工作台界面：聊天、文件、历史、报告

## Tech Stack

- Backend: Python 3.11, FastAPI, SQLAlchemy, SQLite
- Vector Store: ChromaDB with JSON fallback
- AI: OpenAI-compatible chat API with local fallback
- Documents: pypdf, python-docx
- Reports: Markdown, reportlab PDF
- Frontend: Vue 3, Vite, TypeScript, Axios

## Quick Start

### Backend

```bash
cd personal-ai-agent/backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

API docs: `http://localhost:8000/docs`

To use a real LLM, edit `backend/.env`:

```env
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
```

OpenAI-compatible providers such as DeepSeek, 通义千问, or 智谱 can be used by changing `LLM_BASE_URL` and `LLM_MODEL`.

### Frontend

```bash
cd personal-ai-agent/frontend
npm install
npm run dev
```

Frontend URL: `http://localhost:5173`

## Project Structure

```text
backend/app
├── api          HTTP routes
├── agent        planner, tools, executor
├── core         config, database, exceptions
├── models       SQLAlchemy models
├── parsers      PDF, Word, Markdown, TXT parsers
├── schemas      Pydantic request/response models
├── services     business workflows
├── utils        text splitting and citation helpers
└── vectorstore  Chroma adapter and fallback store
```

## Core Workflows

1. Upload file: save file, parse text, split chunks, embed text, index vectors.
2. Chat: save message, retrieve relevant chunks, call LLM, return answer and sources.
3. Agent: classify task, retrieve context, analyze with LLM, save structured result.
4. Reports: write Markdown or render PDF, save report metadata.

## Tests

```bash
cd personal-ai-agent/backend
pytest
```

## Roadmap

- Add user authentication
- Add streaming chat responses
- Add richer document metadata and page-level citations
- Add configurable embedding providers
- Add background indexing jobs
- Add Docker image builds for backend and frontend

