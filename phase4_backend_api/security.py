"""
Phase 5: Security & Compliance utilities.

- PII detection (blocking)
- Output safety guardrail (blocks advice/comparisons/predictions)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PiiMatch:
    pii_type: str
    match_text: str


# Phase 5.2.1 patterns (plus a conservative account-number heuristic)
_PII_PATTERNS: dict[str, str] = {
    "PAN": r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
    "AADHAAR": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
    "PHONE": r"\b(\+91[\s-]?)?[6-9]\d{9}\b",
    "EMAIL": r"\b[\w.+-]+@[\w.-]+\.\w+\b",
    # Avoid matching years/NAV/etc by requiring a "number-y" context word nearby.
    "ACCOUNT_NO": r"\b(?:a\/c|ac|account)\D{0,10}\d{9,18}\b",
}


def detect_pii(text: str) -> Optional[PiiMatch]:
    """
    Returns the first detected PII match (type + matched text), else None.
    """
    if not text:
        return None

    for pii_type, pattern in _PII_PATTERNS.items():
        m = re.search(pattern, text, flags=re.IGNORECASE)
        if m:
            return PiiMatch(pii_type=pii_type, match_text=m.group(0))
    return None


PII_BLOCK_MESSAGE = (
    "⚠️ For your security, I cannot process messages containing personal information\n"
    "(PAN, Aadhaar, phone numbers, email, or account numbers).\n"
    "Please remove any personal details and try again."
)


_UNSAFE_OUTPUT_PATTERNS: list[str] = [
    # Advisory language
    r"\byou should\b",
    r"\bi recommend\b",
    r"\bconsider investing\b",
    r"\byou may invest\b",
    r"\bideal (to|for) you\b",
    # Comparative language
    r"\bbetter than\b",
    r"\boutperforms\b",
    r"\bsuperior\b",
    r"\bbest (fund|option)\b",
    # Return predictions
    r"\bexpected return\b",
    r"\bprojected (growth|return)\b",
    r"\bwill give\b",
]


def is_unsafe_output(text: str) -> bool:
    """
    Detects unsafe content in LLM output (advice/comparisons/predictions).
    """
    if not text:
        return False
    return any(re.search(p, text, flags=re.IGNORECASE) for p in _UNSAFE_OUTPUT_PATTERNS)


SAFETY_FALLBACK_MESSAGE = (
    "I can’t provide investment advice, comparisons, or return predictions. "
    "I can help with factual details like expense ratio, exit load, SIP minimum, or lock-in period."
)

