import ast
import subprocess
import sys


class PydocstyleResult(list):
    """List of issue strings that also supports dict access for backward compatibility."""
    def __init__(self, issues, passed=False):
        flat_issues = []
        for it in issues:
            if isinstance(it, (list, tuple)):
                flat_issues.append(" ".join(line.strip() for line in it if line.strip()))
            elif it:
                flat_issues.append(str(it).strip())
        super().__init__(flat_issues)
        self.issues = flat_issues
        self.raw_blocks = issues
        self.passed = passed

    def get(self, key, default=None):
        if key == "issues":
            return self.issues
        if key == "passed":
            return self.passed
        if key == "raw_blocks":
            return self.raw_blocks
        return default

    def __getitem__(self, item):
        if isinstance(item, str):
            return self.get(item)
        return super().__getitem__(item)


def validate_docstrings(path: str):
    """
    Validate docstrings using pydocstyle.
    Returns list of issues (strings).
    """
    result = run_pydocstyle(path)
    if result["passed"]:
        return []
    return result["issues"]


def run_pydocstyle(path: str) -> PydocstyleResult:
    result = subprocess.run(
        [sys.executable, "-m", "pydocstyle", path],
        capture_output=True,
        text=True
    )

    # pydocstyle reports to stderr or stdout
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

    return PydocstyleResult(issues=issues, passed=(result.returncode == 0))


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
            self._handle_func(node)

        def visit_AsyncFunctionDef(self, node):
            self._handle_func(node)

        def _handle_func(self, node):
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

        def visit_AsyncFor(self, node):
            self.complexity += 1
            self.generic_visit(node)

        def visit_While(self, node):
            self.complexity += 1
            self.generic_visit(node)

        def visit_Try(self, node):
            self.complexity += max(1, len(node.handlers))
            self.generic_visit(node)

    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return []

    visitor = ComplexityVisitor()
    visitor.visit(tree)
    return visitor.results
