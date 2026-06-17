import json
import redis
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import END  # Added exact LangGraph termination reference

from backend.config import settings
from backend.agents.state import AgentState
from backend.mcp_server import write_code, read_file, run_unit_tests

_redis = redis.Redis.from_url(settings.redis_url, decode_responses=True)
MAX_ITERATIONS = 3


def _llm() -> ChatOpenAI:
    # Double-check base_url formatting to protect against missing trailing components
    base_url = settings.OPENAI_BASE_URL
    if base_url and "gptgod" in base_url and not base_url.endswith("/v1"):
        base_url = base_url.rstrip("/") + "/v1"

    return ChatOpenAI(
        model=settings.LLM_MODEL,
        api_key=settings.OPENAI_API_KEY,
        base_url=base_url,
        temperature=0.1,
    )


def _log(state: AgentState, agent: str, message: str):
    entry = {"agent": agent, "message": message}
    state.setdefault("logs", []).append(f"[{agent}] {message}")
    # Stream to Redis list the frontend polls (short-term memory + live feed)
    _redis.rpush(f"job:{state['job_id']}:logs", json.dumps(entry))
    _redis.expire(f"job:{state['job_id']}:logs", 3600)


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = lines[1:]  # drop opening fence
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return text


# ---- Nodes --------------------------------------------------------------

def product_manager(state: AgentState) -> AgentState:
    _log(state, "ProductManager", "Breaking request into a technical spec...")
    resp = _llm().invoke([
        SystemMessage(content=(
            "You are a Product Manager. Convert the feature request into a concise, "
            "implementable technical specification for a single Python/FastAPI module. "
            "List endpoints, functions, inputs/outputs, and edge cases. Keep it under 250 words."
        )),
        HumanMessage(content=state["prompt"]),
    ])
    state["spec"] = resp.content
    _log(state, "ProductManager", "Spec ready.")
    return state


def developer(state: AgentState) -> AgentState:
    iteration = state.get("iterations", 0)
    _log(state, "Developer", f"Writing code (iteration {iteration + 1})...")
    feedback = ""
    if state.get("test_output") and not state.get("tests_passed", False):
        feedback = (
            "\n\nThe previous version FAILED these tests. Fix the bug:\n"
            + state["test_output"]
        )
    resp = _llm().invoke([
        SystemMessage(content=(
            "You are a Senior Python Developer. Implement the spec in a single file "
            "named main.py. Return ONLY the Python code, no explanation, no markdown fences."
        )),
        HumanMessage(content=f"SPEC:\n{state['spec']}{feedback}"),
    ])
    code = _strip_code_fence(resp.content)
    state["code"] = code
    write_code(state["job_id"], "main.py", code)
    _log(state, "Developer", "Wrote main.py via MCP write_code tool.")
    return state


def qa_engineer(state: AgentState) -> AgentState:
    _log(state, "QAEngineer", "Writing pytest unit tests...")
    current_code = read_file(state["job_id"], "main.py")
    resp = _llm().invoke([
        SystemMessage(content=(
            "You are a QA Engineer. Write pytest unit tests for the given module in a "
            "file named test_main.py. Import from `main`. Return ONLY Python code, no fences."
        )),
        HumanMessage(content=f"SPEC:\n{state['spec']}\n\nCODE:\n{current_code}"),
    ])
    test_code = _strip_code_fence(resp.content)
    state["test_code"] = test_code
    write_code(state["job_id"], "test_main.py", test_code)
    _log(state, "QAEngineer", "Running tests via MCP run_unit_tests tool...")

    result = run_unit_tests(state["job_id"], "test_main.py")
    state["test_output"] = result["output"]
    state["tests_passed"] = result["passed"]
    state["iterations"] = state.get("iterations", 0) + 1

    if result["passed"]:
        _log(state, "QAEngineer", "All tests PASSED.")
    else:
        _log(state, "QAEngineer", f"Tests FAILED:\n{result['output'][:500]}")
    return state


def route_after_qa(state: AgentState) -> str:
    if state.get("tests_passed"):
        return "end"  # Maps directly to the defined end handle string literal
    if state.get("iterations", 0) >= MAX_ITERATIONS:
        _log(state, "QAEngineer", "Max iterations reached. Returning best effort.")
        return "end"
    _log(state, "QAEngineer", "Looping back to Developer for a fix.")
    return "developer"