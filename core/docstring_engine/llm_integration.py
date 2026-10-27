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
        raise RuntimeError("GROQ_API_KEY not set")
    print(">>> GROQ_API_KEY seen by Groq:", repr(api_key))
    llm = ChatGroq(
        model="llama-3.1-8b-instant", # openai/gpt-oss-120b, llama-3.1-8b-instant
        temperature=0.3,
        api_key=os.getenv("GROQ_API_KEY")
    )

    arg_names = [a["name"] for a in fn.get("args", [])]
    raises = fn.get("raises", [])

    prompt = f"""
Return ONLY valid JSON in this exact format:

{{
  "summary": "1–2 line description of what the function does",
  "args": {{
    "arg_name": "description"
  }},
  "returns": "description of the return value",
  "raises": {{
    "ExceptionName": "reason"
  }}
}}

Rules:
- The summary MUST be written in imperative mood
- Start with the base verb (e.g., Add, Calculate, Normalize, Convert, Fetch, Validate)
- Do NOT use third-person verbs (no Adds, Calculates, Returns)
- If the summary violates this rule, rewrite it internally before responding
- Include "raises" ONLY if exceptions actually occur
- If no exceptions occur, return "raises": {{}}
- Do NOT invent exceptions
- Do NOT include markdown
- Do NOT include triple quotes
- JSON must be strictly valid
- Be concise and professional


Function name: {fn["name"]}
Arguments: {arg_names}
Return type: {fn.get("returns")}
Known raises: {raises}
"""

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        raw_text = response.content.strip()
        if raw_text.startswith("```"):
            lines = raw_text.splitlines()
            if len(lines) >= 2 and lines[0].startswith("```"):
                lines = lines[1:]
            if len(lines) >= 1 and lines[-1].strip() == "```":
                lines = lines[:-1]
            raw_text = "\n".join(lines).strip()
        return json.loads(raw_text)
    except Exception as e:
        print(">>> Docstring generation fallback due to:", repr(e))
        return {
            "summary": f"Process `{fn['name']}` operations.",
            "args": {a: f"Value for {a}" for a in arg_names},
            "returns": f"Result of {fn['name']}",
            "raises": {exc: "If an error occurs" for exc in raises} if raises else {}
        }
