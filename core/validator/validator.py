import subprocess
import sys
import ast
from typing import List, Dict, Any


class ValidationResult(list):
    """List subclass containing issue strings that also supports dict access."""
    def __init__(self, issues: List[str], passed: bool):
        super().__init__(issues)
        self.passed = passed
        self.issues = issues

    def __getitem__(self, key):
        if key == "passed":
            return self.passed
        if key == "issues":
            return self.issues
        return super().__getitem__(key)

    def get(self, key, default=None):
        if key == "passed":
            return self.passed
        if key == "issues":
            return self.issues
        return default


def run_pydocstyle(path: str):
    """Execute pydocstyle and return a ValidationResult list of issue strings."""
    result = subprocess.run(
        [sys.executable, "-m", "pydocstyle", str(path)],
        capture_output=True,
        text=True
    )

    raw_output = result.stderr or result.stdout

    issues = []
    block = []

    for line in raw_output.splitlines():
        if line.strip() == "":
            if block:
                issues.append("\n".join(block))
                block = []
        else:
            block.append(line.rstrip())

    if block:
        issues.append("\n".join(block))

    return ValidationResult(issues=issues, passed=(result.returncode == 0))


def validate_docstrings(path: str):
    """
    Validate docstrings using pydocstyle.
    Returns list of issue strings.
    """
    result = run_pydocstyle(path)
    if result.passed:
        return []
    return result.issues


def compute_complexity(source_code: str) -> List[Dict[str, Any]]:
    """
    Compute cyclomatic complexity for all functions in the given source code.
    Returns list of dicts: [{"name": str, "complexity": int, "line": int}].
    """
    try:
        tree = ast.parse(source_code)
    except Exception:
        return []

    results = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            complexity = 1
            for child in ast.walk(node):
                if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try,
                                      ast.ExceptHandler, ast.ListComp, ast.DictComp,
                                      ast.SetComp, ast.GeneratorExp, ast.IfExp)):
                    complexity += 1
                elif isinstance(child, ast.BoolOp):
                    complexity += max(1, len(child.values) - 1)
            results.append({
                "name": node.name,
                "complexity": complexity,
                "line": node.lineno
            })
    return results
