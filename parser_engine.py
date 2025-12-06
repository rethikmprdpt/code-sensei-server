import tree_sitter_c_sharp as tree_sitter_csharp
import tree_sitter_cpp
import tree_sitter_java
import tree_sitter_javascript
import tree_sitter_python
from tree_sitter import Language, Parser


class LanguageStrategy:
    """
    Configuration class to map a specific language grammar.

    to the node types that represent 'functions' or 'methods' in that language.
    """

    def __init__(self, lang_module, function_node_types):
        # Load the compiled C grammar
        self.language = Language(lang_module.language())
        # List of node types to search for (e.g. ['function_definition', 'arrow_function'])
        self.function_node_types = function_node_types


# --- STRATEGY MAPPING ---
# This dictionary maps the frontend selection to specific Tree-sitter configurations.
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
        """Main entry point. Parses code and extracts function blocks based on language."""
        # 1. Normalize Language Name (handle c++ -> cpp, c# -> csharp)
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

        # 4. Parse Code (Tree-sitter expects bytes)
        tree = self.parser.parse(bytes(code, "utf8"))
        root_node = tree.root_node

        functions: list[LanguageStrategy] = []

        # 5. Recursive Walk
        self._find_functions_recursive(
            root_node,
            code,
            functions,
            strategy.function_node_types,
        )

        return functions

    def _find_functions_recursive(self, node, code, functions, target_types):
        """Recursively searches the tree for nodes matching the target types."""
        if node.type in target_types:
            functions.append(self._process_node(node, code))

        # Recurse into children (e.g., methods inside classes, functions inside namespaces)
        for child in node.children:
            self._find_functions_recursive(child, code, functions, target_types)

    def _process_node(self, node, full_code: str):
        """Extracts metadata, raw code, and body text from a specific node."""
        # Tree-sitter uses 0-indexed rows, we convert to 1-indexed for UI display
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1

        lines = full_code.split("\n")
        # Extract the exact source code for this block
        function_source = "\n".join(lines[start_line - 1 : end_line])

        # Extract BODY ONLY for Deduplication (ignoring function name changes)
        # Most languages have a 'body' or 'block' child field
        body_node = node.child_by_field_name("body")
        body_text = body_node.text.decode("utf8") if body_node else ""

        return {
            "name": self._get_name(node),
            "start_line": start_line,
            "end_line": end_line,
            "code": function_source,
            "body_only": body_text,  # Used for hashing in the DB
        }

    def _get_name(self, node):
        """
        Heuristic to find the function name.

        Different languages use different field names for the identifier.
        """
        # Python/JS/C++ often use 'name'
        name_node = node.child_by_field_name("name")

        # C++/Java sometimes use 'declarator'
        if not name_node:
            name_node = node.child_by_field_name("declarator")

        if name_node:
            # If the declarator is complex (e.g., pointer *foo), we might need to dig deeper
            # For this POC, getting the raw text of the name node is sufficient
            return name_node.text.decode("utf8")

        return "anonymous"


# --- TEST BLOCK ---
if __name__ == "__main__":
    parser = TreeSitterParser()

    print("--- Testing Python ---")
    py_code = """
    def my_func(x):
        return x * 2
    """
    print(parser.extract_functions(py_code, "python"))

    print("\n--- Testing C++ ---")
    cpp_code = """
    int main() {
        return 0;
    }
    """
    print(parser.extract_functions(cpp_code, "cpp"))

    print("\n--- Testing JavaScript ---")
    js_code = """
    function hello() {
        console.log("world");
    }
    const arrow = () => { return true; }
    """
    print(parser.extract_functions(js_code, "javascript"))
