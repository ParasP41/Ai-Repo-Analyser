from fastapi import APIRouter, BackgroundTasks, Depends

from src.controller.chat_controller import AskQuestionRequest, ask_question
from src.middleware.auth_middleware import get_current_user


chat_router = APIRouter()


@chat_router.post("/ask")
def ask_question_route(
    payload: AskQuestionRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
):
    return ask_question(payload, current_user, background_tasks)
