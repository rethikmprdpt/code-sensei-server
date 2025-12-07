from experts.base_expert import analyze_with_persona
from shared_state import AgentState


def cpp_expert(state: AgentState):
    # instructions = (
    #     "Focus on Memory Management (RAII), manual new/delete leaks, "
    #     "buffer overflows, pointer safety, and pass-by-value vs pass-by-reference. "
    #     "Check for Modern C++ (C++11/14/17/20) best practices."
    # )
    instructions = (
        "Perform a comprehensive code review focusing on C++ safety and Modern C++ idioms. "
        "1. MEMORY & SAFETY: Strictly enforce RAII. Flag any manual `new/delete` and suggest "
        "`std::unique_ptr` or `std::shared_ptr`. Check for buffer overflows, iterator invalidation, "
        "dangling pointers, and use of C-style arrays (suggest `std::vector` or `std::array`). "
        "2. MODERN PRACTICES: Prominently suggest C++17/20 features (e.g., structured bindings, "
        "concepts, `constexpr`). Recommends STL algorithms over raw loops. "
        "3. CORRECTNESS: Enforce `const` correctness, use of `nullptr` over `NULL`, and C++ style casts "
        "(`static_cast`) over C-style casts. Analyze pass-by-value vs. pass-by-const-reference for efficiency. "
        "4. HOLISTIC CHECK: Do not limit your review to the points above. You must also scan for "
        "logical errors, concurrency issues (data races), exception safety, and edge cases. "
        "If the code works but is 'C with Classes' style, refactor it to idiomatic Modern C++."
    )
    return analyze_with_persona(state, "C++", instructions)
