# core/parser/python_parser.py
"""AST-based per-file Python parser.

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
from pathlib import Path
from typing import Any, Dict, List, Optional


def _extract_raises(node: ast.AST) -> List[str]:
    """Extract clean exception class names from raise statements."""
    raises = []
    for n in ast.walk(node):
        if isinstance(n, ast.Raise) and n.exc:
            try:
                exc = n.exc
                if isinstance(exc, ast.Call):
                    name = ast.unparse(exc.func)
                else:
                    name = ast.unparse(exc)
                if name and name not in raises:
                    raises.append(name)
            except Exception:
                pass
    return raises


def _has_yield(node: ast.AST) -> bool:
    """Check if node contains yield expressions."""
    return any(isinstance(n, (ast.Yield, ast.YieldFrom)) for n in ast.walk(node))


def _extract_class_attributes(c: ast.ClassDef) -> List[str]:
    attrs = []
    for n in c.body:
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    attrs.append(t.id)
        elif isinstance(n, ast.AnnAssign):
            if isinstance(n.target, ast.Name):
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
    """Heuristic complexity: count branches, loops, comprehensions."""
    counter = 1
    for n in ast.walk(node):
        if isinstance(n, (ast.If, ast.For, ast.While, ast.With, ast.Try,
                          ast.ExceptHandler, ast.ListComp, ast.DictComp,
                          ast.SetComp, ast.GeneratorExp, ast.IfExp)):
            counter += 1
    return counter


def _max_nesting_depth(node: ast.AST) -> int:
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
    """Parse top-level functions in module AST."""
    results = []
    function_nodes = [c for c in node.body if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef))]
    for n in function_nodes:
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
        docstring_val = ast.get_docstring(n) or ""
        body_lineno = n.body[0].lineno if n.body else (n.lineno + 1)
        body_indent = n.body[0].col_offset if n.body else (n.col_offset + 4)
        try:
            source_code = ast.unparse(n)
        except Exception:
            source_code = ""

        item = {
            "type": "function",
            "name": n.name,
            "lineno": n.lineno,
            "end_lineno": getattr(n, "end_lineno", None),
            "body_lineno": body_lineno,
            "args": args,
            "defaults": defaults,
            "returns": returns,
            "has_docstring": bool(docstring_val),
            "docstring": docstring_val,
            "source_code": source_code,
            "complexity": _simple_complexity(n),
            "nesting_depth": _max_nesting_depth(n),
            "raises": _extract_raises(n),
            "yields": _has_yield(n),
            "indent": body_indent,
        }
        results.append(item)
    return results


def parse_classes(node: ast.AST) -> List[Dict[str, Any]]:
    """Parse classes and their inner methods."""
    classes = []
    class_nodes = [c for c in node.body if isinstance(c, ast.ClassDef)]
    for c in class_nodes:
        methods = []
        method_nodes = [m for m in c.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
        for m in method_nodes:
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
            
            m_docstring = ast.get_docstring(m) or ""
            m_body_lineno = m.body[0].lineno if m.body else (m.lineno + 1)
            m_body_indent = m.body[0].col_offset if m.body else (m.col_offset + 4)
            try:
                m_source = ast.unparse(m)
            except Exception:
                m_source = ""

            methods.append({
                "type": "method",
                "class_name": c.name,
                "name": m.name,
                "lineno": m.lineno,
                "end_lineno": getattr(m, "end_lineno", None),
                "body_lineno": m_body_lineno,
                "args": args,
                "returns": _get_annotation_str(m.returns),
                "has_docstring": bool(m_docstring),
                "docstring": m_docstring,
                "source_code": m_source,
                "complexity": _simple_complexity(m),
                "nesting_depth": _max_nesting_depth(m),
                "class_attributes": _extract_class_attributes(c),
                "raises": _extract_raises(m),
                "yields": _has_yield(m),
                "indent": m_body_indent,
            })

        c_docstring = ast.get_docstring(c) or ""
        c_body_lineno = c.body[0].lineno if c.body else (c.lineno + 1)
        c_body_indent = c.body[0].col_offset if c.body else (c.col_offset + 4)
        try:
            c_source = ast.unparse(c)
        except Exception:
            c_source = ""

        classes.append({
            "type": "class",
            "name": c.name,
            "lineno": c.lineno,
            "end_lineno": getattr(c, "end_lineno", None),
            "body_lineno": c_body_lineno,
            "has_docstring": bool(c_docstring),
            "docstring": c_docstring,
            "source_code": c_source,
            "indent": c_body_indent,
            "class_attributes": _extract_class_attributes(c),
            "raises": _extract_raises(c),
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


def parse_source(source: str, file_path: str = "uploaded_code.py") -> Dict[str, Any]:
    """Parse Python source code directly into metadata dictionary."""
    tree = ast.parse(source)
    return {
        "path": file_path,
        "file_path": file_path,
        "functions": parse_functions(tree),
        "classes": parse_classes(tree),
        "imports": parse_imports(tree),
        "module_docstring": bool(ast.get_docstring(tree))
    }


def parse_file(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()
    return parse_source(source, file_path=path)


def parse_path(path: str, recursive: bool = True, skip_dirs: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Walk a file or directory and parse python files. Returns list of per-file dicts."""
    if skip_dirs is None:
        skip_dirs = ["venv", ".venv", "__pycache__", ".git"]
    results = []
    if os.path.isfile(path) and path.endswith(".py"):
        try:
            results.append(parse_file(path))
        except Exception:
            pass
        return results
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for fn in files:
            if fn.endswith(".py") and not fn.startswith("__"):
                fp = os.path.join(root, fn)
                try:
                    results.append(parse_file(fp))
                except Exception:
                    pass
        if not recursive:
            break
    return results
