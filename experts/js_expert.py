from experts.base_expert import analyze_with_persona
from shared_state import AgentState


def js_expert(state: AgentState):
    # instructions = (
    #     "Focus on Async/Await best practices, Promise hell, "
    #     "Type Coercion (== vs ===), and ES6+ syntax (arrow functions, destructuring). "
    #     "Check for potential closure memory leaks."
    # )
    instructions = (
        "Conduct a deep technical review focusing on modern JavaScript (ES2022+) standards. "
        "1. Asynchronous Logic: Detect 'waterfall' execution in Async/Await and suggest Promise.all where applicable. "
        "Check for unhandled promise rejections and missing try/catch blocks. "
        "2. Type Safety & Coercion: Enforce strict equality (===) and flag implicit coercion risks. "
        "3. Modern Syntax: Encourage destructuring, arrow functions, and replace verbose null checks with Optional Chaining (?.) and Nullish Coalescing (??). "
        "4. Memory & State: Identify closure-related memory leaks (e.g., inside loops or event listeners) and warn against direct object/array mutation. "
        "5. holistic Review: Do not limit your analysis to the above points; proactively identify logical errors, "
        "inefficient array method usage (e.g., using map for side effects), or security vulnerabilities."
    )
    return analyze_with_persona(state, "JavaScript", instructions)
