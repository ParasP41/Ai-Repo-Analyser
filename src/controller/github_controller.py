import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse

from fastapi import HTTPException, status
from pydantic import BaseModel, Field


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


def clone_repository(payload: CloneRepoRequest, current_user: dict):
    owner, repo_name, clone_url = get_github_repo(payload.github_url)

    TEMP_REPO_DIR.mkdir(parents=True, exist_ok=True)
    local_path = TEMP_REPO_DIR / f"{owner}__{repo_name}"

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

    return {
        "message": "Repository cloned successfully",
        "repo_name": repo_name,
        "github_url": clone_url,
        "local_path": str(local_path),
        "user_id": str(current_user["_id"]),
    }
