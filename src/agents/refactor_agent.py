import sys
from pathlib import Path

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from config import OPENROUTER_API_KEY
from src.rag.retriever import retrieve_chunks


REFACTOR_MODEL = "qwen/qwen3-coder-480b:free"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class RefactorResponse(BaseModel):
    answer: str = Field(description="Clear refactor guidance")
    recommendations: list[str] = Field(default_factory=list, description="Specific refactor suggestions")
    risks: list[str] = Field(default_factory=list, description="Possible risks or behavior changes")
    files: list[str] = Field(default_factory=list, description="Relevant file paths")


REFACTOR_SYSTEM_PROMPT = """
You are a refactor agent for an AI repo analyzer.
Suggest simple, practical code improvements, cleanup, naming fixes, structure improvements, and duplication removal.
Use only the provided repository context. If context is missing, say what is missing.
Avoid large rewrites unless the user asks for them.
Return only the structured output.
"""


def build_refactor_context(chunks: list[dict]) -> str:
    if not chunks:
        return "No relevant code context found in the repository."

    return "\n\n".join(
        f"File: {c['metadata'].get('path')} "
        f"(lines {c['metadata'].get('start_line')}-{c['metadata'].get('end_line')})\n"
        f"```{c['metadata'].get('language')}\n{c['content']}\n```"
        for c in chunks
    )


def create_refactor_agent():
    model = ChatOpenAI(
        model=REFACTOR_MODEL,
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
        temperature=0,
    )
    return create_agent(
        model=model,
        tools=[],
        system_prompt=REFACTOR_SYSTEM_PROMPT,
        response_format=RefactorResponse,
    )


_refactor_agent = None

def get_refactor_agent():
    global _refactor_agent
    if _refactor_agent is None:
        _refactor_agent = create_refactor_agent()
    return _refactor_agent


def answer_refactor_question(question: str, repository_id: str) -> RefactorResponse:
    chunks = retrieve_chunks(query=question, repository_id=repository_id, top_k=6)
    context = build_refactor_context(chunks)

    agent = get_refactor_agent()
    response = agent.invoke({
        "messages": [
            {"role": "user", "content": f"Question: {question}\n\nContext:\n{context}"}
        ]
    })
    return response["structured_response"]


if __name__ == "__main__":
    question = input("Enter your question: ")
    repository_id = input("Enter repository ID: ")
    result = answer_refactor_question(question, repository_id)
    print(result.model_dump())