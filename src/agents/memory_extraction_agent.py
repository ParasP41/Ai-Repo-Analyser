import os
import sys
from datetime import datetime
from pathlib import Path

from bson import ObjectId
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from config import GOOGLE_API_KEY
from src.database.index import db
from src.models.chat_model import chats

if GOOGLE_API_KEY:
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY


user_memory = db["user_memory"]


class UserMemoryFacts(BaseModel):
    skill_level: str | None = Field(default=None, description="User skill level if clear")
    preferences: list[str] = Field(default_factory=list, description="Durable user preferences")
    tech_stack: list[str] = Field(default_factory=list, description="Technologies the user uses or prefers")
    facts: list[str] = Field(default_factory=list, description="Other durable facts about the user")


MEMORY_SYSTEM_PROMPT = """
You are a long-term memory extraction agent.
Extract only durable facts about the user from recent chat messages.
Keep facts about skill level, coding preferences, preferred stack, tools, and recurring project goals.
Do not store temporary requests, secrets, passwords, API keys, or one-off task details.
Return only the structured output.
"""


def get_message_text(message: dict) -> str:
    value = message.get("message", message.get("content", ""))
    return str(value)


def get_recent_messages(user_id: str, repository_id: str, limit: int = 15) -> list[dict]:
    if not ObjectId.is_valid(user_id) or not ObjectId.is_valid(repository_id):
        return []

    messages = list(
        chats.find({
            "user_id": ObjectId(user_id),
            "repository_id": ObjectId(repository_id),
        })
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


def merge_unique(existing: list[str], incoming: list[str]) -> list[str]:
    values = []
    seen = set()
    for item in [*existing, *incoming]:
        clean = str(item).strip()
        key = clean.lower()
        if clean and key not in seen:
            values.append(clean)
            seen.add(key)
    return values


def create_memory_extraction_agent():
    model = init_chat_model(
        "google_genai:gemini-2.5-flash",
        temperature=0,
    )
    return create_agent(
        model=model,
        tools=[],
        system_prompt=MEMORY_SYSTEM_PROMPT,
        response_format=UserMemoryFacts,
    )


_memory_extraction_agent = None


def get_memory_extraction_agent():
    global _memory_extraction_agent
    if _memory_extraction_agent is None:
        _memory_extraction_agent = create_memory_extraction_agent()
    return _memory_extraction_agent


def get_user_memory(user_id: str) -> dict:
    if not ObjectId.is_valid(user_id):
        return {}
    memory = user_memory.find_one({"user_id": ObjectId(user_id)})
    return memory or {}


def get_user_memory_context(user_id: str) -> str:
    memory = get_user_memory(user_id)
    if not memory:
        return ""

    lines = []
    if memory.get("skill_level"):
        lines.append(f"Skill level: {memory['skill_level']}")
    if memory.get("preferences"):
        lines.append("Preferences: " + "; ".join(memory["preferences"]))
    if memory.get("tech_stack"):
        lines.append("Tech stack: " + "; ".join(memory["tech_stack"]))
    if memory.get("facts"):
        lines.append("Facts: " + "; ".join(memory["facts"]))
    return "\n".join(lines)


def upsert_user_memory(user_id: str, facts: UserMemoryFacts):
    if not ObjectId.is_valid(user_id):
        return

    user_object_id = ObjectId(user_id)
    existing = user_memory.find_one({"user_id": user_object_id}) or {}

    update_data = {
        "preferences": merge_unique(existing.get("preferences", []), facts.preferences),
        "tech_stack": merge_unique(existing.get("tech_stack", []), facts.tech_stack),
        "facts": merge_unique(existing.get("facts", []), facts.facts),
        "updated_at": datetime.utcnow(),
    }

    if facts.skill_level:
        update_data["skill_level"] = facts.skill_level
    elif existing.get("skill_level"):
        update_data["skill_level"] = existing["skill_level"]

    user_memory.update_one(
        {"user_id": user_object_id},
        {
            "$set": update_data,
            "$setOnInsert": {"user_id": user_object_id, "created_at": datetime.utcnow()},
        },
        upsert=True,
    )


def extract_and_store_user_memory(user_id: str, repository_id: str):
    messages = get_recent_messages(user_id, repository_id)
    if len(messages) < 3:
        return

    agent = get_memory_extraction_agent()
    response = agent.invoke({
        "messages": [
            {"role": "user", "content": format_messages(messages)}
        ]
    })
    upsert_user_memory(user_id, response["structured_response"])
