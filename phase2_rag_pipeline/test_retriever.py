"""
Test script for the Phase 2 Retriever Module.
Verifies scheme extraction, strict retrieval rules, and distance thresholding.
"""

import sys
import logging
from pprint import pprint

from retriever import Retriever

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_tests():
    try:
        retriever = Retriever()
    except Exception as e:
        logger.error(f"Failed to initialize retriever: {e}")
        sys.exit(1)

    test_queries = [
        # 1. Scheme-specific factual
        "What is the expense ratio of HDFC Mid-Cap Fund?",
        # 2. Scheme-specific with partial alias
        "Tell me about exit load for hdfc small cap",
        # 3. Scheme-specific procedural
        "How do I invest in HDFC ELSS Tax Saver?",
        # 4. Out of scope / Generic (Should return empty due to strict rule)
        "What is an expense ratio?",
        # 5. Out of scope (Should return empty)
        "Tell me a joke",
        # 6. Nonsense query with scheme (Should return empty due to distance threshold)
        "Why is the sky blue in HDFC Equity Fund?"
    ]

    print("\n" + "="*80)
    print("RUNNING RETRIEVER TESTS")
    print("="*80)

    for i, query in enumerate(test_queries, 1):
        print(f"\n[{i}] Query: '{query}'")
        
        # Test extraction independently for logging
        detected_scheme = retriever.extractor.extract(query)
        print(f"    Detected Scheme: {detected_scheme}")
        
        # Test full retrieval
        results = retriever.retrieve(query)
        
        if not results:
            print("    Status: NO RESULTS RETURNED (Strict rule or thresholding applied)")
        else:
            print(f"    Status: {len(results)} CHUNKS RETRIEVED")
            print("    Top Result:")
            top = results[0]
            print(f"      - Distance: {top['distance']:.4f}")
            print(f"      - Source: {top['metadata']['source_url']}")
            print(f"      - Text Preview: {top['text'][:120]}...")

if __name__ == "__main__":
    run_tests()
