"""
Phase 2.2.3 — LLM Generator Module (Groq API)
Handles sending prompts to Groq, streaming/receiving responses, and
post-processing validation (ensuring exactly one citation and date footer).
"""

import os
import re
import logging
from typing import Dict, Any, Optional

from dotenv import load_dotenv
from groq import Groq

import config

# Load environment variables (for GROQ_API_KEY)
load_dotenv(os.path.join(config.BASE_DIR, "..", ".env"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class Generator:
    """Generator module utilizing Groq API to generate factual responses."""

    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            logger.error("GROQ_API_KEY environment variable not found. Please set it in the .env file.")
            raise ValueError("GROQ_API_KEY is missing.")
            
        self.client = Groq(api_key=api_key)

    def _validate_response(self, response_text: str) -> bool:
        """
        Post-processing validation per architecture:
        1. Validates that the response contains exactly one URL.
        2. Validates that the footer "Last updated from sources: <date>" is present.
        """
        # 1. Check for exactly one URL (unless it's a refusal)
        url_pattern = r'https?://[^\s]+'
        urls_found = re.findall(url_pattern, response_text)
        
        is_refusal = "I don't have this information" in response_text
        
        if is_refusal:
            if len(urls_found) > 0:
                logger.warning(f"Validation failed: Found URLs in a refusal response.")
                return False
        else:
            if len(urls_found) != 1:
                logger.warning(f"Validation failed: Found {len(urls_found)} URLs, expected exactly 1.")
                return False

        # 2. Check for the footer
        footer_pattern = r'Last updated from sources: \d{4}-\d{2}-\d{2}'
        if not re.search(footer_pattern, response_text):
            logger.warning("Validation failed: Missing or malformed 'Last updated from sources' footer.")
            return False

        return True

    def _fix_response_programmatically(self, response_text: str, context_metadata: list) -> str:
        """
        Attempts to programmatically append missing footer or citation if validation fails.
        """
        logger.info("Attempting programmatic fix of the LLM response...")
        fixed_text = response_text.strip()
        
        # Check URL
        url_pattern = r'https?://[^\s]+'
        urls_found = re.findall(url_pattern, fixed_text)
        
        # If no URL, try to pull from the top context chunk
        if len(urls_found) == 0 and context_metadata:
            source_url = context_metadata[0].get("source_url")
            if source_url:
                fixed_text += f"\n\nSource: {source_url}"
                logger.info("Appended missing source URL.")
                
        # Check Footer
        footer_pattern = r'Last updated from sources: \d{4}-\d{2}-\d{2}'
        if not re.search(footer_pattern, fixed_text) and context_metadata:
            date = context_metadata[0].get("last_updated", "Unknown")
            # If the response ended abruptly, add newlines
            if not fixed_text.endswith("\n"):
                fixed_text += "\n"
            fixed_text += f"Last updated from sources: {date}"
            logger.info("Appended missing date footer.")
            
        return fixed_text

    def generate(self, system_prompt: str, user_prompt: str, context_metadata: list) -> Dict[str, Any]:
        """
        Calls the Groq API to generate an answer. 
        Implements validation and a 1-time retry mechanism.
        """
        logger.info(f"Generating response using {config.LLM_MODEL}...")
        
        try:
            # First attempt
            response = self._call_api(system_prompt, user_prompt)
            answer = response.choices[0].message.content
            
            if self._validate_response(answer):
                logger.info("Response validated successfully on first attempt.")
                return {"answer": answer, "status": "success", "retries": 0}
                
            # If validation fails, attempt a strict retry
            logger.warning("First attempt validation failed. Retrying with stricter instructions...")
            retry_system_prompt = system_prompt + "\n\nCRITICAL REMINDER: You MUST include exactly one source URL from the context and end exactly with 'Last updated from sources: <date>'."
            
            retry_response = self._call_api(retry_system_prompt, user_prompt)
            retry_answer = retry_response.choices[0].message.content
            
            if self._validate_response(retry_answer):
                logger.info("Retry response validated successfully.")
                return {"answer": retry_answer, "status": "success", "retries": 1}
                
            # If retry also fails, attempt programmatic fix
            logger.warning("Retry validation failed. Applying programmatic fix.")
            final_answer = self._fix_response_programmatically(retry_answer, context_metadata)
            
            return {"answer": final_answer, "status": "programmatic_fix", "retries": 1}

        except Exception as e:
            logger.error(f"Groq API Error: {e}")
            return {
                "answer": "An error occurred while communicating with the LLM. Please try again later.",
                "status": "error",
                "error": str(e)
            }

    def _call_api(self, system_prompt: str, user_prompt: str):
        return self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                }
            ],
            model=config.LLM_MODEL,
            temperature=config.LLM_TEMPERATURE,
            max_tokens=config.LLM_MAX_TOKENS,
            top_p=config.LLM_TOP_P,
        )
