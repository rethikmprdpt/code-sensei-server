from typing import TypedDict


class AgentState(TypedDict):
    """The state object that gets passed around the LangGraph."""

    code: str
    language: str
    function_name: str
    analysis: dict | None  # The Pydantic output
    error: str | None
    linter_errors: list[str] | None
