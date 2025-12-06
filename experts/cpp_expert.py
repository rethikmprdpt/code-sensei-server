from experts.base_expert import analyze_with_persona
from shared_state import AgentState


def cpp_expert(state: AgentState):
    instructions = (
        "Focus on Memory Management (RAII), manual new/delete leaks, "
        "buffer overflows, pointer safety, and pass-by-value vs pass-by-reference. "
        "Check for Modern C++ (C++11/14/17/20) best practices."
    )
    return analyze_with_persona(state, "C++", instructions)
