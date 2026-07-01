import sys
from pathlib import Path

from langchain_huggingface import HuggingFaceEmbeddings

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.rag.chunk_rag import chunk_repo


DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

LANGUAGE_BY_EXTENSION = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".html": "html",
    ".css": "css",
    ".md": "markdown",
    ".json": "json",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".toml": "toml",
    ".txt": "text",
}

_embedding_model_cache = {}


def get_embedding_model(model_name=DEFAULT_EMBEDDING_MODEL):
    if model_name not in _embedding_model_cache:
        _embedding_model_cache[model_name] = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embedding_model_cache[model_name]


def get_language(file_path: str):
    return LANGUAGE_BY_EXTENSION.get(Path(file_path).suffix.lower(), "text")


def get_repo_name(repo_path: str):
    return Path(repo_path).resolve().name


def add_chunk_metadata(chunks, repo_path: str):
    repo_name = get_repo_name(repo_path)
    for chunk in chunks:
        source = chunk.metadata.get("source", "")
        file_path = Path(source)
        chunk.metadata.update({
            "repo": repo_name,
            "path": source,
            "file_name": file_path.name,
            "language": get_language(source),
            "chunk": chunk.metadata.get("chunk", chunk.metadata.get("chunk_index")),
            "start_line": chunk.metadata.get("start_line"),
            "end_line": chunk.metadata.get("end_line"),
        })
    return chunks


def embed_chunks(chunks, repo_path: str, model_name=DEFAULT_EMBEDDING_MODEL):
    chunks = add_chunk_metadata(chunks, repo_path)
    embedding_model = get_embedding_model(model_name)
    texts = [chunk.page_content for chunk in chunks]

    batch_size = 128
    vectors = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        vectors.extend(embedding_model.embed_documents(batch))

    embedded_data = []
    for chunk, vector in zip(chunks, vectors):
        embedded_data.append({
            "content": chunk.page_content,
            "metadata": chunk.metadata,
            "embedding": vector,
        })

    return embedded_data


def embed_repo(repo_path: str, model_name=DEFAULT_EMBEDDING_MODEL):
    chunks = chunk_repo(repo_path)
    return embed_chunks(chunks, repo_path, model_name)


if __name__ == "__main__":
    repo_path = "public/temp/krishnaik06__Langchain-V1-Crash-Course"
    embeddings = embed_repo(repo_path)
    print(f"Total embedded chunks: {len(embeddings)}")
    if embeddings:
        for i, chunk in enumerate(embeddings[:5]):
            print(f"Chunk {i + 1}:")
            print(f"Content: {chunk['content']}")
            print(f"Metadata: {chunk['metadata']}")
            print(f"Embedding length: {len(chunk['embedding'])}")
            print("-" * 40)

