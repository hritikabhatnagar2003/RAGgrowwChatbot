"""
Phase 3.2: Router Module
Orchestrates the routing flow: PII Check -> Classifier -> Response.
"""

import logging
from typing import Dict, Any

from pii_filter import check_for_pii
from classifier import IntentClassifier
import router_config as config

logger = logging.getLogger(__name__)

class QueryRouter:
    """Main routing orchestrator."""

    def __init__(self):
        self.classifier = IntentClassifier()

    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Processes a query through the routing layer.
        Returns a dictionary with status and routing instructions.
        """
        # 1. PII Check
        has_pii, pii_type = check_for_pii(query)
        if has_pii:
            return {
                "route_to": "REFUSAL_HANDLER",
                "intent": "PII_DETECTED",
                "response": config.REFUSAL_PII,
                "metadata": {"pii_type": pii_type}
            }

        # 2. Intent Classification
        intent = self.classifier.classify(query)

        # 3. Route based on Taxonomy
        if intent in ["FACTUAL", "PROCEDURAL"]:
            return {
                "route_to": "RAG_PIPELINE",
                "intent": intent,
                "response": None,
                "metadata": {}
            }
            
        elif intent in ["ADVISORY", "COMPARATIVE"]:
            return {
                "route_to": "REFUSAL_HANDLER",
                "intent": intent,
                "response": config.REFUSAL_ADVISORY,
                "metadata": {}
            }
            
        elif intent == "PERFORMANCE":
            return {
                "route_to": "REFUSAL_HANDLER",
                "intent": intent,
                "response": config.REFUSAL_PERFORMANCE,
                "metadata": {}
            }
            
        else: # OUT_OF_SCOPE or default
            return {
                "route_to": "REFUSAL_HANDLER",
                "intent": "OUT_OF_SCOPE",
                "response": config.REFUSAL_OUT_OF_SCOPE,
                "metadata": {}
            }
