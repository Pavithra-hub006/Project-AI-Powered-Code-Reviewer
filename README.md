# AI-Powered Code Reviewer & Docstring Engine 🤖🧠

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-FF4B4B.svg)
![LangChain](https://img.shields.io/badge/LangChain-1.0+-green.svg)
![LLM](https://img.shields.io/badge/LLM-Llama--3.1--8B--Instant-orange.svg)
![Tests](https://img.shields.io/badge/Tests-28%20Passed-success.svg)
![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)

---

## 📌 Project Overview

**AI-Powered Code Reviewer** is an intelligent developer tooling application that statically inspects Python source files, identifies missing documentation across functions, classes, and methods, and automatically generates standard-compliant docstrings (**Google**, **NumPy**, or **reST**) using **Llama 3.1** via **Groq Cloud** and **LangChain**.

Rather than relying on unconstrained LLM code rewrites (which risk introducing logic regressions), this project utilizes a **hybrid architecture**:
1. **Deterministic Static Analysis (AST):** Safe code parsing and exact indentation-aware insertion.
2. **LLM Semantic Inference:** Generates structured semantic docstring content (summary, parameter descriptions, returns, and raises).

---

## 🚀 Key Features

* **🔍 AST-Based Code Analysis:** Parses Python Abstract Syntax Trees (`ast`) without executing untrusted code, detecting functions, classes, inner methods, type annotations, and exceptions.
* **🧠 AI-Powered Docstring Generation:** Uses Groq's fast Llama 3.1 model to generate context-aware summaries and parameter mappings.
* **📝 Multi-Style Docstring Support:** Formats documentation in standard **Google**, **NumPy**, or **reST (Sphinx)** styles.
* **✍️ In-Place One-Click Code Insertion:** Automatically inserts accepted docstrings directly into the file on disk after the signature colon `:` with matching indentation.
* **📥 Instant Export / Download:** Download the fully documented `.py` file directly from the Streamlit web browser.
* **📊 Documentation Coverage Tracking:** Visual metrics, percentage coverage calculations, and color-coded progress indicators.
* **🧪 PEP 257 Compliance Auditing:** Automated style validation via `pydocstyle` detecting missing docstrings and formatting violations.
* **📐 Complexity & Maintainability Metrics:** Calculates function-level **Cyclomatic Complexity** and overall **Maintainability Index**.
* **⚡ Demo Mode:** One-click pre-loaded demo code for quick evaluation on Streamlit Cloud without requiring file uploads.

---

## 🛠️ Tech Stack

* **Language:** Python 3.11+
* **User Interface:** Streamlit, Pandas
* **LLM & AI Orchestration:** LangChain, Groq Cloud API (`llama-3.1-8b-instant`)
* **Static Code Analysis:** Python `ast` (Abstract Syntax Tree), `pydocstyle` (PEP 257), `radon`
* **Test Suite:** PyTest (28 automated unit tests with 100% pass rate)

---

## 📂 Project Structure

```text
Project-AI-Powered-Code-Reviewer/
│
├── main_app.py                     # Streamlit Web Application & Orchestrator
│
├── core/                           # Core Engine Modules
│   ├── parser/
│   │   └── python_parser.py        # AST Code Analyzer (Functions, Classes, Methods)
│   ├── docstring_engine/
│   │   ├── generator.py            # Google / NumPy / reST Style Formatter
│   │   ├── llm_integration.py      # Groq Llama 3.1 LLM Integration
│   │   └── apply_docstring.py      # In-Place Code Insertion Engine
│   ├── reporter/
│   │   └── coverage_reporter.py    # Coverage Calculator & Report Generator
│   └── validator/
│       └── validator.py            # PEP 257 Validator & Cyclomatic Complexity
│
├── storage/
│   ├── reports/                    # Persisted JSON coverage and pytest reports
│   └── uploads/                    # Working directory for uploaded Python files
│
├── tests/                          # Automated PyTest Test Suite (28 Tests)
│   ├── test_parser.py              # AST parser validation
│   ├── test_generotor.py           # Style formatter tests
│   ├── test_llm_integration.py     # Prompt & LLM fallback tests
│   ├── test_coverage_repoter.py    # Coverage mathematical calculations
│   ├── test_validation.py          # PEP 257 & complexity tests
│   └── test_dashboard.py           # Data processing tests
│
├── .env.example                    # Sample environment configuration template
├── .gitignore                      # Git tracking exclusion rules (protects API keys)
├── requirements.txt                # Production Python dependencies
├── pyproject.toml                  # Project & PyTest configuration
├── LICENSE                         # MIT License
└── README.md                       # Project documentation
```

---

## ⚙️ Installation & Local Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Pavithra-hub006/Project-AI-Powered-Code-Reviewer.git
cd Project-AI-Powered-Code-Reviewer
```

### 2. Create and Activate Virtual Environment
* **Windows (PowerShell):**
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```
* **Linux / macOS:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API Key
Create a `.env` file in the project root:
```bash
cp .env.example .env
```
Add your free Groq API key from [Groq Console](https://console.groq.com):
```env
GROQ_API_KEY="gsk_your_api_key_here"
```

---

## ▶️ Running the Application

Launch the Streamlit dashboard locally:
```bash
streamlit run main_app.py
```
The app will open automatically in your browser at `http://localhost:8501`.

---

## ☁️ Deployment on Streamlit Community Cloud

1. Push your repository to GitHub.
2. Sign in to **[share.streamlit.io](https://share.streamlit.io)**.
3. Click **"New app"** and select:
   * **Repository:** `Pavithra-hub006/Project-AI-Powered-Code-Reviewer`
   * **Branch:** `main`
   * **Main file path:** `main_app.py`
4. In **Advanced Settings → Secrets**, add your Groq key:
   ```toml
   GROQ_API_KEY = "gsk_your_api_key_here"
   ```
5. Click **Deploy!**

---

## 🧪 Running Automated Tests

To execute the full test suite (28 tests):
```bash
pytest
```

To run tests with a generated JSON report:
```bash
pytest --json-report --json-report-file=storage/reports/pytest_results.json
```

---

## 📜 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
