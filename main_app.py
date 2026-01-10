def load_pytest_results():
    path = Path("storage/reports/pytest_results.json")
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None
def summarize_tests_by_file(pytest_data):
    """
    Returns:
    {
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


# main_app.py
# Streamlit UI for Milestone 1 — Parser & Baseline Generator view (mentor-style)
import sys
from pathlib import Path

# ensure project root is on sys.path so core.* imports work
PROJECT_ROOT = Path(__file__).parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
import streamlit as st
from dashboard_ui.dashboard import (
    load_pytest_results,
    filter_functions
)
from core.parser.python_parser import parse_path, parse_file
from core.docstring_engine.generator import generate_docstring
# ---------- UI STATE ----------
if "active_feature" not in st.session_state:
    st.session_state.active_feature = None

from core.reporter.coverage_reporter import compute_coverage, write_report
from core.docstring_engine.apply_docstring import apply_docstring_to_file
from core.validator.validator import run_pydocstyle
import ast

def compute_code_metrics(file_path):
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
/* Page background */
.stApp {
    background-color: #F7F9FC;
}

/* Card container */
.ui-card {
    background: white;
    border-radius: 14px;
    padding: 18px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.06);
    margin-bottom: 16px;
}

/* Status colors */
.status-ok {
    color: #16A34A;
    font-weight: 600;
}
.status-error {
    color: #DC2626;
    font-weight: 600;
}
.status-warn {
    color: #D97706;
    font-weight: 600;
}

/* Buttons */
.stButton button {
    border-radius: 10px;
    padding: 0.4rem 1rem;
}

/* Code blocks */
code, pre {
    background-color: #F1F5F9 !important;
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)
st.markdown("""
<style>

/* ===============================
   GLOBAL (RIGHT PANEL UNTOUCHED)
   =============================== */
.stApp {
    background-color: #F7F9FC;
    color: #0F172A;
}

/* ===============================
   SIDEBAR BASE
   =============================== */
section[data-testid="stSidebar"] {
    background-color: #0F2A44;
    border-right: 1px solid #1E3A8A;
}

/* ===============================
   SIDEBAR HEADINGS
   =============================== */
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #FFFFFF !important;
    font-weight: 700;
}

/* ===============================
   SIDEBAR LABELS
   (Scan Path, Docstring Style, Navigation title)
   =============================== */
section[data-testid="stSidebar"] label {
    color: #FFFFFF !important;
    font-weight: 600;
}

/* ===============================
   SIDEBAR INPUTS
   =============================== */
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] textarea {
    background-color: #FFFFFF !important;
    color: #000000 !important;
    border-radius: 8px;
}

/* ===============================
   SIDEBAR SELECTBOX (Docstring Style)
   =============================== */
section[data-testid="stSidebar"] div[data-baseweb="select"] {
    background-color: #FFFFFF !important;
    border-radius: 8px;
}

section[data-testid="stSidebar"] div[data-baseweb="select"] span {
    color: #000000 !important;
}

section[data-testid="stSidebar"] div[data-baseweb="select"] svg {
    fill: #000000 !important;
}

/* ===============================
   UI CARDS (RIGHT PANEL SAFE)
   =============================== */
.ui-card {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 18px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.06);
    margin-bottom: 16px;
}

/* ===============================
   CODE BLOCKS (RIGHT PANEL SAFE)
   =============================== */
code, pre {
    background-color: #F1F5F9 !important;
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
.feature-card {
    border-radius: 14px;
    padding: 22px;
    color: white;
    text-align: center;
    font-weight: 600;
    box-shadow: 0 8px 20px rgba(0,0,0,0.12);
}

.feature-title {
    font-size: 16px;
    margin-top: 8px;
}

.feature-sub {
    font-size: 13px;
    opacity: 0.9;
}

.grad-purple { background: linear-gradient(135deg, #6D5DF6, #8E7CFF); }
.grad-pink   { background: linear-gradient(135deg, #FF6CAB, #FF8C7F); }
.grad-blue   { background: linear-gradient(135deg, #2EC5FF, #3A7BFF); }
.grad-green  { background: linear-gradient(135deg, #2EE59D, #38F9D7); }
/* Feature button styled as card */
section[data-testid="stAppViewContainer"] .stButton > button {
    height: 120px;
    background: linear-gradient(135deg, #6D5DF6, #8E7CFF);
    color: white;
    font-weight: 600;
    border-radius: 14px;
    border: none;
    box-shadow: 0 8px 20px rgba(0,0,0,0.12);
    white-space: pre-line; /* allows line breaks */
}

section[data-testid="stAppViewContainer"] .stButton > button:hover {
    transform: translateY(-2px);
    transition: 0.2s ease;
}
 
</style>
""", unsafe_allow_html=True)
st.markdown("""
<style>
/* ===== SAFE: Sidebar navigation text ONLY ===== */
section[data-testid="stSidebar"]
div[data-baseweb="radio"]
span[data-testid="stMarkdownContainer"] {
    color: #FFFFFF !important;
}
</style>
""", unsafe_allow_html=True)
st.markdown("""
<style>
/* ===== Enhanced UI Buttons (Key-based, SAFE) ===== */

/* Advanced Filters – Purple */
button[kind="secondary"][data-testid="baseButton-feature_filters"] {
    background: linear-gradient(135deg, #6D5DF6, #8E7CFF);
    color: white;
    border: none;
}

/* Search – Pink */
button[kind="secondary"][data-testid="baseButton-feature_search"] {
    background: linear-gradient(135deg, #FF6CAB, #FF8C7F);
    color: white;
    border: none;
}

/* Export – Blue */
button[kind="secondary"][data-testid="baseButton-feature_export"] {
    background: linear-gradient(135deg, #2EC5FF, #3A7BFF);
    color: white;
    border: none;
}

/* Help & Tips – Green */
button[kind="secondary"][data-testid="baseButton-feature_help"] {
    background: linear-gradient(135deg, #2EE59D, #38F9D7);
    color: white;
    border: none;
}

/* Hover effect (all 4 only) */
button[kind="secondary"][data-testid^="baseButton-feature"]:hover {
    filter: brightness(1.05);
    transform: translateY(-1px);
}
</style>
""", unsafe_allow_html=True)



scan_path = "examples/"
doc_style = "google"


st.set_page_config(page_title="Milestone 1: Parser & Baseline Generator ", layout="wide")
st.title("AI-Powered Code Reviewer by Pavithra Kotha")


# layout: left panel (files) + main area
left_col, main_col = st.columns([1.2, 3])


try:
    results = parse_path(scan_path)
    report = compute_coverage(results)
    write_report(report, "storage/reports/docstring_coverage.json")
    st.session_state["last_scan_results"] = results
    st.session_state["last_report"] = report
            # ✅ Auto-select first file for AST preview
    if results:
        st.session_state["selected_file"] = str(results[0]["path"])
    else:
        st.session_state.pop("selected_file", None)

        st.success(f"Scanned {len(results)} file(s). Report saved.")
except Exception as e:
    st.error(f"Scan failed: {e}")
    st.text(e)


    # show quick metrics in left panel
    report = st.session_state.get("last_report")
    results = st.session_state.get("last_scan_results")
    if report:
        summary = report.get("summary", {})
        total_items = summary.get("total_items", 0)
        total_docs = summary.get("total_docs", 0)
        cov_pct = summary.get("coverage_percent", 0.0)

        st.markdown("")
        st.markdown(f"**Overall coverage**: {cov_pct}%")
        # visual progress
        st.progress(int(cov_pct))

        st.markdown("---")
        st.markdown("#### Files")
        files = report.get("files", {})
        # order by coverage ascending so low coverage is visible first
        for fp, meta in sorted(files.items(), key=lambda x: x[1].get("coverage_percent", 0)):
            short = Path(fp).name
            pct = meta.get("coverage_percent", 0.0)
            # show small bar and linkable button (select)
            st.markdown(f"**{short}** — {pct}%")
            st.progress(int(pct))

            # button to select file for preview
            if st.button(f"Preview: {short}", key=f"preview-{short}"):
                st.session_state["selected_file"] = fp

    else:
        st.info("No scan run yet. Enter path and click Scan.")
with st.sidebar:
    st.markdown("## 🔍 Project Control")

    scan_path = st.text_input("Scan Path", value="examples/")
    doc_style = st.selectbox(
        "Docstring Style",
        ["google", "numpy", "rest"]
    )

    if st.button("🚀 Scan Project"):
        results = parse_path(scan_path)
        report = compute_coverage(results)
        write_report(report, "storage/reports/docstring_coverage.json")

        st.session_state["last_scan_results"] = results
        st.session_state["last_report"] = report

        if results:
            st.session_state["selected_file"] = str(results[0]["path"])

        st.success("Scan completed")

    st.divider()

    st.markdown("## 🧭 Navigation")
    if "view" not in st.session_state:
        st.session_state.view = "📊 Dashboard"

    def nav_button(label):
        if st.button(label, use_container_width=True):
           st.session_state.view = label

    nav_button("📊 Dashboard")
    nav_button("🧩 Docstrings")
    nav_button("🧪 Validation")
    nav_button("📈 Coverage")

    view = st.session_state.view
    st.divider()

    st.markdown("## 📁 Files")
    report = st.session_state.get("last_report")
    if report:
        for fp in report.get("files", {}):
            if st.button(Path(fp).name, key=f"file-{fp}"):
                st.session_state["selected_file"] = fp

# ===============================
# VALIDATION HELPER
# ===============================
def classify_issues(issues):
    warnings = []
    errors = []

    for issue in issues:
        text = " ".join(issue)

        if "D1" in text:
            errors.append(issue)
        elif "D2" in text:
            warnings.append(issue)
        else:
            warnings.append(issue)

    return errors, warnings
    selected = st.session_state.get("selected_file")
    report = st.session_state.get("last_report")
    results = st.session_state.get("last_scan_results")

    coverage_score = 0.0
    validation_score = 0
    test_score = 0
    quality_score = 0.0

suggestions = {}

if results:
    for r in results:
        fp = r.get("path")
        suggs_for_file = []

        for fn in r.get("functions", []):
            if not fn.get("has_docstring"):
                doc = generate_docstring(fn, style=doc_style)
                suggs_for_file.append({
                    "name": fn["name"],
                    "lineno": fn["lineno"],
                    "indent": fn["indent"],
                    "file": fp,
                    "doc": doc,
                    "existing_doc": fn.get("docstring"),
                })

        if suggs_for_file:
            suggestions[fp] = suggs_for_file

    if view == "📊 Dashboard":
        st.markdown("## 📊 Project Dashboard")

        if not report:
           st.info("Run scan to view dashboard")
        else:
           summary = report["summary"]

           c1, c2, c3 = st.columns(3)
           c1.metric("Files Scanned", len(report.get("files", {})))
           c2.metric("Coverage %", summary.get("coverage_percent", 0))
           c3.metric("Total Items", summary.get("total_items", 0))

           st.progress(summary.get("coverage_percent", 0) / 100)
        # ✅ AST PARSER OUTPUT (ONLY HERE)
        st.markdown("### 🧠 AST Parsing Output")
        selected = st.session_state.get("selected_file")
        if selected and results:
            parsed = None
            for r in results:
               if str(r.get("path")) == selected:
                  parsed = r
                  break

            if not parsed:
               st.warning("Selected file not found.")
            else:
               txt_lines = []
               txt_lines.append(f"# File: {Path(parsed['path']).name}")
               txt_lines.append(
                f"Module docstring: {bool(parsed.get('module_docstring'))}"
               )
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
            st.info("Select a file from sidebar to see AST output.")
        #st.markdown("## 🧪 Test Results")

        pytest_data = load_pytest_results()

        if not pytest_data:
           st.info("Run pytest with --json-report")
        else:
           file_summary = summarize_tests_by_file(pytest_data)

           rows = []
           for file, stats in file_summary.items():
               rows.append({
                   "File": Path(file).stem,
                   "Passed": stats["passed"],
                   "Failed": stats["failed"]
                })

           import pandas as pd
           df = pd.DataFrame(rows).set_index("File")

           st.markdown("## 📊 Test Execution Results (File-wise)")
           st.bar_chart(df)
           # ---------- Mentor-style single-bar graph ----------

        #    EXPECTED_TEST_FILES = [
        #        "test_coverage_reporter",
        #        "test_dashboard",
        #        "test_generator",
        #        "test_llm_integration",
        #        "test_parser",
        #        "test_validation",
        #    ]

# Initialize all files with 0 → ensures 6 bars always
           

        #    summary = pytest_data["summary"]

        #    c1, c2, c3 = st.columns(3)
        #    c1.metric("Total", summary["total"])
        #    c2.metric("Passed", summary["passed"])
        #    c3.metric("Failed", summary["failed"])
        #    file_summary = summarize_tests_by_file(pytest_data)
        #     # Build per-file graph data
        #    graph_data = {}

        #    for file, stats in file_summary.items():
        #        short_name = Path(file).stem.replace("test_", "")
        #        graph_data[short_name] = {
        #             "Passed": stats["passed"],
        #             "Failed": stats["failed"]
        #        }
        #    st.markdown("## 📊 Test Results by File (Passed vs Failed)")

        #    st.bar_chart(graph_data)

           st.markdown("### 📄 Test Results by File")

           rows = []
           for file, stats in file_summary.items():
              rows.append({
              "File": file,
              "Total": stats["total"],
              "Passed": stats["passed"],
              "Failed": stats["failed"],
           })

           st.table(rows)
        st.markdown("### ❌ Errors by Test File")

        file_summary = summarize_tests_by_file(pytest_data)

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
                               or "No error details provided by pytest"
                            )

                            st.code(error_text)

        st.markdown("### ✨ Enhanced UI Features")
        st.caption("Explore powerful analysis tools")

        st.markdown('<div class="feature-section">', unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            if st.button(
        "🔍\nAdvanced Filters\nFilter by status",
        key="feature_filters",
        use_container_width=True
            ):
             st.session_state.active_feature = "filters"

        with c2:
            if st.button(
        "🔎\nSearch\nFind functions",
        key="feature_search",
        use_container_width=True
            ):
             st.session_state.active_feature = "search"

        with c3:
            if st.button(
        "📤\nExport\nJSON & CSV",
        key="feature_export",
        use_container_width=True
            ):
             st.session_state.active_feature = "export"

        with c4:
            if st.button(
        "ℹ️\nHelp & Tips\nQuick guide",
        key="feature_help",
        use_container_width=True
            ):
             st.session_state.active_feature = "help"

        st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.active_feature == "filters":
            st.markdown("## 🔎 Advanced Filters")

            status_filter = st.selectbox(
              "Documentation status",
              ["All", "Missing Docstring"]
            )

            rows = []
            for r in results:
                for fn in r.get("functions", []):
                    has_doc = fn.get("has_docstring", False)

                    if status_filter == "Missing Docstring" and has_doc:
                        continue

                    rows.append({
                       "File": Path(r["path"]).name,
                       "Function": fn["name"],
                       "Docstring": "Yes" if has_doc else "No"
                    })

            st.table(rows)
        query = ""
        if st.session_state.active_feature == "search":
            st.markdown("## 🔎 Search Functions")
            st.caption("Search across all parsed functions and classes")

            query = st.text_input(
                "Enter function or class name",
                placeholder="Type to search..."
            ).strip().lower()

            rows = []

            if query and results:
                for r in results:
                    file_name = Path(r["path"]).name

            # Functions
                    for fn in r.get("functions", []):
                        name = fn["name"].lower()
                        if query in name:
                            rows.append({
                               "File": file_name,
                               "Name": fn["name"],
                               "Type": "Function",
                               "Docstring": "✅ Fixed" if fn["has_docstring"] else "❌ Missing"
                             })

            # Classes
                    for cls in r.get("classes", []):
                        name = cls["name"].lower()
                        if query in name:
                            rows.append({
                            "File": file_name,
                            "Name": cls["name"],
                            "Type": "Class",
                            "Docstring": "✅ Fixed" if cls["has_docstring"] else "❌ Missing"
                            })

        if query:
            if rows:
                st.markdown("### Results")
                st.table(rows)
            else:
                st.info("No matching functions or classes found.")
        if st.session_state.active_feature == "export":
            st.markdown("## 📤 Export Data")
            st.caption("Download analysis results in JSON or CSV format")

            rows = build_export_rows(results)

            total = len(rows)
            documented = sum(1 for r in rows if r["Docstring"] == "Present")
            missing = total - documented

            st.markdown("### 📊 Export Summary")
            st.info(
                    f"""
                    • **Total Items:** {total}  
                    • **Documented:** {documented}  
                    • **Missing Docstrings:** {missing}
                    """
                    )
            json_data = json.dumps(rows, indent=2)

            st.download_button(
            label="📥 Export as JSON",
            data=json_data,
            file_name="docstring_report.json",
            mime="application/json"
            )
            import pandas as pd
            df = pd.DataFrame(rows)
            csv_data = df.to_csv(index=False)

            st.download_button(
            label="📥 Export as CSV",
            data=csv_data,
            file_name="docstring_report.csv",
            mime="text/csv"
            )
        if st.session_state.active_feature == "help":
            st.markdown("## ℹ️ Interactive Help & Tips")
            st.caption("Contextual help and quick reference guide")

            c1, c2 = st.columns(2)

            with c1:
                st.markdown("""
                <div class="ui-card" style="border-left: 6px solid #22C55E;">
                <h4>📊 Coverage Metrics</h4>
                <ul>
                <li><b>Coverage %</b> = (Documented / Total) × 100</li>
                <li>🟢 Green badge: ≥ 90%</li>
                <li>🟡 Yellow badge: 70–89%</li>
                <li>🔴 Red badge: &lt; 70%</li>
                </ul>
                </div>
                """, unsafe_allow_html=True)

            with c2:
                st.markdown("""
                <div class="ui-card" style="border-left: 6px solid #F59E0B;">
                <h4>✅ Function Status</h4>
                <ul>
                <li>🟢 Docstring present</li>
                <li>🔴 Missing or incomplete docstring</li>
                <li>Auto-detected docstring style</li>
                <li>Style-specific validation</li>
                </ul>
                </div>
                """, unsafe_allow_html=True)

            c3, c4 = st.columns(2)

            with c3:
                st.markdown("""
                <div class="ui-card" style="border-left: 6px solid #3B82F6;">
                <h4>🧪 Test Results</h4>
                <ul>
                <li>Real-time test execution summary</li>
                <li>Pass / Fail indicators</li>
                <li>File-wise test breakdown</li>
                <li>Integrated pytest reports</li>
                </ul>
                </div>
                """, unsafe_allow_html=True)

            with c4:
                st.markdown("""
                <div class="ui-card" style="border-left: 6px solid #8B5CF6;">
                <h4>📄 Docstring Styles</h4>
                <ul>
                <li><b>Google</b>: Args, Returns, Raises</li>
                <li><b>NumPy</b>: Parameters / Returns format</li>
                <li><b>reST</b>: :param, :return:</li>
                <li>Auto-style detection & validation</li>
                </ul>
               </div>
               """, unsafe_allow_html=True)

    elif view == "🧩 Docstrings":
        st.markdown("## 🧩 Docstring Review")

        if not suggestions:
           st.success("All functions have docstrings 🎉")
        else:
            st.markdown("## ")

        if not suggestions:
           st.success("All functions already have docstrings 🎉")
        else:
           search = st.text_input(
            "🔍 Search function",
            placeholder="Type function name"
            )
           for fp, items in suggestions.items():
                st.markdown(f"### 📄 {Path(fp).name}")

                for idx, it in enumerate(items):

                    if search and search.lower() not in fn["name"].lower():
                       continue
                    st.markdown('<div class="ui-card">', unsafe_allow_html=True)

                    st.markdown(
                       f"### `{it['name']}` "
                       f"<span class='status-error'>Missing Docstring</span>",
                       unsafe_allow_html=True
                    )


                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("**Original**")
                        st.code(
                           it["existing_doc"] or "No docstring found",
                           language="python"
                        )

                    with col2:
                        st.markdown("**Revised (AI)**")
                        st.code(doc, language="python")

                    col_a, col_r = st.columns([1, 1])

                    with col_a:
                        if st.button(
                            "✅ Accept",
                            key=f"accept-{fp}-{it['lineno']}-{idx}"
                        ):
                            apply_docstring_to_file(
                            file_path=it["file"],
                            lineno=it["lineno"],
                            indent=it["indent"],
                            docstring=it["doc"],
                            )
                            st.success("Docstring applied successfully")
                            st.rerun()

                    with col_r:
                        st.button(
                           "❌ Reject",
                           key=f"reject-{fp}-{it['lineno']}-{idx}"
                        )

                    st.markdown("</div>", unsafe_allow_html=True)
    elif view == "🧪 Validation":
        st.markdown("## 🧪 Validation Results (PEP 257)")

        if st.button("Run Validation"):
           st.session_state["validation_result"] = run_pydocstyle(scan_path)

        result = st.session_state.get("validation_result")

        if not result:
           st.info("Run validation to see results.")
        else:
           issues = result["issues"]
           errors, warnings = classify_issues(issues)

           c1, c2, c3 = st.columns(3)
           c1.metric("Errors", len(errors))
           c2.metric("Warnings", len(warnings))
           c3.metric("Status", "❌ Issues" if issues else "✅ Clean")

           st.bar_chart({
            "Errors": len(errors),
            "Warnings": len(warnings)
           })

           for e in errors:
               st.error("\n".join(e))

           for w in warnings:
               st.warning("\n".join(w))
           
           pytest_data = load_pytest_results() 
           failed_tests = [
           t for t in pytest_data.get("tests", [])
              if t.get("outcome") == "failed"
           ]

    elif view == "📈 Coverage":
        st.markdown("## 📈 Coverage Report")

        if not report:
           st.info("Run scan to view coverage")
        else:
           summary = report["summary"]

           c1, c2, c3 = st.columns(3)
           c1.metric("Total Items", summary["total_items"])
           c2.metric("Documented", summary["total_docs"])
           c3.metric("Coverage %", summary["coverage_percent"])

           st.progress(summary["coverage_percent"] / 100)

           rows = []
           for fp, meta in report["files"].items():
               rows.append({
                "File": Path(fp).name,
                "Items": meta["total_items"],
                "Docs": meta["doc_count"],
                "Coverage %": meta["coverage_percent"]
               })
           st.table(rows)
           
           st.markdown("## 📐 Code Metrics")

           selected = st.session_state.get("selected_file")

           if not selected:
               st.info("Select a file from the sidebar to view code metrics.")
           else:
               try:
                    mi, metrics = compute_code_metrics(selected)

                    st.metric("Maintainability Index", round(mi, 2))

                    rows = []
                    for m in metrics:
                        rows.append({
                      "Name": m["name"],
                      "Type": m["type"],
                      "Line": m["line"],
                      "Complexity": m["complexity"]
                        })

                    st.markdown("### 🔍 Function / Class Breakdown")
                    st.table(rows)

               except Exception as e:
                   st.error("Unable to compute metrics for this file.")
                   st.text(e)

           #st.dataframe(rows, use_container_width=True)
    pytest_data = load_pytest_results() 
   
    # ---------- Validation helpers ----------
    def classify_issues(issues):
        warnings = []
        errors = []

        for issue in issues:
            text = " ".join(issue)

            if "D1" in text:      # Missing docstrings (module/class/function/method)
                errors.append(issue)
            elif "D2" in text:    # Formatting issues (blank lines, spacing)
                warnings.append(issue)
            else:
                warnings.append(issue)

        return errors, warnings
       
    suggestions = {}

    if results:
       for r in results:
        fp = r.get("path")
        suggs_for_file = []

        for fn in r.get("functions", []):
            if not fn.get("has_docstring"):
                doc = generate_docstring(fn, style=doc_style)
                suggs_for_file.append({
                    "type": "function",
                    "name": fn.get("name"),
                    "lineno": fn.get("lineno"),
                    "indent": fn.get("indent"),
                    "file": fp,
                    "doc": doc,
                    "existing_doc": fn.get("docstring"),
                })

        if suggs_for_file:
            suggestions[fp] = suggs_for_file