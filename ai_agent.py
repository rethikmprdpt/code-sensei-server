from typing import Literal

from langgraph.graph import END, StateGraph

# Import Experts from the library
from experts import (
    cpp_expert,
    csharp_expert,
    generic_expert,
    java_expert,
    js_expert,
    python_expert,
)
from linter_engine import run_python_linter
from shared_state import AgentState


# --- 1. GUARDRAIL NODE ---
def guardrail_node(state: AgentState):
    """Simple check before routing to expensive experts."""
    code = state["code"]
    if not code or len(code.strip()) < 5:  # noqa: PLR2004
        return {"error": "Input is too short or empty."}
    return {"error": None}


def linter_node(state: AgentState):
    code = state["code"]
    lang = state["language"].lower()

    errors = []
    if lang == "python":
        errors = run_python_linter(code)

    # We can add C++/Java linters here later

    return {"linter_errors": errors}


# --- 2. ROUTER LOGIC ---
def route_language(  # noqa: PLR0911
    state: AgentState,
) -> Literal[
    "python_expert",
    "cpp_expert",
    "js_expert",
    "java_expert",
    "csharp_expert",
    "generic_expert",
    "end",
]:
    if state.get("error"):
        return "end"

    lang = state["language"].lower()

    # Mapping
    if lang == "python":
        return "python_expert"
    if lang in ["cpp", "c++", "c"]:
        return "cpp_expert"
    if lang in ["javascript", "js", "typescript", "ts"]:
        return "js_expert"
    if lang == "java":
        return "java_expert"
    if lang in ["c#", "csharp"]:
        return "csharp_expert"

    return "generic_expert"


# --- 3. BUILD GRAPH ---
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("guardrail", guardrail_node)
workflow.add_node("linter", linter_node)
workflow.add_node("python_expert", python_expert)
workflow.add_node("cpp_expert", cpp_expert)
workflow.add_node("js_expert", js_expert)
workflow.add_node("java_expert", java_expert)
workflow.add_node("csharp_expert", csharp_expert)
workflow.add_node("generic_expert", generic_expert)

# Set Entry
workflow.set_entry_point("guardrail")
workflow.add_edge("guardrail", "linter")

# Add Edges
workflow.add_conditional_edges(
    "linter",
    route_language,
    {
        "python_expert": "python_expert",
        "cpp_expert": "cpp_expert",
        "js_expert": "js_expert",
        "java_expert": "java_expert",
        "csharp_expert": "csharp_expert",
        "generic_expert": "generic_expert",
        "end": END,  # <--- Critical: Maps string "end" to the END constant
    },
)

# All experts exit to END
for node in [
    "python_expert",
    "cpp_expert",
    "js_expert",
    "java_expert",
    "csharp_expert",
    "generic_expert",
]:
    workflow.add_edge(node, END)

graph = workflow.compile()


# --- ENTRY POINT ---
def run_agent(code: str, language: str, function_name: str) -> dict:
    initial_state = {
        "code": code,
        "language": language,
        "function_name": function_name,
        "analysis": None,
        "error": None,
        "linter_errors": None,
    }

    result = graph.invoke(initial_state)  # type: ignore #noqa:PGH003

    if result.get("error"):
        raise ValueError(result["error"])

    return result["analysis"]
