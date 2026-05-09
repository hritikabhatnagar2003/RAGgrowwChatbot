"""
Centralized Configuration for Phase 3: Query Routing & Refusal Handling
"""

import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Taxonomy ────────────────────────────────────────────────────────────────
TAXONOMY_CATEGORIES = [
    "FACTUAL", 
    "ADVISORY", 
    "COMPARATIVE", 
    "PERFORMANCE", 
    "PROCEDURAL", 
    "OUT_OF_SCOPE", 
    "PII_DETECTED"
]

# ── PII Patterns (Regex) ────────────────────────────────────────────────────
PII_PATTERNS = {
    "PAN": r'[A-Z]{5}[0-9]{4}[A-Z]',
    "AADHAAR": r'\b\d{4}\s?\d{4}\s?\d{4}\b',
    "EMAIL": r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+',
    "PHONE": r'\b[6-9]\d{9}\b'  # Indian 10-digit mobile number
}

# ── Refusal Templates ───────────────────────────────────────────────────────
REFUSAL_ADVISORY = """I'm a facts-only assistant and cannot provide investment advice or fund comparisons.
For investment guidance, please consult a SEBI-registered financial advisor.

📚 Learn more: https://www.amfiindia.com/investor-corner/knowledge-center.html

Facts-only. No investment advice."""

REFUSAL_PERFORMANCE = f"""I cannot provide performance data or return calculations directly.
You can view the official performance data in the scheme factsheet on the Groww Mutual Fund portal.

📄 Portal: https://groww.in/mutual-funds

Last updated from sources: {datetime.now().strftime('%Y-%m-%d')}"""

REFUSAL_OUT_OF_SCOPE = """This question is outside my scope. I can only answer factual questions about mutual fund schemes.

Try asking about expense ratios, exit loads, SIP amounts, or lock-in periods."""

REFUSAL_PII = """Query blocked. Please do not share sensitive personal information (like PAN, Aadhaar, Email, or Phone numbers) in this chat for your security."""

# ── LLM Classifier Configuration ────────────────────────────────────────────
CLASSIFIER_MODEL = "llama-3.3-70b-versatile"
CLASSIFIER_TEMPERATURE = 0.0  # Zero creativity for strict classification
CLASSIFIER_MAX_TOKENS = 15
