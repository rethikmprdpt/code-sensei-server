from experts.base_expert import analyze_with_persona
from shared_state import AgentState


def generic_expert(state: AgentState):
    instructions = (
        "Focus on fundamental logical correctness, algorithmic complexity (Big O), "
        "and clean code principles (SOLID, DRY). "
        "Assume a general syntax but prioritize logic flaws."
    )
    return analyze_with_persona(state, "General Code", instructions)
