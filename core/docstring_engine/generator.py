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
def _format_args_section(args: List[Dict], arg_desc: Dict[str, str]) -> str:
    # Filter out self and cls
    filtered = [a for a in args if a.get("name") not in ("self", "cls")]
    if not filtered:
        return ""
    lines = ["Args:"]
    for a in filtered:
        name = a["name"]
        annotation = a.get("annotation")
        desc = arg_desc.get(name, f"The {name} argument.")
        if annotation:
            lines.append(f"    {name} ({annotation}): {desc}")
        else:
            lines.append(f"    {name}: {desc}")
    return "\n".join(lines)


def _format_returns_section(returns: Optional[str], return_desc: str) -> str:
    if not returns and not return_desc:
        return ""
    if returns in ("None", "NoneType") and not return_desc:
        return ""
    
    clean_desc = return_desc or "Result of the operation."
    if returns and returns not in ("None", "NoneType"):
        return f"Returns:\n    {returns}: {clean_desc}"
    elif clean_desc and clean_desc.lower() != "none":
        return f"Returns:\n    {clean_desc}"
    return ""


# -------------------------------------------------
# Google style
# -------------------------------------------------
def generate_google_docstring(fn: Dict, llm: Dict) -> str:
    summary = llm.get("summary", f"Execute `{fn['name']}` operations.")
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

    lines = [summary]
    filtered_args = [a for a in fn.get("args", []) if a.get("name") not in ("self", "cls")]

    if filtered_args:
        lines.extend(["", "Parameters", "----------"])
        for arg in filtered_args:
            name = arg["name"]
            annotation = arg.get("annotation")
            desc = arg_desc.get(name, f"The {name} parameter.")
            if annotation:
                lines.append(f"{name} : {annotation}")
            else:
                lines.append(f"{name}")
            lines.append(f"    {desc}")

    returns = fn.get("returns")
    if returns and returns not in ("None", "NoneType"):
        lines.extend([
            "",
            "Returns",
            "-------",
            f"{returns}",
            f"    {return_desc or 'Result of the operation.'}"
        ])
    elif return_desc and return_desc.lower() != "none":
        lines.extend([
            "",
            "Returns",
            "-------",
            f"    {return_desc}"
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
    filtered_args = [a for a in fn.get("args", []) if a.get("name") not in ("self", "cls")]

    for arg in filtered_args:
        name = arg["name"]
        annotation = arg.get("annotation")
        desc = arg_desc.get(name, f"The {name} parameter.")
        lines.append(f":param {name}: {desc}")
        if annotation:
            lines.append(f":type {name}: {annotation}")

    returns = fn.get("returns")
    if returns and returns not in ("None", "NoneType"):
        lines.append(f":return: {return_desc or 'Result of the operation.'}")
        lines.append(f":rtype: {returns}")
    elif return_desc and return_desc.lower() != "none":
        lines.append(f":return: {return_desc}")

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
