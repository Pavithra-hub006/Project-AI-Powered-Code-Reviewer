# core/docstring_engine/apply_docstring.py
from pathlib import Path
from typing import Optional


def apply_docstring_to_file(
    file_path: str,
    lineno: int,
    indent: int,
    docstring: str,
    body_lineno: Optional[int] = None
) -> str:
    """
    Insert docstring into a Python file cleanly inside a function, method, or class definition.

    file_path   : path to .py file
    lineno      : line number of def/class (1-based)
    indent      : indentation level (spaces)
    docstring   : triple-quoted docstring
    body_lineno : line number of first body statement (1-based)

    Returns:
        str: The updated full file content.
    """
    path = Path(file_path)
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()

    # Find the line (0-based) where the def/class signature finishes with ':'
    insert_at = lineno
    for idx in range(max(0, lineno - 1), min(len(lines), lineno + 50)):
        line_clean = lines[idx].split("#")[0].strip()
        if line_clean.endswith(":"):
            insert_at = idx + 1
            break

    # Format docstring with proper indentation
    indent_str = " " * indent
    doc_lines = [
        indent_str + dl if dl.strip() else ""
        for dl in docstring.strip().splitlines()
    ]

    # Check if there is an existing docstring right below the header
    scan_idx = insert_at
    while scan_idx < len(lines) and not lines[scan_idx].strip():
        scan_idx += 1  # skip blank lines

    if scan_idx < len(lines):
        first_line = lines[scan_idx].strip()
        if first_line.startswith(('"""', "'''")):
            # It's an existing docstring!
            if (first_line.count('"""') >= 2 and len(first_line) > 3) or (first_line.count("'''") >= 2 and len(first_line) > 3):
                # single line docstring
                lines = lines[:scan_idx] + lines[scan_idx + 1:]
            else:
                end_quote = '"""' if first_line.startswith('"""') else "'''"
                end_idx = scan_idx + 1
                while end_idx < len(lines) and end_quote not in lines[end_idx]:
                    end_idx += 1
                if end_idx < len(lines):
                    lines = lines[:scan_idx] + lines[end_idx + 1:]
            insert_at = scan_idx

    new_lines = (
        lines[:insert_at]
        + doc_lines
        + lines[insert_at:]
    )

    updated_content = "\n".join(new_lines) + "\n"
    path.write_text(updated_content, encoding="utf-8")
    return updated_content
