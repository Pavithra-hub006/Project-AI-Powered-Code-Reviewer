"""
LLM integration for docstring content generation.

Responsibilities:
- Generate semantic docstring content ONLY
- Return structured JSON
- Never format docstrings
"""

import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage


def generate_docstring_content(fn: dict) -> dict:
    """
    Generate structured docstring content using LLM.

    Returns dict:
    {
        "summary": str,
        "args": {arg_name: description},
        "returns": str,
        "raises": {ExceptionName: description}
    }
    """
    load_dotenv(override=True)
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
                api_key = st.secrets["GROQ_API_KEY"]
                os.environ["GROQ_API_KEY"] = api_key
        except Exception:
            pass

    item_type = fn.get("type", "function")
    name = fn.get("name", "unknown")
    class_name = fn.get("class_name")
    display_title = f"{class_name}.{name}" if class_name else name
    arg_names = [a["name"] for a in fn.get("args", []) if a.get("name") not in ("self", "cls")]
    raises = fn.get("raises", [])
    returns = fn.get("returns")
    source_code = fn.get("source_code", "").strip()

    if not api_key:
        return {
            "summary": f"Execute `{display_title}` operations.",
            "args": {a: f"Value for {a}." for a in arg_names},
            "returns": f"Result of {name}." if returns not in (None, "None") else "",
            "raises": {exc: "If an error occurs." for exc in raises} if raises else {}
        }

    try:
        llm = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0.2,
            api_key=api_key
        )

        code_block = source_code if source_code else f"def {name}({', '.join(arg_names)}): pass"

        prompt = f"""You are an expert Python documentation engineer.
Analyze the following Python implementation and generate clean, accurate docstring metadata in JSON format.

```python
{code_block}
```

Target: {item_type} `{display_title}`
Parameters: {arg_names}
Return Type: {returns or 'None / not annotated'}
Known Exceptions: {raises}

Output strictly valid JSON with no extra commentary, following this structure:
{{
  "summary": "1–2 sentence explanation of what this specifically does. Start with an imperative base verb (e.g. Calculate, Validate, Parse, Transform). Do not use third-person verbs like Calculates or Returns.",
  "args": {{
    // Map each parameter in {arg_names} to a clear, concise description
  }},
  "returns": "Description of return value, or empty string if None or void",
  "raises": {{
    // Map each exception in {raises} to the condition when it is raised
  }}
}}

Rules:
- Accurately describe the logic inside the provided code block.
- Do NOT document 'self' or 'cls'.
- If the item is a class or __init__, set "returns": "".
- If no exceptions are raised, set "raises": {{}}.
- If no parameters, set "args": {{}}.
- Return ONLY the JSON object.
"""

        response = llm.invoke([HumanMessage(content=prompt)])
        raw_text = response.content.strip()

        # Extract JSON object substring
        start_idx = raw_text.find("{")
        end_idx = raw_text.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            raw_text = raw_text[start_idx:end_idx + 1]

        data = json.loads(raw_text)
        return data

    except Exception as e:
        print(">>> Docstring generation fallback due to:", repr(e))
        return {
            "summary": f"Execute `{display_title}` operations.",
            "args": {a: f"Value for {a}." for a in arg_names},
            "returns": f"Result of {name}." if returns not in (None, "None") else "",
            "raises": {exc: "If an error occurs." for exc in raises} if raises else {}
        }
