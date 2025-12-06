from experts.base_expert import analyze_with_persona
from shared_state import AgentState


def java_expert(state: AgentState):
    instructions = (
        "Focus on NullPointerExceptions, correct OOP patterns, "
        "verbosity reduction (Streams API), and thread safety. "
        "Check for inefficient String concatenation (StringBuilder)."
    )
    return analyze_with_persona(state, "Java", instructions)
