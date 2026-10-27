# # core/docstring_engine/generator.py
# """core.docstring_engine.generator
# Generate Google-style baseline docstrings given parser metadata.

# Generator is non-destructive: returns docstring text but does not modify code files.
# """
# from typing import Dict, List, Optional
# from .generator_numpy import generate_numpy_docstring
# from .generator_rest import generate_rest_docstring


# def _arg_type_str(arg: Dict) -> str:
#     """Return a single arg type string (placeholder when annotation absent)."""
#     ann = arg.get("annotation")
#     if ann:
#         return ann
#     return "TYPE"

# def _format_args_section(args: List[Dict]) -> str:
#     if not args:
#         return ""
#     lines = []
#     for a in args:
#         name = a["name"]
#         atype = _arg_type_str(a)
#         lines.append(f"    {name} ({atype}): description of {name}.")
#     return "Args:\n" + "\n".join(lines)

# def _format_returns_section(returns: Optional[str], has_return_statements: bool) -> str:
#     if returns:
#         return f"Returns:\n    {returns}: description of return value."
#     if has_return_statements:
#         return "Returns:\n    TYPE: description of return value."
#     return ""

# def _format_raises_section(raises: List[str]) -> str:
#     if not raises:
#         return ""
#     lines = []
#     for r in raises:
#         lines.append(f"    {r}: reason when raised.")
#     return "Raises:\n" + "\n".join(lines)
# def _format_yields_section(yields: bool) -> str:
#     if yields:
#         return "Yields:\n    TYPE: description of yielded values."
#     return ""


# def generate_google_docstring(func_meta: Dict) -> str:
#     """Given func_meta produced by parser, return a Google-style docstring string."""
#     name = func_meta.get("name")
#     args = func_meta.get("args", [])
#     returns = func_meta.get("returns")
#     # heuristic: check if 'return' exists in function body is not available here,
#     # parser could add a flag; for now we assume returns if returns annotation exists
#     has_return_statements = bool(returns)
#     # no raises info available in milestone1; leave empty
#     raises = func_meta.get("raises", [])
#     yields = func_meta.get("yields", False)


#     parts = []
#     parts.append(f"{name} - short description.")
#     args_section = _format_args_section(args)
#     if args_section:
#         parts.append(args_section)
#     returns_section = _format_returns_section(returns, has_return_statements)
#     if returns_section:
#         parts.append(returns_section)
#     raises_section = _format_raises_section(raises)
#     if raises_section:
#         parts.append(raises_section)
#     yields_section = _format_yields_section(yields)
#     if yields_section:
#         parts.append(yields_section)


#     body = "\n\n".join(parts)
#     # assemble triple-quoted docstring
#     doc = '"""\n' + body + "\n\"\"\""
#     return doc
# def generate_docstring(func_meta, style="google"):
#     if style == "google":
#         return generate_google_docstring(func_meta)
#     if style == "numpy":
#         return generate_numpy_docstring(func_meta)
#     if style == "rest":
#         return generate_rest_docstring(func_meta)
#     raise ValueError("Unsupported docstring style")




"""
core.docstring_engine.generator

Generates style-consistent docstrings using:
- LLM for semantic content
- Deterministic formatters for structure
"""

from typing import Dict, List, Optional
from core.docstring_engine.llm_integration import generate_docstring_content


# -------------------------------------------------
# Helpers
# -------------------------------------------------
def _arg_type_str(arg: Dict) -> str:
    return arg.get("annotation") or "TYPE"


def _format_args_section(args: List[Dict], arg_desc: Dict[str, str]) -> str:
    if not args:
        return ""
    lines = ["Args:"]
    for a in args:
        name = a["name"]
        typ = _arg_type_str(a)
        desc = arg_desc.get(name, "DESCRIPTION")
        lines.append(f"    {name} ({typ}): {desc}")
    return "\n".join(lines)


def _format_returns_section(returns: Optional[str], return_desc: str) -> str:
    if not returns:
        return ""
    return f"Returns:\n    {returns}: {return_desc or 'DESCRIPTION'}"


# -------------------------------------------------
# Google style
# -------------------------------------------------
def generate_google_docstring(fn: Dict, llm: Dict) -> str:
    summary = llm.get("summary", f"Short description of `{fn['name']}`.")
    arg_desc = llm.get("args", {})
    return_desc = llm.get("returns", "")
    raises_desc = llm.get("raises", {})

    parts = [summary, ""]

    args_section = _format_args_section(fn.get("args", []), arg_desc)
    if args_section:
        parts.append(args_section)
        parts.append("")

    returns_section = _format_returns_section(fn.get("returns"), return_desc)
    if returns_section:
        parts.append(returns_section)
        parts.append("")

    if raises_desc:
        parts.append("Raises:")
        for exc, desc in raises_desc.items():
            parts.append(f"    {exc}: {desc}")
        parts.append("")

    doc = "\n".join(parts).strip()
    return f'"""\n{doc}\n"""'


# -------------------------------------------------
# NumPy style
# -------------------------------------------------
def generate_numpy_docstring(fn: Dict, llm: Dict) -> str:
    summary = llm.get("summary", f"{fn['name']} function.")
    arg_desc = llm.get("args", {})
    return_desc = llm.get("returns", "")
    raises_desc = llm.get("raises", {})

    lines = [summary, "", "Parameters", "----------"]

    for arg in fn.get("args", []):
        t = arg.get("annotation") or "TYPE"
        desc = arg_desc.get(arg["name"], "DESCRIPTION")
        lines.append(f"{arg['name']} : {t}")
        lines.append(f"    {desc}")

    if fn.get("returns"):
        lines.extend([
            "",
            "Returns",
            "-------",
            f"{fn['returns']}",
            f"    {return_desc or 'DESCRIPTION'}"
        ])

    if raises_desc:
        lines.extend(["", "Raises", "------"])
        for exc, desc in raises_desc.items():
            lines.append(f"{exc}")
            lines.append(f"    {desc}")

    return f'"""\n' + "\n".join(lines) + '\n"""'


# -------------------------------------------------
# reST style
# -------------------------------------------------
def generate_rest_docstring(fn: Dict, llm: Dict) -> str:
    summary = llm.get("summary", f"{fn['name']} function.")
    arg_desc = llm.get("args", {})
    return_desc = llm.get("returns", "")
    raises_desc = llm.get("raises", {})

    lines = [summary, ""]

    for arg in fn.get("args", []):
        t = arg.get("annotation") or "TYPE"
        desc = arg_desc.get(arg["name"], "DESCRIPTION")
        lines.append(f":param {arg['name']}: {desc}")
        lines.append(f":type {arg['name']}: {t}")

    if fn.get("returns"):
        lines.append(f":return: {return_desc or 'DESCRIPTION'}")
        lines.append(f":rtype: {fn['returns']}")

    for exc, desc in raises_desc.items():
        lines.append(f":raises {exc}: {desc}")

    return f'"""\n' + "\n".join(lines) + '\n"""'


# -------------------------------------------------
# Main entry
# -------------------------------------------------
def generate_docstring(fn: Dict, style: str = "google") -> str:
    """
    Generate docstring using:
    - LLM for meaning
    - Code for formatting
    """

    llm_content = generate_docstring_content(fn)

    if style == "google":
        return generate_google_docstring(fn, llm_content)
    elif style == "numpy":
        return generate_numpy_docstring(fn, llm_content)
    elif style == "rest":
        return generate_rest_docstring(fn, llm_content)
    else:
        raise ValueError(f"Unknown style: {style}")




