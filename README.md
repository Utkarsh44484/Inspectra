# ⚡ Inspectra

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red.svg)](https://streamlit.io/)
[![LiteLLM](https://img.shields.io/badge/LiteLLM-Integrated-green.svg)](https://github.com/BerriAI/litellm)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Inspectra** is an intelligent, multi-agent code analysis tool designed to provide enterprise-grade feedback on GitHub repositories. It moves beyond standard single-prompt LLM wrappers by utilizing a **Mixture of Experts (MoE)** architecture, parallel processing, and cross-family model synthesis.





🌍 **https://inspectra-bprehxwsfhkggwc7zdyixh.streamlit.app/**  

---

## 🧠 System Architecture: Mixture of Experts (MoE)

Inspectra doesn't rely on a single model to do everything. Instead, it deploys four specialized AI agents simultaneously using a **Map-Reduce** methodology.

### 1. The "Map" Phase (Parallel Execution)
When a repository is ingested, the codebase is passed to four independent agents running in parallel threads:
* 🏗️ **The Architect (Meta Llama 3.1 8B):** Analyzes structural integrity, SOLID principles, and design patterns.
* 🔒 **The Auditor (Meta Llama 3.3 70B):** A flagship model dedicated strictly to identifying security vulnerabilities, injection risks, and authorization flaws.
* ⚡ **The Optimizer (Google Gemini 1.5 Flash):** Leverages a massive context window to find algorithmic bottlenecks and memory leaks.
* 🧪 **The QA Engineer (Meta Llama 3.1 8B):** Searches for unhandled edge cases and recommends specific unit testing strategies.

### 2. The "Reduce" Phase (Synthesis)
* 👑 **The Lead Synthesizer:** Once the four expert reports are generated, they are fed into a Lead Synthesizer model. This model resolves conflicting advice, removes duplicates, and generates a unified, highly readable Executive Markdown Report.

---

## ✨ Key Features

* **Freemium SaaS Architecture:** Designed to work out-of-the-box using high-speed, free-tier open models (Groq/Google). Zero setup required for basic use.
* **Pro Mode (BYOK):** Power users can open the sidebar to inject their own OpenAI (GPT-4o) or Anthropic (Claude 3.5) API keys to override the default open models.
* **Native GitHub Integration:** Fetches repository trees and filters for relevant source code dynamically, ignoring binaries and images to optimize context windows.
* **Exportable Reports:** Download the final synthesized diagnostic review as a Markdown file with a single click.

---

## 🚀 How to Run Locally

Because this is a public repository, backend API keys are not hardcoded into the codebase for security reasons. To run this locally, you can use entirely **free** API keys.

### Prerequisites
* Python 3.9+
* Git

### 1. Clone & Install
```bash
git clone [https://github.com/Utkarsh44484/Inspectra.git](https://github.com/Utkarsh44484/Inspectra.git)
cd Inspectra
pip install -r requirements.txt
```


### Configure API Keys (Two Options)

**Option A: The UI Way (Easiest)**
Simply launch the app, open the "Pro Mode / Custom API Keys" expander in the sidebar, and paste your free API keys directly into the UI.

**Option B: The Environment Way (For standard routing)**
Create a `.streamlit` folder and add a `secrets.toml` file to route the default models automatically:

```bash
mkdir .streamlit
touch .streamlit/secrets.toml
```

Inside `secrets.toml`, add your free keys:

```toml
GROQ_API_KEY = "your_groq_key"
GEMINI_API_KEY = "your_gemini_key"
GITHUB_TOKEN = "your_github_token" # Optional, but highly recommended to prevent GitHub rate limits
```

*You can get free keys at [Groq Console](https://console.groq.com/) and [Google AI Studio](https://aistudio.google.com/).*

### Launch the Application

```bash
streamlit run app.py
```

---

## 🛠️ Tech Stack & Dependencies

* **Frontend & UI:** [Streamlit](https://streamlit.io/)
* **LLM Orchestration:** [LiteLLM](https://github.com/BerriAI/litellm) (Standardizes API calls across OpenAI, Anthropic, Google, and Groq).
* **Concurrency:** Python `concurrent.futures` for parallel agent execution.
* **Network:** `requests` for interacting with the GitHub REST API.
* **Inference Engines:** [Groq](https://groq.com/) (Meta Llama 3.1 & 3.3) and [Google AI Studio](https://aistudio.google.com/) (Gemini 1.5 Flash).
```
