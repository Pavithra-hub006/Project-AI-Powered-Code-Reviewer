# core/parser/python_parser.py
"""AST-based per-file Python parser for Milestone 1.

Extracts:
 - functions (name, args, annotations, defaults, returns, start/end lines)
 - classes (and their methods)
 - imports
 - simple complexity estimate (heuristic)
 - nesting depth
 - presence of docstring
"""
import ast
import os
from typing import Any, Dict, List, Optional
def _extract_raises(node: ast.AST) -> List[str]:
    raises = []
    for n in ast.walk(node):
        if isinstance(n, ast.Raise) and n.exc:
            try:
                raises.append(ast.unparse(n.exc))
            except Exception:
                pass
    return raises


def _has_yield(node: ast.AST) -> bool:
    return any(isinstance(n, ast.Yield) for n in ast.walk(node))


def _extract_class_attributes(c: ast.ClassDef) -> List[str]:
    attrs = []
    for n in c.body:
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    attrs.append(t.id)
    return attrs


def _get_annotation_str(node: Optional[ast.AST]) -> Optional[str]:
    if node is None:
        return None
    try:
        # ast.unparse available in 3.9+
        return ast.unparse(node)
    except Exception:
        return None

def _get_default_str(node: Optional[ast.AST]) -> Optional[str]:
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:
        return None

def _simple_complexity(node: ast.FunctionDef) -> int:
    """Heuristic complexity: count branches, loops, comprehensions, calls."""
    counter = 0
    for n in ast.walk(node):
        if isinstance(n, (ast.If, ast.For, ast.While, ast.With, ast.Try,
                          ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp,
                          ast.IfExp)):
            counter += 1
        if isinstance(n, ast.Call):
            counter += 0  # don't blow up, keep calls neutral
    # Add length factor
    lines = (getattr(node, "end_lineno", node.lineno) - node.lineno) if getattr(node, "end_lineno", None) else 0
    return max(1, counter + (lines // 10))

def _max_nesting_depth(node: ast.FunctionDef) -> int:
    """Compute max nesting depth for control flow inside function."""
    max_depth = 0

    def walk(n: ast.AST, depth: int):
        nonlocal max_depth
        if isinstance(n, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
            depth += 1
            max_depth = max(max_depth, depth)
        for child in ast.iter_child_nodes(n):
            walk(child, depth)

    walk(node, 0)
    return max_depth

def parse_functions(node: ast.AST) -> List[Dict[str, Any]]:
    results = []
    for n in [c for c in node.body if isinstance(c, ast.FunctionDef)]:
        args = []
        # positional args
        for a in n.args.args:
            args.append({
                "name": a.arg,
                "annotation": _get_annotation_str(a.annotation) if getattr(a, "annotation", None) else None,
            })
        # kwonlyargs
        for a in getattr(n.args, "kwonlyargs", []):
            args.append({
                "name": a.arg,
                "annotation": _get_annotation_str(a.annotation) if getattr(a, "annotation", None) else None,
            })
        # defaults alignment
        defaults = []
        for d in getattr(n.args, "defaults", []):
            defaults.append(_get_default_str(d))
        returns = _get_annotation_str(n.returns)
        item = {
            "type": "function",
            "name": n.name,
            "lineno": n.lineno,
            "end_lineno": getattr(n, "end_lineno", None),
            "args": args,
            "defaults": defaults,
            "returns": returns,
            "has_docstring": bool(ast.get_docstring(n)),
            "complexity": _simple_complexity(n),
            "nesting_depth": _max_nesting_depth(n),
            "raises": _extract_raises(n),
            "yields": _has_yield(n),
            "indent": n.col_offset + 4,
              }
        results.append(item)
    return results

def parse_classes(node: ast.AST) -> List[Dict[str, Any]]:
    classes = []
    for c in [c for c in node.body if isinstance(c, ast.ClassDef)]:
        methods = []
        for m in [m for m in c.body if isinstance(m, ast.FunctionDef)]:
            args = []
            for a in m.args.args:
                args.append({"name": a.arg, "annotation": _get_annotation_str(a.annotation) if getattr(a, "annotation", None) else None})
            methods.append({
                "type": "method",
                "name": m.name,
                "lineno": m.lineno,
                "end_lineno": getattr(m, "end_lineno", None),
                "args": args,
                "returns": _get_annotation_str(m.returns),
                "has_docstring": bool(ast.get_docstring(m)),
                "complexity": _simple_complexity(m),
                "nesting_depth": _max_nesting_depth(m),
                "class_attributes": _extract_class_attributes(c),
                "indent": m.col_offset + 4,

            })
        classes.append({
            "type": "class",
            "name": c.name,
            "lineno": c.lineno,
            "end_lineno": getattr(c, "end_lineno", None),
            "has_docstring": bool(ast.get_docstring(c)),
            "methods": methods
        })
    return classes

def parse_imports(node: ast.AST) -> List[str]:
    imports = []
    for n in ast.walk(node):
        if isinstance(n, ast.Import):
            for alias in n.names:
                imports.append(alias.name)
        elif isinstance(n, ast.ImportFrom):
            module = n.module or ""
            for alias in n.names:
                imports.append(f"{module}.{alias.name}" if module else alias.name)
    return sorted(set(imports))

def parse_file(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()
    tree = ast.parse(source)
    return {
        "path": path,
        "functions": parse_functions(tree),
        "classes": parse_classes(tree),
        "imports": parse_imports(tree),
        "module_docstring": bool(ast.get_docstring(tree))
    }

def parse_path(path: str, recursive: bool = True, skip_dirs: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Walk a file or directory and parse python files. Returns list of per-file dicts."""
    if skip_dirs is None:
        skip_dirs = ["venv", ".venv", "__pycache__", ".git"]
    results = []
    if os.path.isfile(path) and path.endswith(".py"):
        results.append(parse_file(path))
        return results
    for root, dirs, files in os.walk(path):
        # filter skip dirs
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for fn in files:
            if fn.endswith(".py") and not fn.startswith("__"):
                fp = os.path.join(root, fn)
                try:
                    results.append(parse_file(fp))
                except Exception:
                    # continue on parse errors
                    pass
        if not recursive:
            break
    return results
