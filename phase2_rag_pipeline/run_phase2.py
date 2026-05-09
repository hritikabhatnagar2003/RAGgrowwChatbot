"""
End-to-End Runner for Phase 2.2 RAG Pipeline.
Connects Retriever (2.2.1), Prompt Builder (2.2.2), and Generator (2.2.3).
"""

import sys
import logging

from retriever import Retriever
from prompt_builder import build_context, get_system_prompt, build_user_prompt
from generator import Generator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_rag_pipeline(query: str):
    logger.info(f"\n{'='*80}\nPROCESSING QUERY: '{query}'\n{'='*80}")
    
    # 1. Initialize components
    try:
        retriever = Retriever()
        generator = Generator()
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        return

    # 2. Retrieve context
    chunks = retriever.retrieve(query)
    if not chunks:
        logger.warning("No relevant chunks retrieved. Fallback triggered.")
        print("\n[Assistant]: I don't have this information in my current sources. Please check the official AMC website.")
        return

    # 3. Build Prompts
    context_str = build_context(chunks)
    system_prompt = get_system_prompt()
    user_prompt = build_user_prompt(context_str, query)
    
    # Extract metadata to pass to the generator for potential programmatic fixing
    context_metadata = [chunk["metadata"] for chunk in chunks]

    # 4. Generate Answer
    result = generator.generate(system_prompt, user_prompt, context_metadata)
    
    # 5. Output
    print("\n[Assistant]:")
    print("-" * 60)
    print(result["answer"])
    print("-" * 60)
    print(f"Status: {result['status']} | Retries: {result.get('retries', 0)}")

if __name__ == "__main__":
    test_queries = [
        "What is the expense ratio of HDFC Mid-Cap Fund?",
        "How do I invest in HDFC ELSS Tax Saver Fund?",
        # A query that should be refused (advisory, will be handled properly in Phase 3, 
        # but let's see how the RAG handles it now with the strict prompt)
        "Should I invest in HDFC Small Cap Fund?", 
    ]
    
    for q in test_queries:
        run_rag_pipeline(q)
