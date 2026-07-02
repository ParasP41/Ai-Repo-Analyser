import json
from datetime import datetime

from bson import ObjectId
from fastapi import BackgroundTasks, HTTPException, status
from pydantic import BaseModel, Field

from src.agents.memory_extraction_agent import extract_and_store_user_memory
from src.models.chat_model import chats
from src.models.repo_model import repositories
from src.pipeline.orchestrator import handle_user_question


class AskQuestionRequest(BaseModel):
    repository_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


def save_chat_message(user_id, repository_id, role: str, message: str):
    chats.insert_one({
        "user_id": user_id,
        "repository_id": repository_id,
        "role": role,
        "message": message,
        "timestamp": datetime.utcnow(),
    })


def ask_question(
    payload: AskQuestionRequest,
    current_user: dict,
    background_tasks: BackgroundTasks,
):
    if not ObjectId.is_valid(payload.repository_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid repository id",
        )

    user_id = current_user["_id"]
    repository_id = ObjectId(payload.repository_id)

    repo = repositories.find_one({
        "_id": repository_id,
        "user_id": user_id,
    })
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found",
        )

    save_chat_message(user_id, repository_id, "user", payload.message)

    result = handle_user_question(
        question=payload.message,
        repo_path=repo["local_path"],
        repository_id=payload.repository_id,
        user_id=str(user_id),
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=result.get("error", "Unable to answer question"),
        )

    save_chat_message(
        user_id,
        repository_id,
        "assistant",
        json.dumps(result.get("data"), default=str),
    )

    background_tasks.add_task(
        extract_and_store_user_memory,
        str(user_id),
        payload.repository_id,
    )

    return {
        "message": "Question answered successfully",
        "repository_id": payload.repository_id,
        "agent": result.get("agent"),
        "reason": result.get("reason"),
        "memory_used": result.get("memory_used", False),
        "answer": result.get("data"),
    }