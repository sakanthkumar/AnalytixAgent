# Data Analyst Agent (Failure Analysis System)

An intelligent, agentic system designed to analyze machine failure logs, perform strict Root Cause Analysis, Impact Assessment, and generate Repair Guides using local LLMs.

## 🚀 Features

- **Automated EDA**: Instantly analyzes uploaded CSV datasets, creating statistical summaries and correlation heatmaps.
- **Strict Failure Analysis**:
    - **Root Cause Analysis (WHY)**: Identifies system-level causes without speculation.
    - **Impact Assessment (WHAT)**: Qualifies operational, safety, and performance risks.
    - **Repair Guide (HOW)**: Provides high-level corrective actions derived from manuals.
- **Single-Pipeline Architecture**: Uses a unified, strict system prompt to generate a cohesive report in a single pass, ensuring consistency across all sections.
- **RAG Integration**: Retrieves technical context from uploaded manuals (PDFs) to ground the analysis in fact.
- **Acronym Resolution**: Detects unknown acronyms in the dataset and prompts the user for definitions before analysis.
- **Local Privacy**: Runs entirely locally using Ollama and ChromaDB—no data leaves your machine.

## 🛠️ Tech Stack

- **Frontend**: React, Chart.js, CSS Modules (Glassmorphism UI)
- **Backend**: Python, FastAPI, Pandas
- **AI/ML**: Ollama (Qwen 2.5 Coder), LangChain (Conceptually), ChromaDB (Vector Store)
- **Architecture**: Agentic Workflow with "Perceive-Decide-Act" loop.

## 📦 Installation

### Prerequisites
- Python 3.10+
- Node.js 16+
- [Ollama](https://ollama.com/) installed and running.

### 1. Backend Setup
```bash
cd backend
python -m venv venv
# Activate venv (Windows: venv\Scripts\activate, Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
```

### 2. Frontend Setup
```bash
cd frontend
npm install
```

### 3. Model Setup
Pull the required local model:
```bash
ollama pull qwen2.5-coder:1.5b
```

## 🏃 Usage

1. **Start the Backend**:
   ```bash
   python backend/main.py
   ```
   (Server runs on `http://localhost:8000`)

2. **Start the Frontend**:
   ```bash
   cd frontend
   npm start
   ```
   (App opens at `http://localhost:3000`)

3. **Workflow**:
   - Upload a CSV file (e.g., `machine_failures.csv`).
   - Define any unknown acronyms if prompted.
   - Click **"🧠 Generate AI Reliability Report"**.
   - View the strict, multi-stage analysis generated locally.

## 📁 Project Structure

- `backend/agent.py`: Core agent logic with strict system prompts/personas.
- `backend/main.py`: FastAPI routes and orchestration.
- `backend/normalizer.py`: Deterministic text processing to enforce output constraints.
- `backend/knowledge.py`: RAG implementation using ChromaDB.
- `frontend/src/Dashboard.jsx`: Main React UI component.

## 🔒 License
MIT
