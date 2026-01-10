def validate_docstrings(path: str):
    """
    Validate docstrings using pydocstyle.
    Returns list of issues (strings).
    """
    result = run_pydocstyle(path)

    if result["passed"]:
        return []

    return result["issues"]
def run_pydocstyle(path):
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "pydocstyle", path],
        capture_output=True,
        text=True
    )

    # pydocstyle reports to stderr
    raw_output = result.stderr or result.stdout

    issues = []
    block = []

    for line in raw_output.splitlines():
        if line.strip() == "":
            if block:
                issues.append(block)
                block = []
        else:
            block.append(line.rstrip())

    if block:
        issues.append(block)

    return {
        "passed": result.returncode == 0,
        "issues": issues   # 🔴 list of lists (each issue multiline)
    }
import ast


def compute_complexity(source_code: str):
    """
    Compute cyclomatic complexity for functions in given source code.

    Returns:
        List[dict]: [{ "name": str, "complexity": int }]
    """
    class ComplexityVisitor(ast.NodeVisitor):
        def __init__(self):
            self.results = []
            self.current_function = None
            self.complexity = 0

        def visit_FunctionDef(self, node):
            prev_function = self.current_function
            prev_complexity = self.complexity

            self.current_function = node.name
            self.complexity = 1  # base complexity

            self.generic_visit(node)

            self.results.append({
                "name": node.name,
                "complexity": self.complexity
            })

            self.current_function = prev_function
            self.complexity = prev_complexity

        def visit_If(self, node):
            self.complexity += 1
            self.generic_visit(node)

        def visit_For(self, node):
            self.complexity += 1
            self.generic_visit(node)

        def visit_While(self, node):
            self.complexity += 1
            self.generic_visit(node)

        def visit_Try(self, node):
            self.complexity += len(node.handlers)
            self.generic_visit(node)

    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return []

    visitor = ComplexityVisitor()
    visitor.visit(tree)
    return visitor.results
