import sys
from pathlib import Path
from typing import Literal

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from config import OPENROUTER_API_KEY
from src.rag.retriever import retrieve_chunks


SECURITY_MODEL = "deepseek/deepseek-r1:free"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class SecurityFinding(BaseModel):
    severity: Literal["low", "medium", "high", "critical"] = Field(description="Risk severity")
    issue: str = Field(description="Security issue")
    recommendation: str = Field(description="How to fix or reduce the risk")
    file: str | None = Field(default=None, description="Relevant file path if available")


class SecurityResponse(BaseModel):
    answer: str = Field(description="Security review summary")
    findings: list[SecurityFinding] = Field(default_factory=list, description="Security findings")
    sources: list[str] = Field(default_factory=list, description="Relevant file paths if available")


SECURITY_SYSTEM_PROMPT = """
You are a security agent for an AI repo analyzer.
Review authentication, authorization, secrets, input validation, dependency risks, unsafe file operations, and data exposure.
Use only the provided repository context. If context is missing, say what is missing.
Do not invent vulnerabilities. Be direct and practical.
Return only the structured output.
"""


def build_security_context(chunks: list[dict]) -> str:
    if not chunks:
        return "No relevant code context found in the repository."

    return "\n\n".join(
        f"File: {c['metadata'].get('path')}\n```{c['metadata'].get('language')}\n{c['content']}\n```"
        for c in chunks
    )


def create_security_agent():
    model = ChatOpenAI(
        model=SECURITY_MODEL,
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
        temperature=0,
    )
    return create_agent(
        model=model,
        tools=[],
        system_prompt=SECURITY_SYSTEM_PROMPT,
        response_format=SecurityResponse,
    )


_security_agent = None

def get_security_agent():
    global _security_agent
    if _security_agent is None:
        _security_agent = create_security_agent()
    return _security_agent


def answer_security_question(question: str, repository_id: str) -> SecurityResponse:
    chunks = retrieve_chunks(query=question, repository_id=repository_id, top_k=6)
    context = build_security_context(chunks)

    agent = get_security_agent()
    response = agent.invoke({
        "messages": [
            {"role": "user", "content": f"Question: {question}\n\nContext:\n{context}"}
        ]
    })
    return response["structured_response"]


if __name__ == "__main__":
    question = input("Enter your question: ")
    repository_id = input("Enter repository ID: ")
    result = answer_security_question(question, repository_id)
    print(result.model_dump())