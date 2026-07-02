import os
import sys
from pathlib import Path

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from config import GOOGLE_API_KEY
from src.rag.retriever import retrieve_chunks

if GOOGLE_API_KEY:
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY


class DocsResponse(BaseModel):
    answer: str = Field(description="Documentation-style answer")
    sections: list[str] = Field(default_factory=list, description="Suggested documentation sections")
    sources: list[str] = Field(default_factory=list, description="Relevant file paths if available")


DOCS_SYSTEM_PROMPT = """
You are a documentation agent for an AI repo analyzer.
Write clear documentation, README content, setup instructions, API notes, and usage explanations.
Use only the provided repository context. If context is missing, say what is missing.
Return only the structured output.
"""


def build_docs_context(chunks: list[dict]) -> str:
    if not chunks:
        return "No relevant code context found in the repository."

    return "\n\n".join(
        f"File: {c['metadata'].get('path')}\n```{c['metadata'].get('language')}\n{c['content']}\n```"
        for c in chunks
    )


def create_docs_agent():
    model = init_chat_model(
        "google_genai:gemini-2.5-flash",
        temperature=0,
    )
    return create_agent(
        model=model,
        tools=[],
        system_prompt=DOCS_SYSTEM_PROMPT,
        response_format=DocsResponse,
    )


_docs_agent = None

def get_docs_agent():
    global _docs_agent
    if _docs_agent is None:
        _docs_agent = create_docs_agent()
    return _docs_agent


def answer_docs_question(question: str, repository_id: str) -> DocsResponse:
    chunks = retrieve_chunks(query=question, repository_id=repository_id, top_k=8)
    context = build_docs_context(chunks)

    agent = get_docs_agent()
    response = agent.invoke({
        "messages": [
            {"role": "user", "content": f"Question: {question}\n\nContext:\n{context}"}
        ]
    })
    return response["structured_response"]


if __name__ == "__main__":
    question = input("Enter your question: ")
    repository_id = input("Enter repository ID: ")
    result = answer_docs_question(question, repository_id)
    print(result.model_dump())