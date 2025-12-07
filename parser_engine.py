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
        # 1. Setup
        key = lang_name.lower().replace("#", "sharp").replace("++", "cpp")
        strategy = STRATEGIES.get(key)
        if not strategy:
            print(
                f"⚠️ Warning: Language '{lang_name}' not supported. Defaulting to Python.",
            )
            strategy = STRATEGIES["python"]

        self.parser.language = strategy.language
        tree = self.parser.parse(bytes(code, "utf8"))
        root_node = tree.root_node

        # 2. Validation
        self._check_syntax_validity(root_node, lang_name)

        # 3. GLOBAL SCAN: Build Symbol Table (Name -> Node)
        # We look for classes, structs, or globals defined at the root level
        global_symbols = self._build_global_symbol_table(root_node, code)

        functions: list[dict[str, Any]] = []

        # 4. Recursive Walk (Passing the symbol table down)
        self._find_functions_recursive(
            root_node,
            code,
            functions,
            strategy.function_node_types,
            global_symbols,
        )

        return functions

    def _build_global_symbol_table(self, root_node, code):  # noqa: ARG002
        """Scans top-level definitions to find dependencies (Classes, Structs, Globals)."""
        symbols = {}
        for child in root_node.children:
            name = self._get_name(child)
            if name and name != "anonymous":
                symbols[name] = child
        return symbols

    def _find_functions_recursive(
        self,
        node,
        code,
        functions,
        target_types,
        global_symbols,
    ):
        if node.type in target_types:
            functions.append(self._process_node(node, code, global_symbols))

        for child in node.children:
            self._find_functions_recursive(
                child,
                code,
                functions,
                target_types,
                global_symbols,
            )

    def _process_node(self, node, full_code: str, global_symbols: dict):
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1

        lines = full_code.split("\n")
        function_source = "\n".join(lines[start_line - 1 : end_line])

        # --- STATIC ANALYSIS: CONTEXT EXTRACTION ---
        context_block = self._extract_dependencies(node, full_code, global_symbols)

        # If context exists, prepend it to the code sent to AI
        if context_block:
            final_code_payload = f"{context_block}\n\n{function_source}"
        else:
            final_code_payload = function_source

        # Body for hashing
        body_node = node.child_by_field_name("body")
        body_text = body_node.text.decode("utf8") if body_node else ""

        return {
            "name": self._get_name(node),
            "start_line": start_line,
            "end_line": end_line,
            "code": final_code_payload,  # AI gets Context + Function
            "body_only": body_text,
        }

    def _extract_dependencies(self, function_node, full_code, global_symbols):
        """Finds identifiers used inside the function that match global definitions."""
        used_identifiers = set()
        function_name = self._get_name(function_node)

        # Walk the function body to find usages
        cursor = function_node.walk()

        # Helper to traverse entire subtree
        visited_children = False
        while True:
            # Tree-sitter types for names: 'identifier', 'type_identifier', 'field_identifier'
            if cursor.node.type in ["identifier", "type_identifier"]:
                name = cursor.node.text.decode("utf8")
                if name != function_name:  # Don't match self-recursion
                    used_identifiers.add(name)

            if (
                not visited_children and cursor.goto_first_child()
            ) or cursor.goto_next_sibling():
                visited_children = False
            elif cursor.goto_parent():
                visited_children = True
            else:
                break

        # Match Usages to Definitions
        context_snippets = []
        for identifier in used_identifiers:
            if identifier in global_symbols:
                def_node = global_symbols[identifier]
                skeleton = self._create_skeleton(def_node, full_code)
                context_snippets.append(skeleton)

        if not context_snippets:
            return ""

        return (
            "### CONTEXT (Dependencies detected via Static Analysis) ###\n"
            + "\n".join(context_snippets)
        )

    def _create_skeleton(self, node, full_code):
        """
        Creates a token-efficient summary.

        e.g., 'class User { ... }' instead of the whole class.
        """
        lines = full_code.split("\n")
        start_line = node.start_point[0]

        # Heuristic: Grab the signature line
        header = lines[start_line].strip()

        # Check if it's a block-based structure (Class/Struct)
        if "{" in header or ":" in header:
            return f"{header} ... (Implementation hidden for brevity) }}"

        return f"{header} ... (Summary)"

    def _get_name(self, node):
        name_node = node.child_by_field_name("name")
        if not name_node:
            name_node = node.child_by_field_name("declarator")
        return name_node.text.decode("utf8") if name_node else "anonymous"

    def _check_syntax_validity(self, root_node, lang_name):
        total_nodes = 0
        error_nodes = 0
        cursor = root_node.walk()
        visited_children = False
        while True:
            total_nodes += 1
            if cursor.node.type == "ERROR":
                error_nodes += 1
            if (
                not visited_children and cursor.goto_first_child()
            ) or cursor.goto_next_sibling():
                visited_children = False
            elif cursor.goto_parent():
                visited_children = True
            else:
                break
        if total_nodes > 0 and (error_nodes / total_nodes) > 0.05:  # noqa: PLR2004
            msg = f"High syntax error rate. Are you sure this is {lang_name}?"
            raise ValueError(
                msg,
            )


def get_parser():
    """
    Creates a new parser instance for each request.

    This prevents race conditions where Request A changes the language
    while Request B is parsing.
    """
    return TreeSitterParser()
