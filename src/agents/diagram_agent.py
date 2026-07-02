import os
import sys
from pathlib import Path
from typing import Literal

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


class DiagramResponse(BaseModel):
    diagram_type: Literal["flowchart", "sequence", "class", "architecture"] = Field(
        description="Best diagram type for the answer"
    )
    explanation: str = Field(description="Short explanation of what the diagram shows")
    mermaid: str = Field(description="Mermaid diagram code")
    sources: list[str] = Field(default_factory=list, description="Relevant file paths if available")


DIAGRAM_SYSTEM_PROMPT = """
You are a diagram agent for an AI repo analyzer.
Create clear Mermaid diagrams from the provided repository context.
Prefer flowchart for code flow, sequence for request lifecycle, class for object structure, and architecture for module overview.
Use only the provided context. If context is missing, say what is missing.
Return only the structured output.
"""


def build_diagram_context(chunks: list[dict]) -> str:
    if not chunks:
        return "No relevant code context found in the repository."

    return "\n\n".join(
        f"File: {c['metadata'].get('path')}\n{c['content']}"
        for c in chunks
    )


def create_diagram_agent():
    model = init_chat_model(
        "google_genai:gemini-2.5-flash",
        temperature=0,
    )
    return create_agent(
        model=model,
        tools=[],
        system_prompt=DIAGRAM_SYSTEM_PROMPT,
        response_format=DiagramResponse,
    )


_diagram_agent = None

def get_diagram_agent():
    global _diagram_agent
    if _diagram_agent is None:
        _diagram_agent = create_diagram_agent()
    return _diagram_agent


def create_diagram(question: str, repository_id: str) -> DiagramResponse:
    chunks = retrieve_chunks(query=question, repository_id=repository_id, top_k=8)
    context = build_diagram_context(chunks)

    agent = get_diagram_agent()
    response = agent.invoke({
        "messages": [
            {"role": "user", "content": f"Question: {question}\n\nContext:\n{context}"}
        ]
    })
    return response["structured_response"]


if __name__ == "__main__":
    question = input("Enter your question: ")
    repository_id = input("Enter repository ID: ")
    result = create_diagram(question, repository_id)
    print(result.model_dump())