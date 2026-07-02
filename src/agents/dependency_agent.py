import os
import re
import sys
from pathlib import Path

import requests
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from config import GROQ_API_KEY

if GROQ_API_KEY:
    os.environ["GROQ_API_KEY"] = GROQ_API_KEY


class DependencyResponse(BaseModel):
    answer: str = Field(description="Clear answer about dependencies or imports")
    dependencies: list[str] = Field(default_factory=list, description="Relevant packages or libraries")
    issues: list[str] = Field(default_factory=list, description="Dependency problems or risks if any")
    sources: list[str] = Field(default_factory=list, description="Relevant file paths if available")


DEPENDENCY_SYSTEM_PROMPT = """
You are a dependency agent for an AI repo analyzer.
Answer questions about packages, imports, versions, dependency conflicts, and setup files.
Use only the provided repository context, which includes real current version and 
vulnerability data — do not rely on your own knowledge of package versions or CVEs, 
since that may be outdated. If context is missing, say what is missing.
Return only the structured output.
"""


def parse_requirements(file_content: str, file_type: str) -> list[dict]:
    packages = []
    if file_type == "requirements.txt":
        for line in file_content.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                match = re.match(r"([a-zA-Z0-9_\-]+)\s*[=><~!]*\s*([\d\.]*)", line)
                if match:
                    packages.append({"name": match.group(1), "version": match.group(2) or None})
    elif file_type == "pyproject.toml":
        for line in file_content.splitlines():
            match = re.match(r'\s*"([a-zA-Z0-9_\-]+)\s*[>=<~!]*\s*([\d\.]*)"', line)
            if match:
                packages.append({"name": match.group(1), "version": match.group(2) or None})
    return packages


def check_latest_version(package_name: str) -> str | None:
    try:
        resp = requests.get(f"https://pypi.org/pypi/{package_name}/json", timeout=5)
        resp.raise_for_status()
        return resp.json()["info"]["version"]
    except requests.RequestException:
        return None


def check_vulnerabilities(package_name: str, version: str | None) -> list[str]:
    payload = {"package": {"name": package_name, "ecosystem": "PyPI"}}
    if version:
        payload["version"] = version
    try:
        resp = requests.post("https://api.osv.dev/v1/query", json=payload, timeout=5)
        resp.raise_for_status()
        return [v.get("id") for v in resp.json().get("vulns", [])]
    except requests.RequestException:
        return []


def build_dependency_context(repo_path: str) -> str:
    req_file = Path(repo_path) / "requirements.txt"
    pyproject_file = Path(repo_path) / "pyproject.toml"

    if req_file.exists():
        content, file_type = req_file.read_text(errors="ignore"), "requirements.txt"
    elif pyproject_file.exists():
        content, file_type = pyproject_file.read_text(errors="ignore"), "pyproject.toml"
    else:
        return "No requirements.txt or pyproject.toml found in this repository."

    packages = parse_requirements(content, file_type)

    lines = []
    for pkg in packages:
        latest = check_latest_version(pkg["name"])
        vulns = check_vulnerabilities(pkg["name"], pkg["version"])
        lines.append(
            f"- {pkg['name']}: current={pkg['version'] or 'unspecified'}, "
            f"latest={latest or 'unknown'}, "
            f"known_vulnerabilities={vulns or 'none'}"
        )

    return f"Dependency file: {file_type}\n\n" + "\n".join(lines)


def create_dependency_agent():
    model = init_chat_model(
        "groq:llama-3.3-70b-versatile",
        temperature=0,
    )
    return create_agent(
        model=model,
        tools=[],
        system_prompt=DEPENDENCY_SYSTEM_PROMPT,
        response_format=DependencyResponse,
    )


_dependency_agent = None

def get_dependency_agent():
    global _dependency_agent
    if _dependency_agent is None:
        _dependency_agent = create_dependency_agent()
    return _dependency_agent


def answer_dependency_question(question: str, repo_path: str) -> DependencyResponse:
    context = build_dependency_context(repo_path)

    agent = get_dependency_agent()
    response = agent.invoke({
        "messages": [
            {"role": "user", "content": f"Question: {question}\n\nContext:\n{context}"}
        ]
    })
    return response["structured_response"]


if __name__ == "__main__":
    question = input("Enter your question: ")
    repo_path = input("Enter repo path: ")
    result = answer_dependency_question(question, repo_path)
    print(result.model_dump())