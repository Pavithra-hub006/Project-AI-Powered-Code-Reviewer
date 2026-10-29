# core/parser/python_parser.py
"""AST-based per-file Python parser for Code Reviewer.

Extracts:
 - functions and async functions (name, args, annotations, defaults, returns, code, lines)
 - classes (and their methods, class attributes, docstrings, code)
 - imports
 - complexity estimate (branches, loops, comprehensions)
 - nesting depth
 - docstring presence and text
"""
import ast
import os
from typing import Any, Dict, List, Optional


def _extract_raises(node: ast.AST) -> List[str]:
    """Extract clean exception class names raised in function/method."""
    raises = []
    for n in ast.walk(node):
        if isinstance(n, ast.Raise) and n.exc:
            exc = n.exc
            if isinstance(exc, ast.Call):
                exc = exc.func
            try:
                name = ast.unparse(exc)
                if name and name not in raises:
                    raises.append(name)
            except Exception:
                pass
    return raises


def _has_yield(node: ast.AST) -> bool:
    return any(isinstance(n, (ast.Yield, ast.YieldFrom)) for n in ast.walk(node))


def _extract_class_attributes(c: ast.ClassDef) -> List[str]:
    attrs = []
    for n in c.body:
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    attrs.append(t.id)
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            attrs.append(n.target.id)
    return attrs


def _get_annotation_str(node: Optional[ast.AST]) -> Optional[str]:
    if node is None:
        return None
    try:
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


def _simple_complexity(node: ast.AST) -> int:
    """Heuristic cyclomatic complexity: count decision points."""
    counter = 1
    for n in ast.walk(node):
        if isinstance(n, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith,
                          ast.Try, ast.ExceptHandler, ast.ListComp, ast.DictComp,
                          ast.SetComp, ast.GeneratorExp, ast.IfExp, ast.Assert)):
            counter += 1
        elif isinstance(n, ast.BoolOp):
            counter += len(n.values) - 1
    return counter


def _max_nesting_depth(node: ast.AST) -> int:
    """Compute max nesting depth for control flow inside function."""
    max_depth = 0

    def walk(n: ast.AST, depth: int):
        nonlocal max_depth
        if isinstance(n, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith, ast.Try)):
            depth += 1
            max_depth = max(max_depth, depth)
        for child in ast.iter_child_nodes(n):
            walk(child, depth)

    walk(node, 0)
    return max_depth


def parse_functions(node: ast.AST) -> List[Dict[str, Any]]:
    """Parse top-level functions and async functions."""
    results = []
    for n in [c for c in node.body if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef))]:
        args = []
        for a in n.args.args:
            args.append({
                "name": a.arg,
                "annotation": _get_annotation_str(a.annotation) if getattr(a, "annotation", None) else None,
            })
        for a in getattr(n.args, "kwonlyargs", []):
            args.append({
                "name": a.arg,
                "annotation": _get_annotation_str(a.annotation) if getattr(a, "annotation", None) else None,
            })
        defaults = []
        for d in getattr(n.args, "defaults", []):
            defaults.append(_get_default_str(d))
        returns = _get_annotation_str(n.returns)

        try:
            code = ast.unparse(n)
        except Exception:
            code = ""

        docstring = ast.get_docstring(n)

        item = {
            "type": "async_function" if isinstance(n, ast.AsyncFunctionDef) else "function",
            "name": n.name,
            "lineno": n.lineno,
            "end_lineno": getattr(n, "end_lineno", None),
            "args": args,
            "defaults": defaults,
            "returns": returns,
            "has_docstring": bool(docstring),
            "docstring": docstring,
            "complexity": _simple_complexity(n),
            "nesting_depth": _max_nesting_depth(n),
            "raises": _extract_raises(n),
            "yields": _has_yield(n),
            "indent": n.col_offset + 4,
            "code": code,
        }
        results.append(item)
    return results


def parse_classes(node: ast.AST) -> List[Dict[str, Any]]:
    """Parse class definitions and their methods."""
    classes = []
    for c in [c for c in node.body if isinstance(c, ast.ClassDef)]:
        methods = []
        for m in [m for m in c.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]:
            args = []
            for a in m.args.args:
                args.append({
                    "name": a.arg,
                    "annotation": _get_annotation_str(a.annotation) if getattr(a, "annotation", None) else None
                })
            for a in getattr(m.args, "kwonlyargs", []):
                args.append({
                    "name": a.arg,
                    "annotation": _get_annotation_str(a.annotation) if getattr(a, "annotation", None) else None
                })

            try:
                m_code = ast.unparse(m)
            except Exception:
                m_code = ""

            m_docstring = ast.get_docstring(m)

            methods.append({
                "type": "method",
                "name": m.name,
                "class_name": c.name,
                "lineno": m.lineno,
                "end_lineno": getattr(m, "end_lineno", None),
                "args": args,
                "returns": _get_annotation_str(m.returns),
                "has_docstring": bool(m_docstring),
                "docstring": m_docstring,
                "complexity": _simple_complexity(m),
                "nesting_depth": _max_nesting_depth(m),
                "class_attributes": _extract_class_attributes(c),
                "indent": m.col_offset + 4,
                "raises": _extract_raises(m),
                "yields": _has_yield(m),
                "code": m_code,
            })

        c_docstring = ast.get_docstring(c)
        try:
            c_code = ast.unparse(c)
        except Exception:
            c_code = ""

        classes.append({
            "type": "class",
            "name": c.name,
            "lineno": c.lineno,
            "end_lineno": getattr(c, "end_lineno", None),
            "has_docstring": bool(c_docstring),
            "docstring": c_docstring,
            "methods": methods,
            "code": c_code,
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
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        source = f.read()
    tree = ast.parse(source)
    return {
        "path": path,
        "file_path": path,
        "functions": parse_functions(tree),
        "classes": parse_classes(tree),
        "imports": parse_imports(tree),
        "module_docstring": bool(ast.get_docstring(tree))
    }


def parse_path(path: str, recursive: bool = True, skip_dirs: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Walk a file or directory and parse python files. Returns list of per-file dicts."""
    if skip_dirs is None:
        skip_dirs = ["venv", ".venv", "__pycache__", ".git", ".pytest_cache", "build", "dist"]
    results = []
    if os.path.isfile(path) and path.endswith(".py"):
        try:
            results.append(parse_file(path))
        except Exception as e:
            print(f"Error parsing file {path}: {e}")
        return results
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for fn in sorted(files):
            if fn.endswith(".py") and not fn.startswith("__"):
                fp = os.path.join(root, fn)
                try:
                    results.append(parse_file(fp))
                except Exception as e:
                    print(f"Error parsing {fp}: {e}")
        if not recursive:
            break
    return results
