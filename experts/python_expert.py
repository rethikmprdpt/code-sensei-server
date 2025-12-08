from experts.base_expert import analyze_with_persona
from shared_state import AgentState


def python_expert(state: AgentState):
    # instructions = (
    #     "Focus on PEP8 standards, list comprehensions vs loops, "
    #     "proper use of generators, and Pythonic idioms (The Zen of Python). "
    #     "Check for inefficient pandas/numpy usage if applicable."
    # )
    instructions = (
        "Conduct a deep technical review focusing on modern Python (3.10+) standards and idiomatic best practices. "
        "1. Pythonic Idioms: Enforce the 'Zen of Python'. Prioritize list comprehensions over loops (where readable), "
        "require Context Managers ('with') for file/resource handling, and insist on f-strings over '%' or .format(). "
        "2. Performance & Memory: Detect inefficient use of lists for membership testing (suggest Sets). "
        "Identify where Generators/Iterators ('yield') should replace lists to save memory. "
        "3. Junior Pitfalls: Strictly flag 'Mutable Default Arguments', bare 'except:' clauses, and misuse of 'is' vs '=='. "
        "Encourage 'Easier to Ask Forgiveness' (try/except) patterns over 'Look Before You Leap' where appropriate. "
        "4. Libraries (Pandas/NumPy): If data libraries are used, aggressively flag iteration over rows. "
        "Mandate vectorization and native numpy/pandas methods for performance. "
        "5. Holistic Logic Review: Do not limit analysis to syntax; proactively look for logical errors (e.g., off-by-one errors, scope issues), "
        "race conditions, lack of Type Hints, or security vulnerabilities (e.g., SQL injection risks)."
        "If the code uses specific libraries (like subprocess, pandas, flake8), briefly explain how they are used and any arguments or flags used."
    )
    return analyze_with_persona(state, "Python", instructions)
