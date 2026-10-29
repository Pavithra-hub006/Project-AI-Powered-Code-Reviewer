from pathlib import Path


def apply_docstring_to_file(
    file_path: str,
    lineno: int,
    indent: int,
    docstring: str
):
    """
    Insert docstring into a Python file after a function or class definition.
    Correctly scans for the terminal colon (:) of multiline signatures before inserting.
    """
    path = Path(file_path)
    lines = path.read_text(encoding="utf-8").splitlines()

    # Find the line where the def or class signature ends (the line ending with ':')
    idx = max(0, lineno - 1)
    insert_at = lineno
    while idx < len(lines):
        code_part = lines[idx].split("#")[0].strip()
        if code_part.endswith(":"):
            insert_at = idx + 1
            break
        idx += 1

    indent_str = " " * indent
    doc_lines = [
        indent_str + line if line.strip() else ""
        for line in docstring.splitlines()
    ]

    new_lines = (
        lines[:insert_at]
        + doc_lines
        + lines[insert_at:]
    )

    path.write_text("\n".join(new_lines), encoding="utf-8")
