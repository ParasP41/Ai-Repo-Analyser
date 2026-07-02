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


CODE_MODEL = "qwen/qwen3-coder-480b:free"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class CodeResponse(BaseModel):
    answer: str = Field(description="Clear answer about the code")
    files: list[str] = Field(default_factory=list, description="Relevant file paths")
    notes: list[str] = Field(default_factory=list, description="Important implementation notes")


CODE_SYSTEM_PROMPT = """
You are a code agent for an AI repo analyzer.
Answer questions about code behavior, functions, files, and implementation details.
Use only the provided repository context. If the context is not enough, say what is missing.
Mention relevant files and line ranges when available.
Return only the structured output.
"""


def build_code_context(chunks: list[dict]) -> str:
    if not chunks:
        return "No relevant code context found in the repository."

    return "\n\n".join(
        f"File: {c['metadata'].get('path')} "
        f"(lines {c['metadata'].get('start_line')}-{c['metadata'].get('end_line')})\n"
        f"```{c['metadata'].get('language')}\n{c['content']}\n```"
        for c in chunks
    )


def create_code_agent():
    model = ChatOpenAI(
        model=CODE_MODEL,
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
        temperature=0,
    )
    return create_agent(
        model=model,
        tools=[],
        system_prompt=CODE_SYSTEM_PROMPT,
        response_format=CodeResponse,
    )


_code_agent = None

def get_code_agent():
    global _code_agent
    if _code_agent is None:
        _code_agent = create_code_agent()
    return _code_agent


def answer_code_question(question: str, repository_id: str) -> CodeResponse:
    chunks = retrieve_chunks(query=question, repository_id=repository_id, top_k=6)
    context = build_code_context(chunks)

    agent = get_code_agent()
    response = agent.invoke({
        "messages": [
            {"role": "user", "content": f"Question: {question}\n\nContext:\n{context}"}
        ]
    })
    return response["structured_response"]


if __name__ == "__main__":
    question = input("Enter your question: ")
    repository_id = input("Enter repository ID: ")
    result = answer_code_question(question, repository_id)
    print(result.model_dump())