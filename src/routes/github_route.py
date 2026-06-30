from fastapi import APIRouter, Depends

from src.controller.github_controller import CloneRepoRequest, clone_repository
from src.middleware.auth_middleware import get_current_user

github_router = APIRouter()


@github_router.post("/clone")
def clone_repository_route(
    payload: CloneRepoRequest,
    current_user=Depends(get_current_user),
):
    return clone_repository(payload, current_user)
