"""
Phase 3.2: PII Filter
Runs fast regex checks to prevent sensitive data (PAN, Aadhaar, Email, Phone)
from being sent to the LLM or processed further.
"""

import re
import logging
from typing import Tuple, Optional

import router_config as config

logger = logging.getLogger(__name__)

def check_for_pii(query: str) -> Tuple[bool, Optional[str]]:
    """
    Scans the query for PII patterns defined in config.
    Returns (True, PII_TYPE) if found, (False, None) otherwise.
    """
    for pii_type, pattern in config.PII_PATTERNS.items():
        if re.search(pattern, query, re.IGNORECASE):
            logger.warning(f"PII Detected: Blocked query containing {pii_type} pattern.")
            return True, pii_type
            
    return False, None
