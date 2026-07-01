import sys
from datetime import datetime
from pathlib import Path

from bson import ObjectId

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.database.vector import ensure_vector_indexes, repo_vectors
from src.rag.embeddings_rag import embed_repo


def build_vector_documents(embedded_chunks, user_id: str, repository_id: str):
    user_object_id = ObjectId(user_id)
    repository_object_id = ObjectId(repository_id)
    now = datetime.utcnow()

    documents = []
    for item in embedded_chunks:
        documents.append({
            "user_id": user_object_id,
            "repository_id": repository_object_id,
            "content": item["content"],
            "metadata": item["metadata"],
            "embedding": item["embedding"],
            "created_at": now,
        })

    return documents


def save_repo_vectors(repo_path: str, user_id: str, repository_id: str, replace=True):
    ensure_vector_indexes()

    embedded_chunks = embed_repo(repo_path)
    documents = build_vector_documents(embedded_chunks, user_id, repository_id)

    if replace:
        repo_vectors.delete_many({"repository_id": ObjectId(repository_id)})

    if not documents:
        return {"inserted_count": 0, "repository_id": repository_id}

    result = repo_vectors.insert_many(documents)
    return {
        "inserted_count": len(result.inserted_ids),
        "repository_id": repository_id,
    }

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python src/rag/vector_rag.py <repo_path> <user_id> <repository_id>")
        raise SystemExit(1)

    result = save_repo_vectors(
        repo_path=sys.argv[1],
        user_id=sys.argv[2],
        repository_id=sys.argv[3],
    )
    print(result)
