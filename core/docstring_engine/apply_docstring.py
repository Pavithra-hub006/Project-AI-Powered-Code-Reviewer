from pathlib import Path


def apply_docstring_to_file(
    file_path: str,
    lineno: int,
    indent: int,
    docstring: str
):
    """
    Insert docstring into a Python file after a function/class definition.

    file_path : path to .py file
    lineno    : line number of def/class (1-based)
    indent    : indentation level (spaces)
    docstring : triple-quoted docstring
    """
    path = Path(file_path)
    lines = path.read_text(encoding="utf-8").splitlines()

    insert_at = lineno  # after def line (0-based handled below)

    indent_str = " " * indent
    doc_lines = [
        indent_str + line if line else ""
        for line in docstring.splitlines()
    ]

    # Insert docstring lines
    new_lines = (
        lines[:insert_at]
        + doc_lines
        + lines[insert_at:]
    )

    path.write_text("\n".join(new_lines), encoding="utf-8")
