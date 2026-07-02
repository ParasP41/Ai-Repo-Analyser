import os
import sys
from pathlib import Path

from bson import ObjectId
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from config import GROQ_API_KEY
from src.models.chat_model import chats

if GROQ_API_KEY:
    os.environ["GROQ_API_KEY"] = GROQ_API_KEY


class ChatSummaryResponse(BaseModel):
    summary: str = Field(description="Short summary of the recent chat")
    key_points: list[str] = Field(default_factory=list, description="Important points from recent messages")


CHAT_SUMMARY_SYSTEM_PROMPT = """
You are a short-term memory agent for a repo chat.
Summarize the recent conversation briefly so the next agent can answer with context.
Keep user intent, unresolved questions, preferences, and important repo details.
Return only the structured output.
"""


def get_message_text(message: dict) -> str:
    value = message.get("message", message.get("content", ""))
    return str(value)


def get_recent_chat_messages(repository_id: str, limit: int = 15) -> list[dict]:
    if not ObjectId.is_valid(repository_id):
        return []

    messages = list(
        chats.find({"repository_id": ObjectId(repository_id)})
        .sort("timestamp", -1)
        .limit(limit)
    )
    messages.reverse()
    return messages


def format_messages(messages: list[dict]) -> str:
    return "\n".join(
        f"{message.get('role', 'user')}: {get_message_text(message)}"
        for message in messages
    )


def create_chat_summary_agent():
    model = init_chat_model(
        "groq:llama-3.1-8b-instant",
        temperature=0,
    )
    return create_agent(
        model=model,
        tools=[],
        system_prompt=CHAT_SUMMARY_SYSTEM_PROMPT,
        response_format=ChatSummaryResponse,
    )


_chat_summary_agent = None


def get_chat_summary_agent():
    global _chat_summary_agent
    if _chat_summary_agent is None:
        _chat_summary_agent = create_chat_summary_agent()
    return _chat_summary_agent


def get_chat_summary(repository_id: str, limit: int = 15) -> str:
    messages = get_recent_chat_messages(repository_id, limit)
    if len(messages) < 3:
        return ""

    agent = get_chat_summary_agent()
    response = agent.invoke({
        "messages": [
            {"role": "user", "content": format_messages(messages)}
        ]
    })
    result = response["structured_response"]

    parts = [result.summary]
    if result.key_points:
        parts.append("Key points: " + "; ".join(result.key_points))
    return "\n".join(parts)
