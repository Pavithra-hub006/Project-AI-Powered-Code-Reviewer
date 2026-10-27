"""
AI-Powered Code Reviewer - Main Streamlit Application
------------------------------------------------------
Refactored version with:
- Consolidated duplicate code
- Graceful .env loading
- Fixed logic flow
- Enhanced modern UI
"""

import os
import sys
import json
import ast
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(ENV_PATH, override=True)

# Support Streamlit Cloud Secrets (for deployment)
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
    - **Streamlit Cloud Deployment:** Add `GROQ_API_KEY = \"your_key\"` in **App Settings → Secrets**
    """)
    st.stop()

# Add project root to path
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dashboard_ui.dashboard import load_pytest_results, filter_functions
from core.parser.python_parser import parse_path, parse_file
from core.docstring_engine.generator import generate_docstring
from core.reporter.coverage_reporter import compute_coverage, write_report
from core.docstring_engine.apply_docstring import apply_docstring_to_file
from core.validator.validator import run_pydocstyle

st.set_page_config(
    page_title="AI Code Reviewer by Pavithra Kotha",
    layout="wide",
    initial_sidebar_state="expanded"
)
def load_pytest_results_local():
    """Load pytest results from local storage."""
    path = Path("storage/reports/pytest_results.json")
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def summarize_tests_by_file(pytest_data):
    """
    Summarize pytest results by file.
    
    Returns:
        dict: {
            "test_file.py": {
                "total": int,
                "passed": int,
                "failed": int,
                "errors": [str, str, ...]
            }
        }
    """
    summary = {}

    for test in pytest_data.get("tests", []):
        nodeid = test.get("nodeid", "")
        outcome = test.get("outcome", "")
        longrepr = test.get("longrepr", "")

        file_name = nodeid.split("::")[0]

        if file_name not in summary:
            summary[file_name] = {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "errors": []
            }

        summary[file_name]["total"] += 1

        if outcome == "passed":
            summary[file_name]["passed"] += 1
        elif outcome == "failed":
            summary[file_name]["failed"] += 1
            summary[file_name]["errors"].append(longrepr)

    return summary


def build_export_rows(results):
    """Build export rows for JSON/CSV download."""
    rows = []

    for r in results:
        file_name = Path(r["path"]).name

        # Functions
        for fn in r.get("functions", []):
            args = ", ".join(a["name"] for a in fn.get("args", []))
            rows.append({
                "File": file_name,
                "Type": "Function",
                "Name": fn["name"],
                "Arguments": args,
                "Docstring": "Present" if fn["has_docstring"] else "Missing"
            })

        # Classes
        for cls in r.get("classes", []):
            rows.append({
                "File": file_name,
                "Type": "Class",
                "Name": cls["name"],
                "Arguments": "",
                "Docstring": "Present" if cls["has_docstring"] else "Missing"
            })

    return rows


def classify_issues(issues):
    """
    Classify validation issues into errors and warnings.
    
    Args:
        issues: List of issue tuples from pydocstyle
        
    Returns:
        tuple: (errors, warnings)
    """
    warnings = []
    errors = []

    for issue in issues:
        text = " ".join(issue)

        if "D1" in text:  # Missing docstrings
            errors.append(issue)
        elif "D2" in text:  # Formatting issues
            warnings.append(issue)
        else:
            warnings.append(issue)

    return errors, warnings


def compute_code_metrics(file_path):
    """
    Compute basic code metrics for a file.
    
    Returns:
        tuple: (maintainability_index, metrics_list)
    """
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())

    metrics = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            metrics.append({
                "name": node.name,
                "type": "Class" if isinstance(node, ast.ClassDef) else "Function",
                "line": node.lineno,
                "complexity": len(node.body)
            })

    maintainability_index = max(0, 100 - sum(m["complexity"] for m in metrics))
    return maintainability_index, metrics

st.markdown("""
<style>
/* ============================================
   GLOBAL THEME
   ============================================ */
.stApp {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    background-attachment: fixed;
}

/* ============================================
   MAIN CONTENT AREA
   ============================================ */
.main .block-container {
    background-color: #F7F9FC;
    border-radius: 20px;
    padding: 2rem;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}

/* ============================================
   SIDEBAR STYLING
   ============================================ */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    border-right: 3px solid #8B5CF6;
    box-shadow: 4px 0 20px rgba(102, 126, 234, 0.3);
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #FFFFFF !important;
    font-weight: 700;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
}

section[data-testid="stSidebar"] label {
    color: #FFFFFF !important;
    font-weight: 600;
    text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1);
}

section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] textarea {
    background-color: rgba(255, 255, 255, 0.95) !important;
    color: #1E293B !important;
    border-radius: 8px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    font-weight: 500;
}

section[data-testid="stSidebar"] div[data-baseweb="select"] {
    background-color: rgba(255, 255, 255, 0.95) !important;
    border-radius: 8px;
    border: 2px solid rgba(255, 255, 255, 0.3);
}

section[data-testid="stSidebar"] div[data-baseweb="select"] span {
    color: #1E293B !important;
    font-weight: 500;
}

/* Sidebar buttons with glass effect */
section[data-testid="stSidebar"] button {
    background: rgba(255, 255, 255, 0.2) !important;
    color: #FFFFFF !important;
    border: 2px solid rgba(255, 255, 255, 0.3) !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
    transition: all 0.3s ease !important;
    backdrop-filter: blur(10px);
}

section[data-testid="stSidebar"] button:hover {
    background: rgba(255, 255, 255, 0.3) !important;
    border: 2px solid rgba(255, 255, 255, 0.5) !important;
    transform: translateX(5px);
    box-shadow: 0 4px 15px rgba(255, 255, 255, 0.3);
}

/* Sidebar dividers */
section[data-testid="stSidebar"] hr {
    border-color: rgba(255, 255, 255, 0.3) !important;
}

/* Sidebar markdown text */
section[data-testid="stSidebar"] p {
    color: #FFFFFF !important;
}

/* Progress bar in sidebar */
section[data-testid="stSidebar"] [data-testid="stProgress"] > div {
    background-color: rgba(255, 255, 255, 0.3) !important;
}

section[data-testid="stSidebar"] [data-testid="stProgress"] > div > div {
    background-color: #FFFFFF !important;
}

/* ============================================
   UI CARDS
   ============================================ */
.ui-card {
    background: white;
    border-radius: 14px;
    padding: 20px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.08);
    margin-bottom: 16px;
    border-left: 4px solid #667eea;
}

/* ============================================
   STATUS BADGES
   ============================================ */
.status-ok {
    color: #16A34A;
    font-weight: 700;
    background: #DCFCE7;
    padding: 4px 12px;
    border-radius: 6px;
}

.status-error {
    color: #DC2626;
    font-weight: 700;
    background: #FEE2E2;
    padding: 4px 12px;
    border-radius: 6px;
}

.status-warn {
    color: #D97706;
    font-weight: 700;
    background: #FEF3C7;
    padding: 4px 12px;
    border-radius: 6px;
}

/* ============================================
   BUTTONS
   ============================================ */
.stButton button {
    border-radius: 10px;
    padding: 0.5rem 1.2rem;
    font-weight: 600;
    transition: all 0.3s ease;
}

.stButton button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0,0,0,0.15);
}

/* ============================================
   CODE BLOCKS
   ============================================ */
code, pre {
    background-color: #1E293B !important;
    color: #E2E8F0 !important;
    border-radius: 10px;
    padding: 1rem;
}

/* ============================================
   METRICS
   ============================================ */
[data-testid="stMetricValue"] {
    font-size: 2rem;
    font-weight: 700;
    color: #667eea;
}

/* ============================================
   HEADER GRADIENT
   ============================================ */
.gradient-header {
    color: #1E293B;
    font-size: 2.5rem;
    font-weight: 800;
    margin-bottom: 1rem;
    text-shadow: 2px 2px 4px rgba(255,255,255,0.8);
}

</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if "active_feature" not in st.session_state:
    st.session_state.active_feature = None

if "last_scan_results" not in st.session_state:
    st.session_state.last_scan_results = None

if "last_report" not in st.session_state:
    st.session_state.last_report = None

if "view" not in st.session_state:
    st.session_state.view = "📊 Dashboard"

if "selected_file" not in st.session_state:
    st.session_state.selected_file = None

# ============================================================================
# HEADER
# ============================================================================

st.markdown('<h1 class="gradient-header">🤖 AI-Powered Code Reviewer</h1>', unsafe_allow_html=True)
st.markdown("**by Pavithra Kotha**")
st.divider()

# ============================================================================
# SIDEBAR - PROJECT CONTROLS
# ============================================================================

with st.sidebar:
    st.markdown("## 🔍 Project Control")

    scan_path = st.text_input("📁 Scan Path", value="examples/")
    doc_style = st.selectbox(
        "📝 Docstring Style",
        ["google", "numpy", "rest"]
    )

    if st.button("🚀 Scan Project", use_container_width=True):
        with st.spinner("Scanning project..."):
            try:
                results = parse_path(scan_path)
                report = compute_coverage(results)
                write_report(report, "storage/reports/docstring_coverage.json")

                st.session_state["last_scan_results"] = results
                st.session_state["last_report"] = report
                st.session_state.pop("cached_suggestions_key", None)

                if results:
                    st.session_state["selected_file"] = str(results[0]["path"])

                st.success(f"✅ Scanned {len(results)} file(s)")
            except Exception as e:
                st.error(f"❌ Scan failed: {e}")

    st.divider()

    # ========================================================================
    # NAVIGATION
    # ========================================================================

    st.markdown("## 🧭 Navigation")

    def nav_button(label):
        if st.button(label, use_container_width=True):
            st.session_state.view = label

    nav_button("📊 Dashboard")
    nav_button("🧩 Docstrings")
    nav_button("🧪 Validation")
    nav_button("📈 Coverage")

    view = st.session_state.view

    st.divider()

    # ========================================================================
    # FILE BROWSER
    # ========================================================================

    st.markdown("## 📁 Files")
    report = st.session_state.get("last_report")
    
    if report:
        files = report.get("files", {})
        
        for fp, meta in sorted(files.items(), key=lambda x: x[1].get("coverage_percent", 0)):
            short_name = Path(fp).name
            coverage_pct = meta.get("coverage_percent", 0.0)
            
            # Coverage badge
            if coverage_pct >= 90:
                badge = "🟢"
            elif coverage_pct >= 70:
                badge = "🟡"
            else:
                badge = "🔴"
            
            if st.button(f"{badge} {short_name} ({coverage_pct}%)", key=f"file-{fp}", use_container_width=True):
                st.session_state["selected_file"] = fp
    else:
        st.info("No files scanned yet")

# ============================================================================
# MAIN CONTENT AREA
# ============================================================================

results = st.session_state.get("last_scan_results")
report = st.session_state.get("last_report")

# ============================================================================
# VIEW: DASHBOARD
# ============================================================================

if view == "📊 Dashboard":
    st.markdown("## 📊 Project Dashboard")

    if not report:
        st.info("👆 Click **Scan Project** in the sidebar to begin")
    else:
        summary = report["summary"]

        # Metrics row
        col1, col2, col3 = st.columns(3)
        col1.metric("📁 Files Scanned", len(report.get("files", {})))
        col2.metric("📊 Coverage", f"{summary.get('coverage_percent', 0)}%")
        col3.metric("🔍 Total Items", summary.get("total_items", 0))

        st.progress(summary.get("coverage_percent", 0) / 100)

        st.divider()

        # AST Parsing Output
        st.markdown("### 🧠 AST Parsing Output")
        selected = st.session_state.get("selected_file")
        
        if selected and results:
            parsed = None
            for r in results:
                if str(r.get("path")) == selected:
                    parsed = r
                    break

            if not parsed:
                st.warning("Selected file not found in scan results")
            else:
                txt_lines = []
                txt_lines.append(f"# File: {Path(parsed['path']).name}")
                txt_lines.append(f"Module docstring: {bool(parsed.get('module_docstring'))}")
                txt_lines.append("")

                for fn in parsed.get("functions", []):
                    args = ", ".join(a["name"] for a in fn.get("args", []))
                    txt_lines.append(
                        f"Function: {fn['name']}({args}) | doc: {fn['has_docstring']}"
                    )

                for cls in parsed.get("classes", []):
                    txt_lines.append(
                        f"Class: {cls['name']} | doc: {cls['has_docstring']}"
                    )
                    for m in cls.get("methods", []):
                        txt_lines.append(
                            f"  Method: {m['name']} | doc: {m['has_docstring']}"
                        )

                st.code("\n".join(txt_lines), language="python")
        else:
            st.info("Select a file from the sidebar to see AST output")

        st.divider()

        # Test Results
        st.markdown("## 🧪 Test Results")
        pytest_data = load_pytest_results()

        if not pytest_data:
            st.info("Run pytest with --json-report to see test results")
        else:
            file_summary = summarize_tests_by_file(pytest_data)

            rows = []
            for file, stats in file_summary.items():
                rows.append({
                    "File": Path(file).stem,
                    "Passed": stats["passed"],
                    "Failed": stats["failed"]
                })

            df = pd.DataFrame(rows).set_index("File")
            st.bar_chart(df)

            # Error details
            st.markdown("### ❌ Error Details")
            for file, stats in file_summary.items():
                if stats["failed"] > 0:
                    with st.expander(f"📄 {file} — ❌ {stats['failed']} failed"):
                        for test in pytest_data.get("tests", []):
                            if (
                                test.get("outcome") == "failed"
                                and test.get("nodeid", "").startswith(file)
                            ):
                                error_text = (
                                    test.get("longreprtext")
                                    or test.get("longrepr")
                                    or test.get("call", {}).get("crash", {}).get("message")
                                    or "No error details provided"
                                )
                                st.code(error_text)

        st.divider()

        # Enhanced UI Features
        st.markdown("### ✨ Enhanced Features")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("🔍\nAdvanced\nFilters", key="feat_filters", use_container_width=True):
                st.session_state.active_feature = "filters"

        with col2:
            if st.button("🔎\nSearch\nFunctions", key="feat_search", use_container_width=True):
                st.session_state.active_feature = "search"

        with col3:
            if st.button("📤\nExport\nData", key="feat_export", use_container_width=True):
                st.session_state.active_feature = "export"

        with col4:
            if st.button("ℹ️\nHelp &\nTips", key="feat_help", use_container_width=True):
                st.session_state.active_feature = "help"

        # Feature content
        if st.session_state.active_feature == "filters":
            st.markdown("## 🔎 Advanced Filters")

            status_filter = st.selectbox(
                "Documentation status",
                ["All", "Missing Docstring"]
            )

            rows = []
            if results:
                for r in results:
                    for fn in r.get("functions", []):
                        has_doc = fn.get("has_docstring", False)

                        if status_filter == "Missing Docstring" and has_doc:
                            continue

                        rows.append({
                            "File": Path(r["path"]).name,
                            "Function": fn["name"],
                            "Docstring": "✅ Yes" if has_doc else "❌ No"
                        })

            if rows:
                st.table(rows)
            else:
                st.success("All functions have docstrings!")

        elif st.session_state.active_feature == "search":
            st.markdown("## 🔎 Search Functions")

            query = st.text_input(
                "Search by name",
                placeholder="Type function or class name..."
            ).strip().lower()

            rows = []

            if query and results:
                for r in results:
                    file_name = Path(r["path"]).name

                    for fn in r.get("functions", []):
                        if query in fn["name"].lower():
                            rows.append({
                                "File": file_name,
                                "Name": fn["name"],
                                "Type": "Function",
                                "Docstring": "✅ Present" if fn["has_docstring"] else "❌ Missing"
                            })

                    for cls in r.get("classes", []):
                        if query in cls["name"].lower():
                            rows.append({
                                "File": file_name,
                                "Name": cls["name"],
                                "Type": "Class",
                                "Docstring": "✅ Present" if cls["has_docstring"] else "❌ Missing"
                            })

            if query:
                if rows:
                    st.table(rows)
                else:
                    st.info("No matches found")

        elif st.session_state.active_feature == "export":
            st.markdown("## 📤 Export Data")

            if results:
                rows = build_export_rows(results)

                total = len(rows)
                documented = sum(1 for r in rows if r["Docstring"] == "Present")

                st.info(f"📊 **{total}** items | **{documented}** documented")

                # JSON export
                json_data = json.dumps(rows, indent=2)
                st.download_button(
                    label="📥 Download JSON",
                    data=json_data,
                    file_name="docstring_report.json",
                    mime="application/json"
                )

                # CSV export
                df = pd.DataFrame(rows)
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_data,
                    file_name="docstring_report.csv",
                    mime="text/csv"
                )
            else:
                st.info("No data to export. Run a scan first.")

        elif st.session_state.active_feature == "help":
            st.markdown("## ℹ️ Help & Tips")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("""
                <div class="ui-card">
                <h4>📊 Coverage Metrics</h4>
                <ul>
                <li><b>Coverage %</b> = (Documented / Total) × 100</li>
                <li>🟢 Green: ≥ 90%</li>
                <li>🟡 Yellow: 70–89%</li>
                <li>🔴 Red: &lt; 70%</li>
                </ul>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown("""
                <div class="ui-card">
                <h4>📄 Docstring Styles</h4>
                <ul>
                <li><b>Google</b>: Args, Returns, Raises</li>
                <li><b>NumPy</b>: Parameters / Returns</li>
                <li><b>reST</b>: :param, :return:</li>
                </ul>
                </div>
                """, unsafe_allow_html=True)

# ============================================================================
# VIEW: DOCSTRINGS
# ============================================================================

elif view == "🧩 Docstrings":
    st.markdown("## 🧩 Docstring Review")

    if not results:
        st.info("ℹ️ Run a scan first to review and generate docstrings.")
        if st.button("🚀 Scan Project Now", use_container_width=True):
            with st.spinner("Scanning project..."):
                try:
                    results = parse_path(scan_path)
                    report = compute_coverage(results)
                    write_report(report, "storage/reports/docstring_coverage.json")
                    st.session_state["last_scan_results"] = results
                    st.session_state["last_report"] = report
                    st.session_state.pop("cached_suggestions_key", None)
                    if results:
                        st.session_state["selected_file"] = str(results[0]["path"])
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Scan failed: {e}")
    else:
        # Build suggestions (cached to avoid repeated LLM calls on re-renders)
        cache_key = f"{doc_style}_{len(results)}"
        if st.session_state.get("cached_suggestions_key") != cache_key:
            with st.spinner("🤖 Generating AI docstrings for missing functions..."):
                suggestions = {}
                for r in results:
                    fp = r.get("path")
                    suggs = []

                    for fn in r.get("functions", []):
                        if not fn.get("has_docstring"):
                            try:
                                doc = generate_docstring(fn, style=doc_style)
                            except Exception as e:
                                doc = f'"""\nPerform {fn["name"]} operations.\n"""'
                            suggs.append({
                                "name": fn["name"],
                                "lineno": fn["lineno"],
                                "indent": fn["indent"],
                                "file": fp,
                                "doc": doc,
                                "existing_doc": fn.get("docstring"),
                            })

                    if suggs:
                        suggestions[fp] = suggs

                st.session_state["cached_suggestions"] = suggestions
                st.session_state["cached_suggestions_key"] = cache_key

        suggestions = st.session_state.get("cached_suggestions", {})

        if not suggestions:
            st.success("🎉 All functions have docstrings!")
        else:
            search = st.text_input("🔍 Filter by function name", placeholder="Type to filter...")

            for fp, items in suggestions.items():
                st.markdown(f"### 📄 {Path(fp).name}")

                for idx, item in enumerate(items):
                    # Apply search filter
                    if search and search.lower() not in item["name"].lower():
                        continue

                    st.markdown('<div class="ui-card">', unsafe_allow_html=True)

                    st.markdown(
                        f"#### `{item['name']}()` <span class='status-error'>Missing Docstring</span>",
                        unsafe_allow_html=True
                    )

                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("**Current**")
                        st.code(
                            item["existing_doc"] or "# No docstring",
                            language="python"
                        )

                    with col2:
                        st.markdown("**AI Generated**")
                        st.code(item["doc"], language="python")

                    # Action buttons
                    col_accept, col_reject = st.columns(2)

                    with col_accept:
                        if st.button(
                            "✅ Accept",
                            key=f"accept-{fp}-{item['lineno']}-{idx}",
                            use_container_width=True
                        ):
                            try:
                                apply_docstring_to_file(
                                    file_path=item["file"],
                                    lineno=item["lineno"],
                                    indent=item["indent"],
                                    docstring=item["doc"],
                                )
                                results = parse_path(scan_path)
                                report = compute_coverage(results)
                                write_report(report, "storage/reports/docstring_coverage.json")
                                st.session_state["last_scan_results"] = results
                                st.session_state["last_report"] = report
                                st.session_state.pop("cached_suggestions_key", None)
                                st.success("✅ Applied successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to apply: {e}")

                    with col_reject:
                        if st.button(
                            "❌ Reject",
                            key=f"reject-{fp}-{item['lineno']}-{idx}",
                            use_container_width=True
                        ):
                            st.info("Docstring rejected")

                    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================================
# VIEW: VALIDATION
# ============================================================================

elif view == "🧪 Validation":
    st.markdown("## 🧪 PEP 257 Validation")

    if st.button("▶️ Run Validation", use_container_width=True):
        with st.spinner("Running pydocstyle validation..."):
            st.session_state["validation_result"] = run_pydocstyle(scan_path)

    result = st.session_state.get("validation_result")

    if not result:
        st.info("Click 'Run Validation' to check code quality")
    else:
        issues = result.get("issues", [])
        errors, warnings = classify_issues(issues)

        col1, col2, col3 = st.columns(3)
        col1.metric("🔴 Errors", len(errors))
        col2.metric("🟡 Warnings", len(warnings))
        
        if issues:
            col3.metric("Status", "❌ Issues Found")
        else:
            col3.metric("Status", "✅ Clean")

        # Visualization
        if errors or warnings:
            st.bar_chart({
                "Errors": len(errors),
                "Warnings": len(warnings)
            })

        # Display issues
        if errors:
            st.markdown("### 🔴 Errors")
            for e in errors:
                # Join error lines and display in code block for better visibility
                error_text = "\n".join(e)
                st.markdown(
                    f'<div style="background-color: #FEE2E2; padding: 12px; border-radius: 8px; '
                    f'border-left: 4px solid #DC2626; margin-bottom: 8px;">'
                    f'<pre style="color: #991B1B; margin: 0; white-space: pre-wrap;">{error_text}</pre>'
                    f'</div>',
                    unsafe_allow_html=True
                )

        if warnings:
            st.markdown("### 🟡 Warnings")
            for w in warnings:
                # Join warning lines and display in code block for better visibility
                warning_text = "\n".join(w)
                st.markdown(
                    f'<div style="background-color: #FEF3C7; padding: 12px; border-radius: 8px; '
                    f'border-left: 4px solid #D97706; margin-bottom: 8px;">'
                    f'<pre style="color: #92400E; margin: 0; white-space: pre-wrap;">{warning_text}</pre>'
                    f'</div>',
                    unsafe_allow_html=True
                )

        if not issues:
            st.success("🎉 No validation issues found!")

# ============================================================================
# VIEW: COVERAGE
# ============================================================================

elif view == "📈 Coverage":
    st.markdown("## 📈 Coverage Report")

    if not report:
        st.info("Run a scan to view coverage metrics")
    else:
        summary = report["summary"]

        col1, col2, col3 = st.columns(3)
        col1.metric("📦 Total Items", summary["total_items"])
        col2.metric("✅ Documented", summary["total_docs"])
        col3.metric("📊 Coverage", f"{summary['coverage_percent']}%")

        st.progress(summary["coverage_percent"] / 100)

        st.divider()

        # File-level breakdown
        st.markdown("### 📁 File Breakdown")
        rows = []
        for fp, meta in report["files"].items():
            rows.append({
                "File": Path(fp).name,
                "Items": meta["total_items"],
                "Documented": meta["doc_count"],
                "Coverage %": meta["coverage_percent"]
            })

        st.dataframe(rows, use_container_width=True)

        st.divider()

        # Code metrics
        st.markdown("## 📐 Code Metrics")

        selected = st.session_state.get("selected_file")

        if not selected:
            st.info("Select a file from the sidebar to view metrics")
        else:
            try:
                mi, metrics = compute_code_metrics(selected)

                st.metric("🎯 Maintainability Index", f"{round(mi, 2)}")

                st.markdown("### 🔍 Complexity Breakdown")
                rows = []
                for m in metrics:
                    rows.append({
                        "Name": m["name"],
                        "Type": m["type"],
                        "Line": m["line"],
                        "Complexity": m["complexity"]
                    })

                st.dataframe(rows, use_container_width=True)

            except Exception as e:
                st.error(f"Unable to compute metrics: {e}")
