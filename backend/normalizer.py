"""
normalizer.py

Deterministic post-processing for LLM-generated Failure Analysis outputs.
This module enforces strict separation between:
- Root Cause Analysis (WHY)
- Impact Assessment (WHAT)
- Repair Guide (HOW)

NO LLM regeneration.
CODE is the authority.
"""

def normalize_output(text: str, section_type: str) -> str:
    if not text or not text.strip():
        return "Insufficient data after normalization."

    # ---------------- CONFIG ---------------- #

    MAX_BULLETS = 8
    MAX_WORDS_PER_LINE = 50

    # Common forbidden concepts (global noise)
    FORBIDDEN_COMMON = [
        "conclusion", "recommend", "schedule", "training",
        "environment", "correlation", "percentage", "predict",
        "maintenance", "prevent", "tools", "steps", "guideline",
        "manual", "education", "bullet points", "sentence per bullet",
        "must include", "e.g.", "format:", "title:", "role:"
    ]

    SECTION_CONFIG = {
        "root_cause": {
            "title": "Root Cause Summary",
            "forbidden": FORBIDDEN_COMMON + [
                "repair", "replace", "inspect", "how to"
            ]
        },
        "impact": {
            "title": "Impact Assessment",
            "forbidden": FORBIDDEN_COMMON + [
                "cause", "caused by", "repair",
                "replace", "inspect", "due to"
            ]
        },
        "repair": {
            "title": "Repair Guide",
            "forbidden": FORBIDDEN_COMMON + [
                "cause", "caused by", "correlation",
                "frequency", "%", "impact", "due to"
            ]
        }
    }

    if section_type not in SECTION_CONFIG:
        return "Insufficient data after normalization."

    title = SECTION_CONFIG[section_type]["title"]
    forbidden = SECTION_CONFIG[section_type]["forbidden"]

    # ---------------- NORMALIZATION ---------------- #

    cleaned_bullets = []
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    for line in lines:
        lower = line.lower()

        # ❌ Remove headings, sections, numbering, markdown
        if (
            lower.startswith("#")
            or lower.startswith("section")
            or lower.startswith("root cause")
            or lower.startswith("impact assessment")
            or lower.startswith("repair guide")
            or lower.startswith("analysis")
            or lower.startswith("failure")
            or lower.startswith("title")
        ):
            continue

        # ❌ Remove long explanations / paragraphs
        if len(line.split()) > MAX_WORDS_PER_LINE:
            continue

        # ❌ Remove forbidden semantic leakage
        if any(word in lower for word in forbidden):
            continue

        # ✅ Accept only declarative content
        bullet = line.rstrip(".")
        if not bullet.startswith("-"):
            bullet = "- " + bullet

        cleaned_bullets.append(bullet)

        if len(cleaned_bullets) >= MAX_BULLETS:
            break

    # ---------------- FALLBACK ---------------- #

    if not cleaned_bullets:
        return "Insufficient data after normalization."

    # ---------------- FINAL OUTPUT ---------------- #

    return title + "\n" + "\n".join(cleaned_bullets)
