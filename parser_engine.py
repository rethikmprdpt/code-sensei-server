import json

import tree_sitter_python
from tree_sitter import Language, Parser


class TreeSitterParser:
    def __init__(self):
        # Initialize the Python Language Grammar
        # tree_sitter_python.language() returns the compiled C grammar object
        self.PY_LANGUAGE = Language(tree_sitter_python.language())

        # Initialize the Parser
        self.parser = Parser()
        self.parser.language = self.PY_LANGUAGE
        # self.parser.set_language(self.PY_LANGUAGE)

    def parse(self, code: str):
        """Parses a string of code into a Tree-sitter Tree."""
        # Tree-sitter expects bytes, not strings
        return self.parser.parse(bytes(code, "utf8"))

    def extract_functions(self, code: str):
        """Walks the CST and returns a list of function blocks with metadata."""
        tree = self.parse(code)
        root_node = tree.root_node

        functions = []

        # A cursor allows us to walk the tree efficiently
        cursor = tree.walk()  # noqa: F841

        # We can also traverse recursively. For a POC, simple traversal is fine.
        # But for robust parsing, we inspect the children of the root.
        for node in root_node.children:
            # We specifically look for function definitions
            if node.type == "function_definition":
                func_data = self._process_node(node, code)
                functions.append(func_data)

            # If there is a class, we might want methods inside it
            elif node.type == "class_definition":
                # iterate through class body to find methods
                body_node = node.child_by_field_name("body")
                if body_node:
                    for child in body_node.children:
                        if child.type == "function_definition":
                            func_data = self._process_node(child, code)
                            functions.append(func_data)

        return functions

    def _process_node(self, node, full_code: str):
        """Helper to extract line numbers and raw code from a node."""
        # node.start_point returns (row, col)
        start_line = node.start_point[0] + 1  # 1-indexed for humans
        end_line = node.end_point[0] + 1

        # Extract the raw source code for this specific function
        # We split the original code to get the lines
        lines = full_code.split("\n")
        # +1 on end_line because python slicing is exclusive
        function_source = "\n".join(lines[start_line - 1 : end_line])

        return {
            "name": self._get_function_name(node),
            "start_line": start_line,
            "end_line": end_line,
            "code": function_source,
            "node_type": node.type,
        }

    def _get_function_name(self, node):
        """Extracts the function name from the node."""
        # In the CST, a function_definition has a child field called 'name'
        name_node = node.child_by_field_name("name")
        if name_node:
            # content is bytes, decode to string
            return name_node.text.decode("utf8")
        return "anonymous"


# Simple test block to verify it works standalone
if __name__ == "__main__":
    sample_code = """
def add(a, b):
    return a + b

class Calculator:
    def multiply(self, x, y):
        # This is a comment
        return x * y
    """

    parser = TreeSitterParser()
    results = parser.extract_functions(sample_code)

    print(parser.parse(sample_code).print_dot_graph(1))

    print(json.dumps(results, indent=2))
