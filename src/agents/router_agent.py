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

from config import GROQ_API_KEY

if GROQ_API_KEY:
    os.environ["GROQ_API_KEY"] = GROQ_API_KEY


AgentName = Literal[
    "summary_agent",
    "code_agent",
    "diagram_agent",
    "docs_agent",
    "security_agent",
    "refactor_agent",
    "dependency_agent",
    "test_agent",
]


class RouterDecision(BaseModel):
    agent: AgentName = Field(description="Best agent to answer the user question")
    reason: str = Field(description="Short reason for choosing this agent")


ROUTER_SYSTEM_PROMPT = """
You are a router for an AI repo analyzer.
Choose exactly one specialist agent for the user question.

Agent choices:
- summary_agent: repo overview, architecture, high-level explanation
- code_agent: code flow, functions, files, implementation details
- diagram_agent: diagrams, flowcharts, visual explanations
- docs_agent: README, docs, API docs, usage guide
- security_agent: vulnerabilities, auth, secrets, unsafe code
- refactor_agent: cleanup, improvements, better structure
- dependency_agent: packages, imports, dependency issues
- test_agent: tests, test cases, coverage

Return only the structured output.
"""


def create_router_agent():
    model = init_chat_model(
        "groq:llama-3.1-8b-instant",
        temperature=0,
    )
    return create_agent(
        model=model,
        tools=[],
        system_prompt=ROUTER_SYSTEM_PROMPT,
        response_format=RouterDecision,
    )


_router_agent = None

def get_router_agent():
    global _router_agent
    if _router_agent is None:
        _router_agent = create_router_agent()
    return _router_agent


def route_question(question: str) -> RouterDecision:
    agent = get_router_agent()
    response = agent.invoke({
        "messages": [
            {"role": "user", "content": question}
        ]
    })
    return response["structured_response"]


if __name__ == "__main__":
    question = input("Enter your question: ")
    decision = route_question(question)
    print(decision.model_dump())