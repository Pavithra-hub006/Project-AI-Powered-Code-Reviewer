"""
LLM integration for docstring content generation.

Responsibilities:
- Generate semantic docstring content ONLY
- Inspect full function/method source code for high accuracy
- Infer parameter and return types
- Return structured JSON
- Gracefully fall back to deterministic parsing if offline or on API errors
"""

import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage


def generate_docstring_content(fn: dict) -> dict:
    """
    Generate structured docstring content using Groq LLM with full source code context.

    Returns dict:
    {
        "summary": str,
        "args": {arg_name: description},
        "arg_types": {arg_name: inferred_type},
        "return_type": str,
        "returns": str,
        "raises": {ExceptionName: description}
    }
    """
    load_dotenv(override=True)
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set")

    all_args = [a["name"] for a in fn.get("args", [])]
    # Filter out self/cls for method documentation
    doc_arg_names = [a for a in all_args if a not in ("self", "cls")]
    annotated_args = {
        a["name"]: a.get("annotation")
        for a in fn.get("args", [])
        if a.get("annotation") and a["name"] in doc_arg_names
    }
    raises = fn.get("raises", [])
    code = fn.get("code", "").strip()
    func_name = fn.get("name", "function")
    func_type = fn.get("type", "function")
    class_name = fn.get("class_name")

    # If code is missing, construct a simple signature representation
    if not code:
        sig_args = ", ".join(all_args)
        code = f"def {func_name}({sig_args}):\n    pass"

    context_name = f"{class_name}.{func_name}" if class_name else func_name

    prompt = f"""You are an expert Python engineer generating a high-quality docstring.
Analyze the source code of `{context_name}` carefully and produce accurate documentation.

Source Code:
```python
{code}
```

Function Details:
- Name: {func_name}
- Type: {func_type}
- Parameters to document: {doc_arg_names}
- Existing type annotations: {annotated_args}
- Return annotation: {fn.get("returns") or "None specified"}
- Raised exceptions detected: {raises}

Instructions:
1. "summary": A crisp, professional 1-line summary in imperative mood starting with a base verb (e.g. Calculate, Validate, Parse, Execute, Transform, Retrieve). Never use 3rd person (no Calculates, Returns, Adds).
2. "args": A dict mapping each parameter in {doc_arg_names} to a clear description of what it represents based on how the function uses it. Do NOT include 'self' or 'cls'.
3. "arg_types": A dict mapping each parameter in {doc_arg_names} to its Python type (e.g. int, str, list[float], dict, bool, Any). Use annotations if present, or infer accurately from the code.
4. "return_type": The inferred or annotated return type (e.g. int, str, dict, list[str], None).
5. "returns": Description of what value is returned and what it signifies. If the function does not return a value or only returns None, set to "None" or empty string.
6. "raises": A dict mapping exception class names (e.g. ValueError, KeyError) to the condition under which they are raised in the code. Only include exceptions that can actually be raised. If none, return empty dict {{}}.

Respond ONLY with valid JSON in this exact structure:
{{
  "summary": "1-line summary starting with base verb.",
  "args": {{
    {", ".join(f'"{a}": "description"' for a in doc_arg_names)}
  }},
  "arg_types": {{
    {", ".join(f'"{a}": "type"' for a in doc_arg_names)}
  }},
  "return_type": "type",
  "returns": "description of returned value",
  "raises": {{}}
}}
"""

    try:
        llm = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0.2,
            api_key=api_key
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        raw_text = response.content.strip()

        # Clean markdown code fences if LLM wrapped output
        if "```" in raw_text:
            lines = raw_text.splitlines()
            cleaned_lines = []
            inside = False
            for line in lines:
                if line.strip().startswith("```"):
                    inside = not inside
                    continue
                if inside or not line.strip().startswith("```"):
                    cleaned_lines.append(line)
            raw_text = "\n".join(cleaned_lines).strip()

        data = json.loads(raw_text)
        return data

    except Exception as e:
        print(f">>> Docstring generation fallback for {context_name} due to: {e}")
        # Intelligent fallback using parsed AST metadata
        inferred_return = fn.get("returns") or ("None" if not fn.get("yields") else "Generator")
        return {
            "summary": f"Execute `{func_name}` logic.",
            "args": {a: f"Input parameter `{a}`." for a in doc_arg_names},
            "arg_types": {a: annotated_args.get(a, "Any") for a in doc_arg_names},
            "return_type": inferred_return,
            "returns": f"Result of {func_name} execution." if inferred_return != "None" else "",
            "raises": {exc: "If validation or execution fails." for exc in raises} if raises else {}
        }
