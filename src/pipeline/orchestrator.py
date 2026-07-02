from src.agents.chat_summary_agent import get_chat_summary
from src.agents.memory_extraction_agent import get_user_memory_context
from src.agents.router_agent import route_question
from src.agents.summary_agent import summarize_repo
from src.agents.code_agent import answer_code_question
from src.agents.diagram_agent import create_diagram
from src.agents.docs_agent import answer_docs_question
from src.agents.security_agent import answer_security_question
from src.agents.refactor_agent import answer_refactor_question
from src.agents.dependency_agent import answer_dependency_question
from src.agents.test_agent import answer_test_question


def build_memory_context(repository_id: str, user_id: str | None = None) -> str:
    parts = []

    chat_summary = get_chat_summary(repository_id)
    if chat_summary:
        parts.append(f"Recent chat summary:\n{chat_summary}")

    if user_id:
        user_memory = get_user_memory_context(user_id)
        if user_memory:
            parts.append(f"Long-term user memory:\n{user_memory}")

    return "\n\n".join(parts)


def build_agent_question(question: str, memory_context: str) -> str:
    if not memory_context:
        return question

    return f"""Memory context:
{memory_context}

Current user question:
{question}"""


def handle_user_question(
    question: str,
    repo_path: str,
    repository_id: str,
    user_id: str | None = None,
) -> dict:
    memory_context = build_memory_context(repository_id, user_id)
    agent_question = build_agent_question(question, memory_context)

    try:
        decision = route_question(agent_question)
    except Exception as e:
        return {
            "agent": None,
            "success": False,
            "error": f"Routing failed: {e}",
            "data": None,
        }

    agent_name = decision.agent

    try:
        if agent_name == "summary_agent":
            result = summarize_repo(agent_question, repo_path, repository_id)

        elif agent_name == "code_agent":
            result = answer_code_question(agent_question, repository_id)

        elif agent_name == "diagram_agent":
            result = create_diagram(agent_question, repository_id)

        elif agent_name == "docs_agent":
            result = answer_docs_question(agent_question, repository_id)

        elif agent_name == "security_agent":
            result = answer_security_question(agent_question, repository_id)

        elif agent_name == "refactor_agent":
            result = answer_refactor_question(agent_question, repository_id)

        elif agent_name == "dependency_agent":
            result = answer_dependency_question(agent_question, repo_path)

        elif agent_name == "test_agent":
            result = answer_test_question(agent_question, repository_id)

        else:
            return {
                "agent": agent_name,
                "success": False,
                "error": f"Unknown agent: {agent_name}",
                "data": None,
            }

        return {
            "agent": agent_name,
            "reason": decision.reason,
            "success": True,
            "error": None,
            "memory_used": bool(memory_context),
            "data": result.model_dump(),
        }

    except Exception as e:
        return {
            "agent": agent_name,
            "reason": decision.reason,
            "success": False,
            "error": f"{agent_name} failed: {e}",
            "data": None,
        }


if __name__ == "__main__":
    question = input("Enter your question: ")
    repo_path = input("Enter repo path: ")
    repository_id = input("Enter repository ID: ")
    user_id = input("Enter user ID: ")

    result = handle_user_question(question, repo_path, repository_id, user_id)
    print(result)

