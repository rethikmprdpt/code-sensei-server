from experts.base_expert import analyze_with_persona
from shared_state import AgentState


def python_expert(state: AgentState):
    instructions = (
        "Focus on PEP8 standards, list comprehensions vs loops, "
        "proper use of generators, and Pythonic idioms (The Zen of Python). "
        "Check for inefficient pandas/numpy usage if applicable."
    )
    return analyze_with_persona(state, "Python", instructions)
