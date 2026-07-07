from fastapi.testclient import TestClient

from app.main import app
from app.schemas.document import KnowledgeAnswer, KnowledgeAnswerSource


def test_knowledge_query_returns_rag_answer(monkeypatch) -> None:
    async def fake_answer_query(self, query, top_k=None):
        return KnowledgeAnswer(
            answer="测试回答",
            sources=[KnowledgeAnswerSource(filename="demo.txt", chunk_index="chunk 1")],
            confidence=0.88,
            retrieved_sources=[],
        )

    monkeypatch.setattr("app.api.v1.knowledge.RAGService.answer_query", fake_answer_query)

    response = TestClient(app).post("/api/v1/knowledge/query", json={"query": "总结", "top_k": 3})

    assert response.status_code == 200
    assert response.json()["answer"] == "测试回答"
    assert response.json()["sources"][0]["filename"] == "demo.txt"
    assert response.json()["confidence"] == 0.88
