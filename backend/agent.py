import requests
import pandas as pd
import json
import time
import os
from dotenv import load_dotenv

from executor import execute_pandas_code
from knowledge import kb
from tools import search_web
from analyzer import analyze_correlations
from normalizer import normalize_output

load_dotenv()

# --- EXECUTION CONTROL ---
RUN_LLM_ANALYSIS = True


class DataAnalystAgent:
    def __init__(self):
        self.memory = []
        self.df = None
        self.context_data = {}

        # Configuration
        self.backend = "ollama"
        self.temperature = 0.1

        # Ollama Config
        self.ollama_url = "http://localhost:11434/api/generate"
        self.ollama_model = "qwen2.5-coder:1.5b"

        # ---------------- SYSTEM PROMPTS ---------------- #

        self.system_prompt_common = """
You are a Data Analyst Agent designed for fast, reliable responses.

Primary: Accuracy over verbosity. Speed over style. Clear, actionable outputs.
Rules:
- Default to concise answers (bullet points preferred).
- Avoid repetition, filler, or storytelling.
- Do not hallucinate. State missing data clearly.
- Response length: 80–120 tokens default.
- Structure: 1) Short summary (mandatory), 2) Detail (only if asked).
- Code: Minimal, runnable, no explanations unless requested.
- Error handling: Never fail silently.
"""

        self.system_prompt_code = self.system_prompt_common + """
Goal: Write ONLY valid python pandas code to analyze the dataframe `df`.
Rules:
1. Assign final output to variable `result`.
2. No imports except pandas (pd) and numpy (np).
3. Do NOT explain the code. Just provide the code block.
"""

        self.system_prompt_analysis = self.system_prompt_common + """
Goal: Explain analysis findings and provide actionable recommendations.
Structure:
1. **Conclusion**: Direct answer.
2. **Analysis**: Key metrics/findings.
3. **Recommendation**: Specific action items.
"""

        # ---------------- SYSTEM PROMPTS (STRICT STAGES) ---------------- #

        self.system_prompt_failure_combined = """
================================
SECTION 1: ROOT CAUSE ANALYSIS
================================
ROLE:
Explain WHY failures occur at a system level.

RULES:
- Do NOT include frequencies, percentages, or correlations.
- Do NOT include impact, repair, or prevention.
- Use causal phrases such as "caused by", "driven by", or "resulting from".
- 4–5 bullet points only.
- One sentence per bullet.

================================
SECTION 2: IMPACT ASSESSMENT
================================
ROLE:
Explain WHAT happens due to the failures.

RULES:
- Do NOT explain causes.
- Use qualitative severity only.
- Exactly three lines:
  - Operational Impact: Low/Medium/High (one sentence)
  - Safety Risk: Low/Medium/High (one sentence)
  - Performance Degradation: Low/Medium/High (one sentence)

================================
SECTION 3: REPAIR GUIDE
================================
ROLE:
Explain HOW the issue can be corrected.

RULES:
- High-level corrective actions only.
- No root cause explanation.
- No prevention, scheduling, or maintenance plans.
- 3–5 bullet points only.
- Action-oriented language.

================================
GLOBAL RULES
================================
- Do NOT repeat information across sections.
- Do NOT add conclusions.
- Do NOT add extra titles or commentary.
- If any rule is violated, regenerate internally before responding.
"""

    def get_config(self):
        return {
            "backend": self.backend,
            "model": self.ollama_model,
            "connected": {"ollama": True}
        }

    def set_model(self, model: str):
        self.ollama_model = model
        return f"Model switched to {model}"

    # ---------------- LLM CALL ---------------- #

    def _call_ollama(self, prompt: str, system_prompt: str):
        import subprocess

        full_prompt = f"{system_prompt}\n\nUser Request:\n{prompt}"

        process = subprocess.Popen(
            ["ollama", "run", self.ollama_model],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        stdout, stderr = process.communicate(input=full_prompt)

        if process.returncode != 0:
            raise Exception(stderr)

        return stdout.strip()

    def generate_direct(self, prompt: str, system_type: str = "analysis"):
        return self._call_llm(prompt, system_type=system_type)




    def _call_llm(self, prompt: str, system_type="analysis"):
        if not RUN_LLM_ANALYSIS:
            return "LLM disabled."

        if system_type == "code":
            system_prompt = self.system_prompt_code
        elif system_type == "failure":
             system_prompt = self.system_prompt_failure_combined
        else:
            system_prompt = self.system_prompt_analysis

        return self._call_ollama(prompt, system_prompt)

    # ---------------- DATA ---------------- #

    def set_df(self, df: pd.DataFrame, context_data: dict = None):
        self.df = df
        self.context_data = context_data or {}

    # ---------------- PERCEPTION ---------------- #

    def perceive(self, question: str):
        if self.df is None:
            raise ValueError("Dataset not loaded")

        correlation_context = ""
        if any(k in question.lower() for k in ["cause", "correlation", "impact"]):
            correlation_context = analyze_correlations(self.df)

        return f"""
COLUMNS: {list(self.df.columns)}
SAMPLE:
{self.df.head(1).to_string()}

CORRELATIONS:
{correlation_context}
"""

    # ---------------- DECISION ---------------- #

    def decide(self, context: str, question: str):
        skip_words = ["explain", "summary", "recommend"]
        if any(w in question.lower() for w in skip_words):
            return "result = 'NO_DATA_ANALYSIS_REQUIRED'"

        prompt = f"{context}\nTask: Generate pandas code for '{question}'"
        response = self._call_llm(prompt, system_type="code")

        code = response.replace("```python", "").replace("```", "").strip()
        return code

    # ---------------- ACTION ---------------- #

    def act(self, code: str):
        if "NO_DATA_ANALYSIS_REQUIRED" in code:
            return True, "NO_DATA"

        return execute_pandas_code(self.df, code)

    # ---------------- EXPLAIN (ROUTER) ---------------- #

    def explain(self, question: str, result):
        prompt = f"""
    User Question:
    {question}

    Computed Result:
    {result}
    """

        failure_keywords = [
            "root cause",
            "failure analysis",
            "impact assessment",
            "repair guide",
            "fault diagnosis",
            "breakdown"
        ]

        if any(k in question.lower() for k in failure_keywords):
            return self._call_llm(prompt, system_type="failure")

        # Non-failure analysis
        return self._call_llm(prompt, system_type="analysis")


    # ---------------- RUN ---------------- #

    def run(self, question: str):
        context = self.perceive(question)
        code = self.decide(context, question)
        success, result = self.act(code)

        if not success:
            return f"Execution Error: {result}"

        response = self.explain(question, result)
        self.memory.append({"q": question, "a": response})
        return response


# ---------- INSTANCE ----------
agent_instance = DataAnalystAgent()
