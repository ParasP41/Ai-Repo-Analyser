import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from fastapi import HTTPException, status
from pydantic import BaseModel, Field

from src.models.repo_model import repositories
from src.rag.vector_rag import save_repo_vectors


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEMP_REPO_DIR = PROJECT_ROOT / "public" / "temp"


class CloneRepoRequest(BaseModel):
    github_url: str = Field(..., min_length=1)


def get_github_repo(github_url: str) -> tuple[str, str, str]:
    parsed_url = urlparse(github_url.strip())

    if parsed_url.scheme not in {"http", "https"} or parsed_url.netloc != "github.com":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid GitHub URL",
        )

    path_parts = parsed_url.path.strip("/").split("/")
    if len(path_parts) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid GitHub repository URL",
        )

    owner = path_parts[0]
    repo_name = path_parts[1].removesuffix(".git")
    clone_url = f"https://github.com/{owner}/{repo_name}.git"
    return owner, repo_name, clone_url


def get_temp_repo_path(path):
    repo_path = Path(path).resolve()
    temp_path = TEMP_REPO_DIR.resolve()

    if temp_path not in repo_path.parents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid repository path",
        )

    return repo_path


def delete_repo(path):
    repo_path = get_temp_repo_path(path)

    if repo_path.exists():
        shutil.rmtree(repo_path)


def update_repo(path):
    repo_path = get_temp_repo_path(path)

    if not repo_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found",
        )

    result = subprocess.run(
        ["git", "pull"],
        cwd=str(repo_path),
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to update repository",
        )

    return {"message": "Repository updated successfully"}


def clone_to_temp(github_url: str):
    owner, repo_name, clone_url = get_github_repo(github_url)

    TEMP_REPO_DIR.mkdir(parents=True, exist_ok=True)
    local_path = TEMP_REPO_DIR / f"{owner}__{repo_name}"

    if local_path.exists():
        delete_repo(local_path)

    result = subprocess.run(
        ["git", "clone", clone_url, str(local_path)],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        delete_repo(local_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to clone repository",
        )

    return repo_name, clone_url, local_path


def index_repository(payload: CloneRepoRequest, current_user: dict):
    repo_name, clone_url, local_path = clone_to_temp(payload.github_url)

    repo_data = {
        "user_id": current_user["_id"],
        "repo_name": repo_name,
        "github_url": clone_url,
        "local_path": str(local_path),
        "branch": "main",
        "language": "Unknown",
        "status": "indexing",
        "indexed_at": datetime.utcnow(),
    }
    repo_result = repositories.insert_one(repo_data)
    repository_id = repo_result.inserted_id

    try:
        vector_result = save_repo_vectors(
            repo_path=str(local_path),
            user_id=str(current_user["_id"]),
            repository_id=str(repository_id),
        )
        repositories.update_one(
            {"_id": repository_id},
            {"$set": {"status": "indexed", "indexed_at": datetime.utcnow()}},
        )
    except Exception as exc:
        repositories.update_one(
            {"_id": repository_id},
            {"$set": {"status": "failed", "indexed_at": datetime.utcnow()}},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to index repository",
        ) from exc

    return {
        "message": "Repository indexed successfully",
        "repository_id": str(repository_id),
        "repo_name": repo_name,
        "github_url": clone_url,
        "local_path": str(local_path),
        "vectors_inserted": vector_result["inserted_count"],
    }


