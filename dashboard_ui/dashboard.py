import json
from pathlib import Path


def load_pytest_results():
    """Load pytest JSON report if available."""
    path = Path("storage/reports/pytest_results.json")
    if not path.exists():
        return None
    return json.loads(path.read_text())


def filter_functions(functions, search=None, status=None):
    """Filter functions by name and documentation status."""
    results = functions

    if search:
        results = [
            f for f in results
            if search.lower() in f["name"].lower()
        ]

    if status == "OK":
        results = [f for f in results if f["has_docstring"]]
    elif status == "Fix":
        results = [f for f in results if not f["has_docstring"]]

    return results
