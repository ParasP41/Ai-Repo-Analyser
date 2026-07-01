import sys
from math import sqrt
from pathlib import Path
from typing import Optional

from bson import ObjectId
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.database.vector import repo_vectors
from src.rag.embeddings_rag import get_embedding_model


def cosine_similarity(first, second):
    dot = sum(a * b for a, b in zip(first, second))
    first_norm = sqrt(sum(a * a for a in first))
    second_norm = sqrt(sum(b * b for b in second))

    if not first_norm or not second_norm:
        return 0.0

    return dot / (first_norm * second_norm)


class MongoVectorRetriever(BaseRetriever):
    repository_id: str
    user_id: Optional[str] = None
    k: int = 5

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
    ):
        query_embedding = get_embedding_model().embed_query(query)

        filters = {"repository_id": ObjectId(self.repository_id)}
        if self.user_id:
            filters["user_id"] = ObjectId(self.user_id)

        stored_chunks = repo_vectors.find(filters)
        results = []

        for chunk in stored_chunks:
            score = cosine_similarity(query_embedding, chunk["embedding"])
            metadata = chunk.get("metadata", {})
            metadata["score"] = score
            metadata["vector_id"] = str(chunk["_id"])

            results.append(Document(
                page_content=chunk["content"],
                metadata=metadata,
            ))

        results.sort(key=lambda document: document.metadata["score"], reverse=True)
        return results[:self.k]


def get_retriever(repository_id: str, user_id: Optional[str] = None, k: int = 5):
    return MongoVectorRetriever(
        repository_id=repository_id,
        user_id=user_id,
        k=k,
    )


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python src/rag/retriever.py <repository_id> <question> [k]")
        raise SystemExit(1)

    retriever = get_retriever(
        repository_id=sys.argv[1],
        k=int(sys.argv[3]) if len(sys.argv) > 3 else 5,
    )
    documents = retriever.invoke(sys.argv[2])

    for index, document in enumerate(documents, start=1):
        print("\n" + "=" * 80)
        print(f"Result {index}")
        print("Score:", document.metadata.get("score"))
        print("Metadata:", document.metadata)
        print("Content:")
        print(document.page_content)
