from pathlib import Path

from langchain_community.document_loaders import DirectoryLoader, TextLoader


IGNORE_DIRS = [
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
]

IGNORE_EXTENSIONS = [
    "*.png",
    "*.jpg",
    "*.jpeg",
    "*.gif",
    "*.svg",
    "*.ico",
    "*.pdf",
    "*.zip",
    "*.exe",
    "*.dll",
    "*.pyc",
]


def get_file_filters():
    ignored_dirs = [f"**/{folder}/**" for folder in IGNORE_DIRS]
    ignored_files = [f"**/{extension}" for extension in IGNORE_EXTENSIONS]
    return ignored_dirs + ignored_files


def read_repo_files(repo_path: str):
    path = Path(repo_path)
    if not path.exists() or not path.is_dir():
        raise ValueError("Repository path does not exist")

    loader = DirectoryLoader(
        str(path),
        glob="**/*",
        exclude=get_file_filters(),
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
        recursive=True,
        silent_errors=True,
    )

    return loader.load()


def format_read_documents(documents, preview_chars=200):
    files = []
    for index, document in enumerate(documents):
        source = document.metadata.get("source", "")
        files.append({
            "index": index,
            "path": source,
            "characters": len(document.page_content),
            "preview": document.page_content[:preview_chars],
        })

    return {
        "total_files": len(documents),
        "files": files,
    }


def read_repo_data(repo_path: str, preview_chars=200):
    documents = read_repo_files(repo_path)
    return format_read_documents(documents, preview_chars)


if __name__ == "__main__":
    repo_path = "public/temp/krishnaik06__Langchain-V1-Crash-Course"
    data = read_repo_data(repo_path)
    print(f"Total files: {data['total_files']}")
    for file_data in data["files"][:5]:
        print(f"[{file_data['index']}] {file_data['path']} ({file_data['characters']} chars)")
