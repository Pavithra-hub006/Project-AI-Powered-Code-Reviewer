"""
AI-Powered Code Reviewer - Main Streamlit Application
------------------------------------------------------
Features:
- Single & clean Python File Upload for Streamlit Cloud deployment
- AST-based parsing of functions, classes, and inner methods
- AI docstring generation (Google, NumPy, reST) via Groq LLM
- In-place Accept & Decline buttons with instant file download
- PEP 257 validation and maintainability metrics
"""

import os
import sys
import json
import ast
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st
import pandas as pd

# ----------------------------------------------------------------------------
# 1. Environment & API Key Setup
# ----------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(ENV_PATH, override=True)

# Support Streamlit Cloud Secrets
if not os.getenv("GROQ_API_KEY"):
    try:
        if hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
            os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
    except Exception:
        pass

if not os.getenv("GROQ_API_KEY"):
    st.error(f"""
    ⚠️ **GROQ_API_KEY not found**
    
    - **Local Development:** Create a `.env` file at `{ENV_PATH}` with `GROQ_API_KEY=your_key`
    - **Streamlit Cloud Deployment:** Add `GROQ_API_KEY = "your_key"` in **App Settings → Secrets**
    """)
    st.stop()

# Add project root to sys.path
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.parser.python_parser import parse_file, parse_source
from core.docstring_engine.generator import generate_docstring
from core.docstring_engine.apply_docstring import apply_docstring_to_file
from core.reporter.coverage_reporter import compute_coverage, write_report
from core.validator.validator import run_pydocstyle

# ----------------------------------------------------------------------------
# 2. Page Configuration
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Code Reviewer by Pavithra Kotha",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------------------------------
# 3. Styling
# ----------------------------------------------------------------------------
st.markdown("""
<style>
/* Global background */
.stApp {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    background-attachment: fixed;
}

/* Main Container Card */
.main .block-container {
    background-color: #F8FAFC;
    border-radius: 18px;
    padding: 2.2rem;
    box-shadow: 0 15px 45px rgba(0,0,0,0.25);
    margin-top: 1rem;
    margin-bottom: 2rem;
}

/* Custom UI Cards */
.ui-card {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 1.5rem;
    box-shadow: 0 4px 14px rgba(0,0,0,0.06);
    border: 1px solid #E2E8F0;
    margin-bottom: 1.2rem;
}

.hero-box {
    background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%);
    border: 1px solid #C7D2FE;
    border-radius: 14px;
    padding: 1.8rem;
    margin-bottom: 1.5rem;
}

.status-badge-error {
    background-color: #FEE2E2;
    color: #991B1B;
    padding: 3px 10px;
    border-radius: 9999px;
    font-size: 0.82rem;
    font-weight: 600;
}

.status-badge-success {
    background-color: #DCFCE7;
    color: #166534;
    padding: 3px 10px;
    border-radius: 9999px;
    font-size: 0.82rem;
    font-weight: 600;
}

/* Sidebar styling */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    border-right: 2px solid #8B5CF6;
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #FFFFFF !important;
}
section[data-testid="stSidebar"] label {
    color: #FFFFFF !important;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# 4. Helper Functions
# ----------------------------------------------------------------------------
DEMO_CODE = '''import math

def calculate_average(numbers):
    total = 0
    for n in numbers:
        total += n
    if len(numbers) == 0:
        return 0
    return total / len(numbers)


def compute_tax(income: float, rate: float = 0.15) -> float:
    if income < 0:
        raise ValueError("Income cannot be negative")
    return income * rate


class DataProcessor:
    def __init__(self, name: str):
        self.name = name

    def process_records(self, records: list):
        filtered = []
        for r in records:
            if r is not None:
                filtered.append(r)
        return filtered
'''


def load_demo_file():
    """Create a sample Python file in storage/uploads and load it."""
    upload_dir = PROJECT_ROOT / "storage" / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    demo_path = upload_dir / "demo_sample.py"
    demo_path.write_text(DEMO_CODE, encoding="utf-8")
    return process_file_path(str(demo_path))


def process_file_path(path_str: str):
    """Scan and parse a single Python file using AST."""
    target_path = Path(path_str)
    if not target_path.exists():
        return None, f"File not found: {path_str}"

    try:
        parsed = parse_file(str(target_path))
    except SyntaxError as e:
        return None, f"Python Syntax Error on line {e.lineno}: {e.msg}"
    except Exception as e:
        return None, f"Failed to parse file: {e}"

    results = [parsed]
    report = compute_coverage(results)
    write_report(report, "storage/reports/docstring_coverage.json")

    st.session_state["selected_file"] = str(target_path)
    st.session_state["last_scan_results"] = results
    st.session_state["last_report"] = report
    st.session_state.pop("cached_suggestions", None)
    st.session_state.pop("cached_suggestions_key", None)
    return results, None


def process_uploaded_file(uploaded_file):
    """Save an uploaded Python file to storage/uploads and parse it."""
    if not uploaded_file:
        return None, "No file provided"
    upload_dir = PROJECT_ROOT / "storage" / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_name = Path(uploaded_file.name).name
    if not safe_name.endswith(".py"):
        safe_name += ".py"

    saved_path = upload_dir / safe_name
    saved_path.write_bytes(uploaded_file.getbuffer())
    return process_file_path(str(saved_path))


def collect_missing_items(results: list) -> list:
    """Collect all functions, classes, and class methods missing docstrings."""
    missing = []
    if not results:
        return missing

    for r in results:
        fp = r.get("path") or r.get("file_path", "")
        # Top-level functions
        for fn in r.get("functions", []):
            if not fn.get("has_docstring"):
                missing.append({
                    "id": f"func_{fn['name']}_{fn['lineno']}",
                    "kind": "Function",
                    "display_name": f"{fn['name']}()",
                    "name": fn["name"],
                    "class_name": None,
                    "type": "function",
                    "lineno": fn["lineno"],
                    "body_lineno": fn.get("body_lineno"),
                    "indent": fn.get("indent", 4),
                    "file": fp,
                    "existing_doc": fn.get("docstring"),
                    "source_code": fn.get("source_code", ""),
                    "raw_meta": fn
                })

        # Classes and inner methods
        for cls in r.get("classes", []):
            # Class docstring
            if not cls.get("has_docstring"):
                missing.append({
                    "id": f"cls_{cls['name']}_{cls['lineno']}",
                    "kind": "Class",
                    "display_name": f"class {cls['name']}",
                    "name": cls["name"],
                    "class_name": cls["name"],
                    "type": "class",
                    "lineno": cls["lineno"],
                    "body_lineno": cls.get("body_lineno"),
                    "indent": cls.get("indent", 4),
                    "file": fp,
                    "existing_doc": cls.get("docstring"),
                    "source_code": cls.get("source_code", ""),
                    "raw_meta": cls
                })

            # Methods inside class
            for m in cls.get("methods", []):
                if not m.get("has_docstring"):
                    missing.append({
                        "id": f"method_{cls['name']}_{m['name']}_{m['lineno']}",
                        "kind": "Method",
                        "display_name": f"{cls['name']}.{m['name']}()",
                        "name": m["name"],
                        "class_name": cls["name"],
                        "type": "method",
                        "lineno": m["lineno"],
                        "body_lineno": m.get("body_lineno"),
                        "indent": m.get("indent", 8),
                        "file": fp,
                        "existing_doc": m.get("docstring"),
                        "source_code": m.get("source_code", ""),
                        "raw_meta": m
                    })

    return missing


def compute_code_metrics(file_path: str):
    """Compute complexity and maintainability index for a python file."""
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()

    metrics = []
    try:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity = 1
                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try,
                                          ast.ExceptHandler, ast.ListComp, ast.DictComp,
                                          ast.SetComp, ast.GeneratorExp, ast.IfExp)):
                        complexity += 1
                metrics.append({
                    "name": node.name,
                    "type": "Function",
                    "line": node.lineno,
                    "complexity": complexity
                })
            elif isinstance(node, ast.ClassDef):
                metrics.append({
                    "name": node.name,
                    "type": "Class",
                    "line": node.lineno,
                    "complexity": max(1, len(node.body))
                })
    except Exception:
        pass

    total_c = sum(m["complexity"] for m in metrics)
    maintainability_index = max(15, min(100, 100 - (total_c * 2))) if metrics else 100
    return maintainability_index, metrics


def classify_issues(issues):
    """Classify validation issues into errors and warnings."""
    errors = []
    warnings = []
    for issue in issues:
        text = str(issue)
        if "D1" in text:
            errors.append(issue)
        else:
            warnings.append(issue)
    return errors, warnings


# ----------------------------------------------------------------------------
# 5. Session State Initialization
# ----------------------------------------------------------------------------
if "view" not in st.session_state:
    st.session_state.view = "📊 Dashboard"

if "selected_file" not in st.session_state:
    st.session_state.selected_file = None

if "last_scan_results" not in st.session_state:
    st.session_state.last_scan_results = None

if "last_report" not in st.session_state:
    st.session_state.last_report = None

if "rejected_items" not in st.session_state:
    st.session_state.rejected_items = set()

# ----------------------------------------------------------------------------
# 6. Sidebar Controls
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🤖 AI Code Reviewer")
    st.caption("Automated AST Analysis & LLM Docstring Engine")
    st.divider()

    st.markdown("### 📤 Upload Python File")
    uploaded_file = st.file_uploader(
        "Choose a Python file (.py)",
        type=["py"],
        key="main_file_uploader",
        help="Upload any Python source file to analyze and generate docstrings."
    )

    if uploaded_file is not None:
        if st.session_state.get("current_uploaded_filename") != uploaded_file.name:
            with st.spinner(f"Analyzing {uploaded_file.name}..."):
                res, err = process_uploaded_file(uploaded_file)
                if err:
                    st.error(f"❌ {err}")
                else:
                    st.session_state["current_uploaded_filename"] = uploaded_file.name
                    st.session_state.rejected_items = set()
                    st.success(f"✅ Loaded {uploaded_file.name}")
                    st.rerun()

    doc_style = st.selectbox(
        "📝 Docstring Style",
        ["google", "numpy", "rest"],
        help="Choose the docstring format to generate."
    )

    # Demo fallback button
    if not st.session_state.get("selected_file"):
        if st.button("⚡ Try with Demo Code", use_container_width=True):
            with st.spinner("Loading demo code..."):
                load_demo_file()
                st.session_state["current_uploaded_filename"] = "demo_sample.py"
                st.session_state.rejected_items = set()
                st.rerun()

    st.divider()

    # Active File Summary if loaded
    selected_file = st.session_state.get("selected_file")
    if selected_file and Path(selected_file).exists():
        file_name = Path(selected_file).name
        rep = st.session_state.get("last_report")
        cov = rep["summary"]["coverage_percent"] if rep else 0.0

        st.markdown(f"**Current File:** `{file_name}`")
        if cov >= 80:
            st.markdown(f"<span class='status-badge-success'>🟢 {cov}% Documented</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"<span class='status-badge-error'>🔴 {cov}% Documented</span>", unsafe_allow_html=True)

        with open(selected_file, "r", encoding="utf-8") as f:
            code_text = f.read()

        st.download_button(
            label="📥 Download Python File",
            data=code_text,
            file_name=file_name,
            mime="text/x-python",
            use_container_width=True
        )

    st.divider()

    # Navigation Buttons
    st.markdown("### 🧭 Navigation")
    for nav_label in ["📊 Dashboard", "🧩 Docstrings", "🧪 Validation", "📈 Coverage"]:
        if st.button(nav_label, use_container_width=True, key=f"nav_{nav_label}"):
            st.session_state.view = nav_label
            st.rerun()

    view = st.session_state.view

# ----------------------------------------------------------------------------
# 7. Header
# ----------------------------------------------------------------------------
st.markdown('<h1 style="color: #1E293B; font-size: 2.3rem; font-weight: 800; margin-bottom: 0.2rem;">🤖 AI-Powered Code Reviewer</h1>', unsafe_allow_html=True)
st.caption("Engineered by Pavithra Kotha — Automated AST Code Intelligence & Docstring Generation")
st.divider()

results = st.session_state.get("last_scan_results")
report = st.session_state.get("last_report")
selected_file = st.session_state.get("selected_file")

# ----------------------------------------------------------------------------
# 8. View: DASHBOARD
# ----------------------------------------------------------------------------
if view == "📊 Dashboard":
    if not selected_file or not results:
        st.markdown("""
        <div class="hero-box">
            <h2 style="color: #3730A3; margin-top: 0;">👋 Welcome to AI-Powered Code Reviewer</h2>
            <p style="color: #4338CA; font-size: 1.05rem;">
                Review your Python code quality, detect missing docstrings across functions, classes, and methods, 
                and automatically generate Google, NumPy, or reST-compliant documentation with Llama 3.1.
            </p>
        </div>
        """, unsafe_allow_html=True)

        dash_col1, dash_col2 = st.columns(2)
        with dash_col1:
            st.markdown('<div class="ui-card">', unsafe_allow_html=True)
            st.markdown("### 📤 Upload Your Python File")
            st.write("Upload any `.py` source code file to begin analysis.")
            quick_upload = st.file_uploader("Select .py file", type=["py"], key="dash_hero_uploader")
            if quick_upload is not None:
                with st.spinner(f"Analyzing {quick_upload.name}..."):
                    process_uploaded_file(quick_upload)
                    st.session_state["current_uploaded_filename"] = quick_upload.name
                    st.session_state.rejected_items = set()
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        with dash_col2:
            st.markdown('<div class="ui-card">', unsafe_allow_html=True)
            st.markdown("### ⚡ Test with Demo Code")
            st.write("Click below to test the analyzer with a pre-configured sample Python file.")
            if st.button("🚀 Load Sample Python File", use_container_width=True, key="dash_load_demo"):
                with st.spinner("Loading demo file..."):
                    load_demo_file()
                    st.session_state["current_uploaded_filename"] = "demo_sample.py"
                    st.session_state.rejected_items = set()
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    else:
        summary = report["summary"] if report else {"coverage_percent": 0, "total_items": 0, "total_docs": 0}
        cov_pct = summary.get("coverage_percent", 0.0)
        tot_items = summary.get("total_items", 0)
        doc_count = summary.get("total_docs", 0)
        missing_count = tot_items - doc_count

        # Overview Metrics Cards
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📄 File Name", Path(selected_file).name)
        col2.metric("📦 Total Items", tot_items, help="All functions, classes, and methods parsed by AST")
        col3.metric("✅ Documented", f"{doc_count} / {tot_items}")
        col4.metric("📊 Coverage %", f"{cov_pct}%")

        st.progress(cov_pct / 100.0)

        # Quick Callout to Action
        if missing_count > 0:
            st.warning(f"⚠️ **{missing_count} item(s) are missing docstrings!** Click **🧩 Docstrings** in the sidebar or below to review and generate AI docstrings.")
            if st.button("👉 Go to Docstring Review & Generation", use_container_width=True):
                st.session_state.view = "🧩 Docstrings"
                st.rerun()
        else:
            st.success("🎉 All functions, classes, and methods have complete docstrings!")

        st.divider()

        # AST Parsing Structure
        st.markdown("### 🧠 AST Code Structure")
        parsed = results[0]
        structure_lines = [f"# File: {Path(parsed['path']).name}", ""]

        for fn in parsed.get("functions", []):
            args_str = ", ".join(a["name"] for a in fn.get("args", []))
            doc_status = "✅ Has Docstring" if fn["has_docstring"] else "❌ Missing Docstring"
            structure_lines.append(f"def {fn['name']}({args_str}):  # {doc_status}")

        for cls in parsed.get("classes", []):
            c_status = "✅ Has Docstring" if cls["has_docstring"] else "❌ Missing Docstring"
            structure_lines.append(f"\nclass {cls['name']}:  # {c_status}")
            for m in cls.get("methods", []):
                m_args = ", ".join(a["name"] for a in m.get("args", []))
                m_status = "✅ Has Docstring" if m["has_docstring"] else "❌ Missing Docstring"
                structure_lines.append(f"    def {m['name']}({m_args}):  # {m_status}")

        st.code("\n".join(structure_lines), language="python")

        st.divider()

        # Code Complexity & Quality
        st.markdown("### 📐 Code Quality & Complexity")
        mi, metrics = compute_code_metrics(selected_file)
        col_m1, col_m2 = st.columns([1, 3])
        col_m1.metric("🎯 Maintainability Index", f"{round(mi, 1)} / 100")
        with col_m2:
            if metrics:
                st.dataframe(pd.DataFrame(metrics), use_container_width=True)

# ----------------------------------------------------------------------------
# 9. View: DOCSTRINGS
# ----------------------------------------------------------------------------
elif view == "🧩 Docstrings":
    st.markdown("## 🧩 Docstring Review & In-Place Code Generation")

    if not selected_file or not results:
        st.info("ℹ️ Please upload a Python file in the sidebar to review and generate docstrings.")
    else:
        raw_missing = collect_missing_items(results)
        # Filter out rejected items
        missing_items = [it for it in raw_missing if it["id"] not in st.session_state.rejected_items]

        if not missing_items:
            st.success("🎉 **All functions, classes, and methods are fully documented!**")
            with open(selected_file, "r", encoding="utf-8") as f:
                full_code = f.read()

            st.download_button(
                label="📥 Download Updated Python File",
                data=full_code,
                file_name=Path(selected_file).name,
                mime="text/x-python",
                use_container_width=True
            )
            with st.expander("👀 View Complete Documented Source Code"):
                st.code(full_code, language="python")
        else:
            # Cache docstrings by file mtime and style
            mtime = os.path.getmtime(selected_file)
            cache_key = f"{doc_style}_{selected_file}_{mtime}_{len(missing_items)}"

            if st.session_state.get("cached_suggestions_key") != cache_key:
                with st.spinner("🤖 Analyzing code & generating AI docstrings with Groq Llama 3.1..."):
                    generated_map = {}
                    for it in missing_items:
                        try:
                            generated_map[it["id"]] = generate_docstring(it["raw_meta"], style=doc_style)
                        except Exception as e:
                            generated_map[it["id"]] = f'"""\nExecute `{it["name"]}` operations.\n"""'
                    st.session_state["cached_suggestions"] = generated_map
                    st.session_state["cached_suggestions_key"] = cache_key

            cached_docs = st.session_state.get("cached_suggestions", {})

            # Attach generated docstrings to items
            for it in missing_items:
                it["generated_doc"] = cached_docs.get(it["id"], f'"""\nExecute `{it["name"]}` operations.\n"""')

            # Top Toolbar
            col_bar1, col_bar2, col_bar3 = st.columns([2, 1, 1])
            with col_bar1:
                st.markdown(f"**Found {len(missing_items)} item(s) missing documentation** (Style: `{doc_style.upper()}`)")
            with col_bar2:
                if st.button("✨ Accept All Docstrings", use_container_width=True, key="btn_accept_all"):
                    with st.spinner("Applying all docstrings to code..."):
                        # Sort items by lineno descending so line shifts do not disrupt subsequent insertions
                        sorted_items = sorted(missing_items, key=lambda x: x["lineno"], reverse=True)
                        for it in sorted_items:
                            apply_docstring_to_file(
                                file_path=it["file"],
                                lineno=it["lineno"],
                                indent=it["indent"],
                                docstring=it["generated_doc"],
                                body_lineno=it.get("body_lineno")
                            )
                        process_file_path(selected_file)
                        st.success(f"✅ Successfully applied all {len(sorted_items)} docstrings!")
                        st.rerun()
            with col_bar3:
                with open(selected_file, "r", encoding="utf-8") as f:
                    current_code = f.read()
                st.download_button(
                    label="📥 Download File",
                    data=current_code,
                    file_name=Path(selected_file).name,
                    mime="text/x-python",
                    use_container_width=True
                )

            search_query = st.text_input("🔍 Filter functions or classes", placeholder="Type to search...")

            st.divider()

            # Render Each Missing Item Card
            for idx, it in enumerate(missing_items):
                if search_query and search_query.lower() not in it["display_name"].lower():
                    continue

                st.markdown('<div class="ui-card">', unsafe_allow_html=True)
                title_col, badge_col = st.columns([3, 1])
                with title_col:
                    st.markdown(f"#### `{it['display_name']}`")
                with badge_col:
                    st.markdown(f"<span class='status-badge-error'>Missing Docstring</span>", unsafe_allow_html=True)

                col_left, col_right = st.columns(2)
                with col_left:
                    st.markdown("**Original Implementation**")
                    if it.get("source_code"):
                        st.code(it["source_code"], language="python")
                    else:
                        st.code(f"Line {it['lineno']}: {it['name']}", language="python")

                with col_right:
                    st.markdown(f"**AI Suggested Docstring ({doc_style})**")
                    st.code(it["generated_doc"], language="python")

                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("✅ Accept & Insert into Code", key=f"btn_acc_{it['id']}", use_container_width=True):
                        try:
                            apply_docstring_to_file(
                                file_path=it["file"],
                                lineno=it["lineno"],
                                indent=it["indent"],
                                docstring=it["generated_doc"],
                                body_lineno=it.get("body_lineno")
                            )
                            process_file_path(selected_file)
                            st.success(f"✅ Docstring inserted for {it['display_name']}!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to apply: {e}")

                with btn_col2:
                    if st.button("❌ Decline", key=f"btn_rej_{it['id']}", use_container_width=True):
                        st.session_state.rejected_items.add(it["id"])
                        st.rerun()

                st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# 10. View: VALIDATION
# ----------------------------------------------------------------------------
elif view == "🧪 Validation":
    st.markdown("## 🧪 PEP 257 Docstring Validation")

    if not selected_file:
        st.info("ℹ️ Please upload a Python file in the sidebar to run validation.")
    else:
        st.write(f"Validating **{Path(selected_file).name}** using `pydocstyle` standards.")

        if st.button("▶️ Run PEP 257 Validation", use_container_width=True, key="btn_run_val"):
            with st.spinner("Running pydocstyle checks..."):
                st.session_state["validation_result"] = run_pydocstyle(selected_file)

        result = st.session_state.get("validation_result")
        if result is not None:
            issues = result.issues if hasattr(result, "issues") else list(result)
            errors, warnings = classify_issues(issues)

            val_col1, val_col2, val_col3 = st.columns(3)
            val_col1.metric("🔴 Missing Docstrings", len(errors))
            val_col2.metric("🟡 Style Warnings", len(warnings))
            val_col3.metric("Status", "✅ Passed" if result.passed else "❌ Issues Found")

            if errors:
                st.markdown("### 🔴 Missing Docstring Violations")
                for err in errors:
                    st.error(str(err))

            if warnings:
                st.markdown("### 🟡 Style & Formatting Violations")
                for w in warnings:
                    st.warning(str(w))

            if not errors and not warnings:
                st.success("🎉 Complies 100% with PEP 257 standards!")

# ----------------------------------------------------------------------------
# 11. View: COVERAGE
# ----------------------------------------------------------------------------
elif view == "📈 Coverage":
    st.markdown("## 📈 Coverage & Quality Metrics")

    if not selected_file or not report:
        st.info("ℹ️ Please upload a Python file in the sidebar to view coverage.")
    else:
        summary = report["summary"]
        cov_pct = summary.get("coverage_percent", 0.0)

        c1, c2, c3 = st.columns(3)
        c1.metric("📦 Total Items", summary.get("total_items", 0))
        c2.metric("✅ Documented Items", summary.get("total_docs", 0))
        c3.metric("📊 Coverage", f"{cov_pct}%")

        st.progress(cov_pct / 100.0)
        st.divider()

        st.markdown("### 🔍 Item Breakdown")
        file_meta = report.get("files", {}).get(selected_file, {})
        items = file_meta.get("items", [])
        if items:
            df = pd.DataFrame(items)
            df["Status"] = df["has_doc"].apply(lambda x: "✅ Documented" if x else "❌ Missing")
            st.dataframe(df[["type", "name", "lineno", "Status"]], use_container_width=True)
