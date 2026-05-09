"""
Phase 3.2: LLM Intent Classifier
Uses the Groq API to classify user queries into defined taxonomy categories.
"""

import os
import logging
from typing import Optional

from dotenv import load_dotenv
from groq import Groq

import router_config as config

# Load environment variables (for GROQ_API_KEY)
load_dotenv(os.path.join(config.BASE_DIR, "..", ".env"))

logger = logging.getLogger(__name__)

class IntentClassifier:
    """Classifies queries into predefined intents to control routing."""

    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            logger.error("GROQ_API_KEY environment variable not found.")
            raise ValueError("GROQ_API_KEY is missing.")
            
        self.client = Groq(api_key=api_key)
        self.taxonomy_str = ", ".join(config.TAXONOMY_CATEGORIES[:-1]) # exclude PII_DETECTED since we regex it

    def _build_system_prompt(self) -> str:
        return f"""You are an expert intent classifier for a Mutual Fund FAQ bot.
Analyze the user's query and classify it into EXACTLY ONE of the following categories:

- FACTUAL: The user is asking for a specific, objective fact about a mutual fund (e.g., expense ratio, exit load, minimum SIP, fund manager).
- PROCEDURAL: The user is asking how to do something (e.g., how to invest, how to download a statement).
- ADVISORY: The user is asking for investment advice, recommendations, or opinions (e.g., "should I invest?", "is this good?").
- COMPARATIVE: The user is asking to compare two or more funds (e.g., "which is better?", "fund A vs fund B").
- PERFORMANCE: The user is asking about historical returns, CAGR, or NAV growth over time.
- OUT_OF_SCOPE: The user is asking something completely unrelated to mutual funds or the platform.

RULES:
1. You MUST respond with ONLY the category name.
2. Do not add punctuation, explanations, or extra words.
3. Your output must exactly match one of these: {self.taxonomy_str}"""

    def classify(self, query: str) -> str:
        """
        Calls the Groq API to classify the user's intent.
        Returns the taxonomy category.
        """
        logger.info(f"Classifying intent for query: '{query}'")
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": self._build_system_prompt()},
                    {"role": "user", "content": f"Query: {query}"}
                ],
                model=config.CLASSIFIER_MODEL,
                temperature=config.CLASSIFIER_TEMPERATURE,
                max_tokens=config.CLASSIFIER_MAX_TOKENS,
            )
            intent = response.choices[0].message.content.strip().upper()
            
            # Fallback if the LLM hallucinates a category
            if intent not in config.TAXONOMY_CATEGORIES:
                logger.warning(f"Invalid category returned by LLM: '{intent}'. Defaulting to OUT_OF_SCOPE.")
                return "OUT_OF_SCOPE"
                
            logger.info(f"Intent classified as: {intent}")
            return intent
            
        except Exception as e:
            logger.error(f"Classifier LLM error: {e}")
            # Failsafe: if the classifier fails, route to out-of-scope to be safe
            return "OUT_OF_SCOPE"
