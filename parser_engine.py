from typing import Any

import tree_sitter_c_sharp as tree_sitter_csharp
import tree_sitter_cpp
import tree_sitter_java
import tree_sitter_javascript
import tree_sitter_python
from tree_sitter import Language, Parser


class LanguageStrategy:
    def __init__(self, lang_module, function_node_types):
        self.language = Language(lang_module.language())
        self.function_node_types = function_node_types


STRATEGIES = {
    "python": LanguageStrategy(tree_sitter_python, ["function_definition"]),
    "javascript": LanguageStrategy(
        tree_sitter_javascript,
        ["function_declaration", "arrow_function", "method_definition"],
    ),
    "cpp": LanguageStrategy(tree_sitter_cpp, ["function_definition"]),
    "java": LanguageStrategy(
        tree_sitter_java,
        ["method_declaration", "constructor_declaration"],
    ),
    "csharp": LanguageStrategy(
        tree_sitter_csharp,
        ["method_declaration", "local_function_statement"],
    ),
}


class TreeSitterParser:
    def __init__(self):
        self.parser = Parser()

    def extract_functions(self, code: str, lang_name: str = "python"):
        # 1. Normalize Language Name
        key = lang_name.lower().replace("#", "sharp").replace("++", "cpp")

        # 2. Load Strategy
        strategy = STRATEGIES.get(key)
        if not strategy:
            print(
                f"⚠️ Warning: Language '{lang_name}' not supported. Defaulting to Python.",
            )
            strategy = STRATEGIES["python"]

        # 3. Configure Parser
        self.parser.language = strategy.language

        # 4. Parse Code
        tree = self.parser.parse(bytes(code, "utf8"))
        root_node = tree.root_node

        # --- NEW: VALIDATION CHECK ---
        # If the code looks like garbage for this language, stop immediately.
        self._check_syntax_validity(root_node, lang_name)

        functions: list[dict[str, Any]] = []

        # 5. Recursive Walk
        self._find_functions_recursive(
            root_node,
            code,
            functions,
            strategy.function_node_types,
        )

        return functions

    def _check_syntax_validity(self, root_node, lang_name):
        """
        Calculates the ratio of ERROR nodes to total nodes.

        If too many errors, assumes language mismatch.
        """
        total_nodes = 0
        error_nodes = 0

        cursor = root_node.walk()
        visited_children = False

        while True:
            total_nodes += 1
            if cursor.node.type == "ERROR":
                error_nodes += 1

            # Depth-First Search Traversal
            if (
                not visited_children and cursor.goto_first_child()
            ) or cursor.goto_next_sibling():
                visited_children = False
            elif cursor.goto_parent():
                visited_children = True
            else:
                break

        if total_nodes == 0:
            return  # Empty file, let other logic handle it

        error_ratio = error_nodes / total_nodes

        # Threshold: If > 5% of the tree is syntax errors, reject it.
        if error_ratio > 0.05:  # noqa: PLR2004
            msg = (
                f"High syntax error rate ({error_ratio:.1%}). "
                f"Are you sure this is {lang_name} code? "
                "Please check your language selection."
            )
            raise ValueError(
                msg,
            )

    def _find_functions_recursive(self, node, code, functions, target_types):
        if node.type in target_types:
            functions.append(self._process_node(node, code))

        for child in node.children:
            self._find_functions_recursive(child, code, functions, target_types)

    def _process_node(self, node, full_code: str):
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1

        lines = full_code.split("\n")
        function_source = "\n".join(lines[start_line - 1 : end_line])

        body_node = node.child_by_field_name("body")
        body_text = body_node.text.decode("utf8") if body_node else ""

        return {
            "name": self._get_name(node),
            "start_line": start_line,
            "end_line": end_line,
            "code": function_source,
            "body_only": body_text,
        }

    def _get_name(self, node):
        name_node = node.child_by_field_name("name")
        if not name_node:
            name_node = node.child_by_field_name("declarator")

        if name_node:
            return name_node.text.decode("utf8")

        return "anonymous"


def get_parser():
    """
    Creates a new parser instance for each request.

    This prevents race conditions where Request A changes the language
    while Request B is parsing.
    """
    return TreeSitterParser()
