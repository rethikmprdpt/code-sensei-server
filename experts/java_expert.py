from experts.base_expert import analyze_with_persona
from shared_state import AgentState


def java_expert(state: AgentState):
    # instructions = (
    #     "Focus on NullPointerExceptions, correct OOP patterns, "
    #     "verbosity reduction (Streams API), and thread safety. "
    #     "Check for inefficient String concatenation (StringBuilder)."
    # )
    instructions = (
        "Primary Focus: Null safety (defensive coding, Optional<T>), SOLID principles, "
        "and proper resource management (try-with-resources). "
        "Code Style: Reduce verbosity using the Streams API (where readable) and modernize "
        "legacy patterns. "
        "Performance & Safety: Ensure thread safety (immutability, Concurrent collections) "
        "and optimize String operations (StringBuilder inside loops). "
        "Holistic Review: Do not limit analysis to the above; proactively identify any logic "
        "errors, swallowed exceptions, time-complexity issues (Big O), or security risks "
        "that compromise code quality."
    )
    return analyze_with_persona(state, "Java", instructions)
