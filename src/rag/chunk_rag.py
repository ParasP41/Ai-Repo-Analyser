import sys
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.rag.read_rag import read_repo_files


DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 150


def get_line_range(text: str, start_index: int, chunk_text: str):
    start_line = text[:start_index].count("\n") + 1
    end_line = start_line + chunk_text.count("\n")
    return start_line, end_line


def chunk_documents(documents, chunk_size=DEFAULT_CHUNK_SIZE, chunk_overlap=DEFAULT_CHUNK_OVERLAP):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        add_start_index=True,
    )
    chunks = splitter.split_documents(documents)
    source_content = {
        document.metadata.get("source", ""): document.page_content
        for document in documents
    }

    for index, chunk in enumerate(chunks):
        source = chunk.metadata.get("source", "")
        start_index = chunk.metadata.get("start_index", 0)
        start_line, end_line = get_line_range(source_content.get(source, ""), start_index, chunk.page_content)
        chunk.metadata["chunk"] = index
        chunk.metadata["chunk_index"] = index
        chunk.metadata["start_line"] = start_line
        chunk.metadata["end_line"] = end_line

    return chunks


def chunk_repo(repo_path: str, chunk_size=DEFAULT_CHUNK_SIZE, chunk_overlap=DEFAULT_CHUNK_OVERLAP):
    documents = read_repo_files(repo_path)
    return chunk_documents(documents, chunk_size, chunk_overlap)


def format_chunks(chunks, preview_chars=300):
    chunk_items = []
    for chunk in chunks:
        chunk_items.append({
            "chunk": chunk.metadata.get("chunk"),
            "source": chunk.metadata.get("source", ""),
            "start_line": chunk.metadata.get("start_line"),
            "end_line": chunk.metadata.get("end_line"),
            "characters": len(chunk.page_content),
            "content": chunk.page_content,
            "preview": chunk.page_content[:preview_chars],
        })

    return {
        "total_chunks": len(chunks),
        "chunks": chunk_items,
    }


def chunk_repo_data(repo_path: str, chunk_size=DEFAULT_CHUNK_SIZE, chunk_overlap=DEFAULT_CHUNK_OVERLAP):
    chunks = chunk_repo(repo_path, chunk_size, chunk_overlap)
    return format_chunks(chunks)


if __name__ == "__main__":
    repo_path = "public/temp/krishnaik06__Langchain-V1-Crash-Course"
    data = chunk_repo_data(repo_path)
    print(f"Total chunks: {data['total_chunks']}")
    for chunk in data["chunks"][:5]:
        print(f"[{chunk['chunk']}] {chunk['source']} lines {chunk['start_line']}-{chunk['end_line']}")
        print(chunk["preview"])
        print("---")
