### **Executive Summary: Smart Developer Assistant**

The **Smart Developer Assistant** is an AI-powered workstation designed to accelerate the software development lifecycle (SDLC) by automating routine engineering tasks. Built on a modular **Controller-Agent architecture**, the system integrates a Streamlit-based frontend with specialized backend agents that handle code quality, testing, architecture visualization, and data operations.

#### **Core Capabilities**

* **Automated Code Governance:**
* **Modern Java Review:** The **CodeReviewAgent** analyzes staged files to enforce Java 17+ standards, identifying dead code, security risks, and concurrency issues while offering auto-fix capabilities.
* **Dependency Auditing:** The **DependencyInspectorAgent** scans project catalogs (`libs.versions.toml`), queries Maven Central APIs, and generates reports on outdated libraries to prevent technical debt.


* **Accelerated Development & Testing:**
* **Unit Test Generation:** The **TestGenAgent** automatically drafts robust JUnit 5 test suites for staged code, covering edge cases and strictly adhering to testing best practices.
* **Architectural Visualization:** The **ClassDiagramAgent** scans the repository and converts raw Java source code into visual Mermaid.js class diagrams, aiding in documentation and system understanding.


* **Natural Language Data Operations:**
* **Text-to-SQL (BigQuery):** The **BigQueryAgent** translates natural language questions into valid, optimized GoogleSQL, strictly grounded in the user's provided schema to prevent hallucinations.
* **Text-to-NoSQL (MongoDB):** The **MongoAgent** converts questions into MongoDB Shell aggregation pipelines, featuring safety guardrails that block write operations.



#### **Technical Architecture**

* **Hybrid AI Engine:** The system is model-agnostic, allowing users to toggle between **Local AI** (Ollama running Qwen 2.5 Coder) for data privacy and **Cloud AI** (Google Gemini 3 Flash) for enhanced performance.
* **Safety & Validation:**
* **Schema Grounding:** Data agents are restricted to specific, user-provided schema files (`.sql` or `.json`) to ensure query accuracy.
* **Syntax Enforcement:** Generated code undergoes validation layers, such as `sqlglot` for SQL and defensive sanitization for diagrams and code blocks.


* **User Interface:** A centralized dashboard (`app.py`) routes requests to the appropriate agent, manages context (project paths or schemas), and renders interactive results like live diagrams and data tables.