"""
core.docstring_engine.generator

Generates style-consistent docstrings using:
- LLM for semantic content (with full code context)
- Deterministic formatters for PEP 257 & Google/NumPy/reST structure
"""

from typing import Dict, List, Optional
from core.docstring_engine.llm_integration import generate_docstring_content


# -------------------------------------------------
# Helpers
# -------------------------------------------------
def _get_arg_type(arg: Dict, arg_types: Dict[str, str]) -> str:
    return arg.get("annotation") or arg_types.get(arg.get("name", ""), "Any")


def _clean_period(text: str) -> str:
    text = text.strip()
    if text and not text.endswith((".", "!", "?")):
        return text + "."
    return text


def _clean_exc_name(exc: str) -> str:
    """Extract class name from calls like ValueError('bad')."""
    return exc.split("(")[0].strip()


# -------------------------------------------------
# Google style
# -------------------------------------------------
def generate_google_docstring(fn: Dict, llm: Dict) -> str:
    summary = _clean_period(llm.get("summary", f"Process `{fn['name']}` operations."))
    arg_desc = llm.get("args", {})
    arg_types = llm.get("arg_types", {})
    return_desc = llm.get("returns", "")
    return_type = fn.get("returns") or llm.get("return_type", "")
    raises_desc = llm.get("raises", {})

    parts = [summary, ""]

    # Filter out self/cls
    args_meta = [a for a in fn.get("args", []) if a.get("name") not in ("self", "cls")]
    if args_meta:
        lines = ["Args:"]
        for a in args_meta:
            name = a["name"]
            typ = _get_arg_type(a, arg_types)
            desc = _clean_period(arg_desc.get(name, f"The {name} argument."))
            lines.append(f"    {name} ({typ}): {desc}")
        parts.append("\n".join(lines))
        parts.append("")

    if return_desc or (return_type and return_type.lower() != "none"):
        ret_type_str = return_type or "Any"
        ret_msg = _clean_period(return_desc or "Result of function execution.")
        parts.append(f"Returns:\n    {ret_type_str}: {ret_msg}")
        parts.append("")

    if raises_desc:
        lines = ["Raises:"]
        for exc, desc in raises_desc.items():
            exc_clean = _clean_exc_name(exc)
            desc_clean = _clean_period(desc)
            lines.append(f"    {exc_clean}: {desc_clean}")
        parts.append("\n".join(lines))
        parts.append("")

    doc = "\n".join(parts).strip()
    return f'"""\n{doc}\n"""'


# -------------------------------------------------
# NumPy style
# -------------------------------------------------
def generate_numpy_docstring(fn: Dict, llm: Dict) -> str:
    summary = _clean_period(llm.get("summary", f"Process `{fn['name']}` operations."))
    arg_desc = llm.get("args", {})
    arg_types = llm.get("arg_types", {})
    return_desc = llm.get("returns", "")
    return_type = fn.get("returns") or llm.get("return_type", "")
    raises_desc = llm.get("raises", {})

    lines = [summary, ""]

    args_meta = [a for a in fn.get("args", []) if a.get("name") not in ("self", "cls")]
    if args_meta:
        lines.extend(["Parameters", "----------"])
        for a in args_meta:
            name = a["name"]
            typ = _get_arg_type(a, arg_types)
            desc = _clean_period(arg_desc.get(name, f"The {name} input parameter."))
            lines.append(f"{name} : {typ}")
            lines.append(f"    {desc}")
        lines.append("")

    if return_desc or (return_type and return_type.lower() != "none"):
        lines.extend([
            "Returns",
            "-------",
            f"{return_type or 'Any'}",
            f"    {_clean_period(return_desc or 'Result of the function.')}",
            ""
        ])

    if raises_desc:
        lines.extend(["Raises", "------"])
        for exc, desc in raises_desc.items():
            exc_clean = _clean_exc_name(exc)
            lines.append(f"{exc_clean}")
            lines.append(f"    {_clean_period(desc)}")
        lines.append("")

    doc = "\n".join(lines).strip()
    return f'"""\n{doc}\n"""'


# -------------------------------------------------
# reST style
# -------------------------------------------------
def generate_rest_docstring(fn: Dict, llm: Dict) -> str:
    summary = _clean_period(llm.get("summary", f"Process `{fn['name']}` operations."))
    arg_desc = llm.get("args", {})
    arg_types = llm.get("arg_types", {})
    return_desc = llm.get("returns", "")
    return_type = fn.get("returns") or llm.get("return_type", "")
    raises_desc = llm.get("raises", {})

    lines = [summary, ""]

    args_meta = [a for a in fn.get("args", []) if a.get("name") not in ("self", "cls")]
    for a in args_meta:
        name = a["name"]
        typ = _get_arg_type(a, arg_types)
        desc = _clean_period(arg_desc.get(name, f"The {name} input parameter."))
        lines.append(f":param {name}: {desc}")
        lines.append(f":type {name}: {typ}")

    if return_desc or (return_type and return_type.lower() != "none"):
        lines.append(f":return: {_clean_period(return_desc or 'Result of the function.')}")
        if return_type:
            lines.append(f":rtype: {return_type}")

    for exc, desc in raises_desc.items():
        exc_clean = _clean_exc_name(exc)
        lines.append(f":raises {exc_clean}: {_clean_period(desc)}")

    doc = "\n".join(lines).strip()
    return f'"""\n{doc}\n"""'


# -------------------------------------------------
# Main entry
# -------------------------------------------------
def generate_docstring(fn: Dict, style: str = "google") -> str:
    """
    Generate docstring using:
    - LLM for meaning and type inference
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
