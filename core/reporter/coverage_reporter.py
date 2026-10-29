# core/reporter/coverage_reporter.py
"""Compute docstring coverage and write report to JSON."""
import json
from pathlib import Path
from typing import Any, Dict, List


def compute_coverage(per_file_results: List[Dict[str, Any]], threshold: float = 80.0) -> Dict[str, Any]:
    """Compute per-file coverage summary and global summary.

    per_file_results: list of parse_file outputs (dicts with 'functions' and 'classes')
    threshold: docstring coverage percentage threshold (default 80.0)
    """
    files = {}
    total_items = 0
    total_docs = 0

    for r in per_file_results:
        path = r.get("path") or r.get("file_path", "unknown")
        fns = r.get("functions", [])
        classes = r.get("classes", [])
        file_items = 0
        file_docs = 0
        items = []

        # Functions
        for f in fns:
            file_items += 1
            if f.get("has_docstring"):
                file_docs += 1
            items.append({
                "type": "function",
                "name": f.get("name"),
                "lineno": f.get("lineno"),
                "has_doc": f.get("has_docstring")
            })

        # Classes and methods
        for c in classes:
            file_items += 1
            if c.get("has_docstring"):
                file_docs += 1
            items.append({
                "type": "class",
                "name": c.get("name"),
                "lineno": c.get("lineno"),
                "has_doc": c.get("has_docstring")
            })
            for m in c.get("methods", []):
                file_items += 1
                if m.get("has_docstring"):
                    file_docs += 1
                items.append({
                    "type": "method",
                    "class": c.get("name"),
                    "name": m.get("name"),
                    "lineno": m.get("lineno"),
                    "has_doc": m.get("has_docstring")
                })

        pct = round((file_docs / file_items) * 100, 2) if file_items > 0 else 100.0
        files[str(path)] = {
            "total_items": file_items,
            "doc_count": file_docs,
            "coverage_percent": pct,
            "items": items
        }
        total_items += file_items
        total_docs += file_docs

    overall = round((total_docs / total_items) * 100, 2) if total_items > 0 else 0.0
    aggregate = {
        "total_items": total_items,
        "total_functions": total_items,
        "total_docs": total_docs,
        "documented": total_docs,
        "coverage_percent": overall,
        "meets_threshold": bool(overall >= threshold),
    }

    return {
        "files": files,
        "summary": aggregate,
        "aggregate": aggregate
    }


def write_report(report: Dict[str, Any], path: str) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
