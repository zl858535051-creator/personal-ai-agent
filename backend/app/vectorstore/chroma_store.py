import json
import math
from pathlib import Path

from app.core.config import settings
from app.vectorstore.base import VectorSearchResult, VectorStore


class ChromaVectorStore(VectorStore):
    """Chroma adapter with a JSON fallback so the MVP runs without services."""

    def __init__(self) -> None:
        self._fallback_path = settings.absolute_vector_dir / "fallback_vectors.json"
        try:
            import chromadb

            client = chromadb.PersistentClient(path=str(settings.absolute_vector_dir))
            self._collection = client.get_or_create_collection("personal_ai_agent")
            self._use_chroma = True
        except Exception:
            self._collection = None
            self._use_chroma = False

    def add_texts(self, ids: list[str], embeddings: list[list[float]], metadatas: list[dict]) -> None:
        if self._use_chroma and self._collection is not None:
            self._collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas)
            return
        items = self._load()
        items = [item for item in items if item["id"] not in set(ids)]
        items.extend({"id": vid, "embedding": emb, "metadata": meta} for vid, emb, meta in zip(ids, embeddings, metadatas))
        self._save(items)

    def query(self, embedding: list[float], top_k: int = 5) -> list[VectorSearchResult]:
        if self._use_chroma and self._collection is not None:
            raw = self._collection.query(query_embeddings=[embedding], n_results=top_k)
            ids = raw.get("ids", [[]])[0]
            distances = raw.get("distances", [[]])[0]
            metadatas = raw.get("metadatas", [[]])[0]
            return [
                VectorSearchResult(id=item_id, score=1 / (1 + float(distance)), metadata=metadata or {})
                for item_id, distance, metadata in zip(ids, distances, metadatas)
            ]

        scored = [
            VectorSearchResult(
                id=item["id"],
                score=_cosine_similarity(embedding, item["embedding"]),
                metadata=item["metadata"],
            )
            for item in self._load()
        ]
        return sorted(scored, key=lambda result: result.score, reverse=True)[:top_k]

    def delete_by_document(self, document_id: int) -> None:
        if self._use_chroma and self._collection is not None:
            self._collection.delete(where={"document_id": document_id})
            return
        self._save([item for item in self._load() if item["metadata"].get("document_id") != document_id])

    def _load(self) -> list[dict]:
        if not self._fallback_path.exists():
            return []
        return json.loads(self._fallback_path.read_text(encoding="utf-8"))

    def _save(self, items: list[dict]) -> None:
        self._fallback_path.parent.mkdir(parents=True, exist_ok=True)
        self._fallback_path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)

