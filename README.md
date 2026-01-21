# Project-AI-Powered-Code-Reviewer

# AI-Powered Code Reviewer 🤖🧠

![Python](https://img.shields.io/badge/Python-3.x-blue)
![AI](https://img.shields.io/badge/AI-NLP-orange)
![LLM](https://img.shields.io/badge/LLM-Transformer--Based-green)
![Status](https://img.shields.io/badge/Status-Active-success)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## 📌 Project Description

**AI-Powered Code Reviewer** is an intelligent software application that automatically reviews source code and provides **context-aware feedback, explanations, and improvement suggestions** using **Artificial Intelligence, Natural Language Processing (NLP), and Large Language Models (LLMs)**.

The system simulates a real-world automated code review assistant capable of analyzing programming logic, structure, readability, and best practices.
It is designed for **academic projects**, **Infosys certification submission**, and **local execution for experimentation with AI-driven software quality tools**.

---

## 🚀 Features

* 🔍 Automated source code analysis
* 🧠 AI-generated code review comments
* ✍️ Natural language explanations of code logic
* 📈 Suggestions for optimization and best practices
* ⚙️ Configurable LLM backend
* 📄 Human-readable review output
* 🧪 Test report generation and summarization
* 🗂 Modular and scalable project structure

---

## 🧠 Techniques Used

### 🔹 Natural Language Processing (NLP)

* Converts code structure into meaningful text representations
* Understands syntax, semantics, and intent of code
* Generates explanations and feedback in natural language

### 🔹 Prompt Engineering

* Carefully structured prompts for:

  * Code review
  * Error explanation
  * Improvement suggestions
* Ensures consistent and reliable AI responses
* Reduces ambiguity and irrelevant outputs

### 🔹 LLM-Based Text Generation

* Uses transformer-based language models
* Generates:

  * Code explanations
  * Review comments
  * Best-practice suggestions
* Produces developer-friendly feedback

---

## 🛠️ Tech Stack

### 🔹 Programming Language

* **Python 3.x**

### 🔹 Libraries / Frameworks

* `transformers`
* `torch`
* `langchain`
* `json`
* `os`
* `pytest`

### 🔹 AI / ML Technologies

* Natural Language Processing (NLP)
* Transformer-based Large Language Models (LLMs)
* Prompt-driven AI workflows

---

## 🤖 LLM Details

* Uses **transformer-based Large Language Models**
* Supports models such as:

  * GPT-style LLMs
  * Hugging Face transformer models
* **LLM is fully configurable**

  * Model can be changed via configuration
  * Supports API-based or locally hosted LLMs
* Designed for extensibility and experimentation

---

## 📂 Project Structure

```
Project-AI-Powered-Code-Reviewer/
│
├── core/
│   ├── reviewer.py
│   ├── prompt_templates.py
│
├── utils/
│   ├── file_loader.py
│   ├── formatter.py
│
├── storage/
│   └── reports/
│       └── pytest_results.json
│
├── tests/
│   └── test_reviewer.py
│
├── main.py
├── requirements.txt
├── README.md
└── LICENSE
```

---

## ⚙️ Installation Steps

1. **Clone the repository**

   ```
   git clone https://github.com/Pavithra-hub006/Project-AI-Powered-Code-Reviewer.git
   ```

2. **Navigate to the project directory**

   ```
   cd Project-AI-Powered-Code-Reviewer
   ```

3. **Create a virtual environment (recommended)**

   ```
   python -m venv venv
   ```

4. **Activate the virtual environment**

   * Windows:

     ```
     venv\Scripts\activate
     ```
   * Linux / macOS:

     ```
     source venv/bin/activate
     ```

5. **Install required dependencies**

   ```
   pip install -r requirements.txt
   ```

---

## ▶️ How to Run the Project Locally

1. Ensure all dependencies are installed

2. Configure the LLM API key (if required)

   ```
   export LLM_API_KEY=your_api_key
   ```

   or set it directly inside the configuration file

3. Run the application

   ```
   python main.py
   ```

4. Provide a source code file as input and receive AI-generated review output

---

## 🧪 Running Tests

To execute automated tests and generate reports:

```
pytest
```

For JSON test reports:

```
pytest --json-report --json-report-file=storage/reports/pytest_results.json
```

## 📜 License

This project is licensed under the **MIT License**.
You are free to use, modify, and distribute this project with proper attribution.


