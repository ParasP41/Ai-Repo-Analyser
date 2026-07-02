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


TEST_MODEL = "deepseek/deepseek-r1:free"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class TestCase(BaseModel):
    name: str = Field(description="Test case name")
    test_type: Literal["unit", "integration", "e2e", "manual"] = Field(description="Type of test")
    target: str = Field(description="Function, route, file, or behavior to test")
    description: str = Field(description="What the test should verify")


class TestResponse(BaseModel):
    answer: str = Field(description="Testing guidance summary")
    test_cases: list[TestCase] = Field(default_factory=list, description="Suggested test cases")
    missing_coverage: list[str] = Field(default_factory=list, description="Important gaps in test coverage")
    sources: list[str] = Field(default_factory=list, description="Relevant file paths if available")


TEST_SYSTEM_PROMPT = """
You are a test agent for an AI repo analyzer.
Suggest practical unit, integration, e2e, or manual tests for the provided repository context.
Focus on important behavior, edge cases, regressions, and missing coverage.
Use only the provided context. If context is missing, say what is missing.
Return only the structured output.
"""


def build_test_context(chunks: list[dict]) -> str:
    if not chunks:
        return "No relevant code context found in the repository."

    return "\n\n".join(
        f"File: {c['metadata'].get('path')}\n```{c['metadata'].get('language')}\n{c['content']}\n```"
        for c in chunks
    )


def create_test_agent():
    model = ChatOpenAI(
        model=TEST_MODEL,
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
        temperature=0,
    )
    return create_agent(
        model=model,
        tools=[],
        system_prompt=TEST_SYSTEM_PROMPT,
        response_format=TestResponse,
    )


_test_agent = None

def get_test_agent():
    global _test_agent
    if _test_agent is None:
        _test_agent = create_test_agent()
    return _test_agent


def answer_test_question(question: str, repository_id: str) -> TestResponse:
    chunks = retrieve_chunks(query=question, repository_id=repository_id, top_k=6)
    context = build_test_context(chunks)

    agent = get_test_agent()
    response = agent.invoke({
        "messages": [
            {"role": "user", "content": f"Question: {question}\n\nContext:\n{context}"}
        ]
    })
    return response["structured_response"]


if __name__ == "__main__":
    question = input("Enter your question: ")
    repository_id = input("Enter repository ID: ")
    result = answer_test_question(question, repository_id)
    print(result.model_dump())