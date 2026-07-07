# Backend

FastAPI service for the Personal AI Agent.

## Run

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs` for API documentation.

ChromaDB is optional for local MVP usage because the vector layer has a JSON
fallback. Install it separately when your Python environment can build or
download `chroma-hnswlib`:

```bash
pip install -r requirements-vector.txt
```
