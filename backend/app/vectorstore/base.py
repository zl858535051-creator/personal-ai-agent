from dataclasses import dataclass


@dataclass
class VectorSearchResult:
    id: str
    score: float
    metadata: dict


class VectorStore:
    def add_texts(self, ids: list[str], embeddings: list[list[float]], metadatas: list[dict]) -> None:
        raise NotImplementedError

    def query(self, embedding: list[float], top_k: int = 5) -> list[VectorSearchResult]:
        raise NotImplementedError

    def delete_by_document(self, document_id: int) -> None:
        raise NotImplementedError

