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


class SummaryResponse(BaseModel):
    summary: str = Field(description="Short summary of the repository or selected context")
    key_points: list[str] = Field(description="Important points the user should know")
    sources: list[str] = Field(default_factory=list, description="Relevant file paths if available")


SUMMARY_SYSTEM_PROMPT = """
You are a summary agent for an AI repo analyzer.
Explain the repository or selected code context clearly and briefly.
Focus on architecture, purpose, main modules, and important files.
Use the provided context only. If context is missing, say what is missing.
Return only the structured output.
"""


def build_repo_context(repo_path: str, question: str, repository_id: str) -> str:
    readme_path = Path(repo_path) / "README.md"
    readme_content = readme_path.read_text(errors="ignore") if readme_path.exists() else "No README found."

    structure = "\n".join(sorted(
        str(p.relative_to(repo_path)) for p in Path(repo_path).rglob("*") if p.is_file()
    )[:200])  # cap for very large repos

    top_chunks = retrieve_chunks(query=question, repository_id=repository_id, top_k=10)
    chunk_snippets = "\n\n".join(
        f"File: {c['metadata'].get('path')}\n{c['content'][:500]}"
        for c in top_chunks
    )

    return f"""README:
{readme_content}

FOLDER STRUCTURE:
{structure}

KEY FILE SNIPPETS:
{chunk_snippets}
"""


def create_summary_agent():
    model = init_chat_model(
        "google_genai:gemini-2.5-flash",
        temperature=0,
    )
    return create_agent(
        model=model,
        tools=[],
        system_prompt=SUMMARY_SYSTEM_PROMPT,
        response_format=SummaryResponse,
    )


_summary_agent = None

def get_summary_agent():
    global _summary_agent
    if _summary_agent is None:
        _summary_agent = create_summary_agent()
    return _summary_agent


def summarize_repo(question: str, repo_path: str, repository_id: str) -> SummaryResponse:
    context = build_repo_context(repo_path, question, repository_id)

    agent = get_summary_agent()
    response = agent.invoke({
        "messages": [
            {"role": "user", "content": f"Question: {question}\n\nContext:\n{context}"}
        ]
    })
    return response["structured_response"]


if __name__ == "__main__":
    question = input("Enter your question: ")
    repo_path = input("Enter repo path: ")
    repository_id = input("Enter repository ID: ")
    result = summarize_repo(question, repo_path, repository_id)
    print(result.model_dump())