from experts.base_expert import analyze_with_persona
from shared_state import AgentState


def csharp_expert(state: AgentState):
    instructions = (
        "Focus on LINQ usage, Async/Await patterns, "
        "Garbage Collection awareness, and proper IDisposable usage. "
        "Check for nullability/nullable reference types."
    )
    return analyze_with_persona(state, "C#", instructions)
