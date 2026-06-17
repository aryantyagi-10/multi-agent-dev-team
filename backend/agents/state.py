from typing import TypedDict


class AgentState(TypedDict, total=False):
    job_id: str
    prompt: str
    spec: str
    code: str
    test_code: str
    test_output: str
    tests_passed: bool
    iterations: int
    logs: list[str]  # streamed to Redis for the frontend
