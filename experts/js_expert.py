from experts.base_expert import analyze_with_persona
from shared_state import AgentState


def js_expert(state: AgentState):
    instructions = (
        "Focus on Async/Await best practices, Promise hell, "
        "Type Coercion (== vs ===), and ES6+ syntax (arrow functions, destructuring). "
        "Check for potential closure memory leaks."
    )
    return analyze_with_persona(state, "JavaScript", instructions)
