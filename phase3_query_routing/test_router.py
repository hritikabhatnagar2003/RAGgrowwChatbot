"""
Test script for Phase 3.2 Query Routing layer.
Validates PII filtering and LLM intent classification paths.
"""

import logging
from pprint import pprint
from router import QueryRouter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)

def run_tests():
    try:
        router = QueryRouter()
    except Exception as e:
        print(f"Failed to initialize router: {e}")
        return

    test_queries = [
        # 1. FACTUAL -> Should pass to RAG
        "What is the exit load for HDFC Small Cap Fund?",
        
        # 2. PROCEDURAL -> Should pass to RAG
        "How do I download my capital gains statement?",
        
        # 3. ADVISORY -> Should be refused
        "I have 50k to invest, should I put it in HDFC Mid Cap or SBI Bluechip?",
        
        # 4. COMPARATIVE -> Should be refused
        "Which fund is better between HDFC Equity and HDFC Defence?",
        
        # 5. PERFORMANCE -> Should redirect to factsheet
        "What was the 3 year CAGR for the Nifty 50 Index Fund?",
        
        # 6. PII -> Should be blocked immediately
        "Hi my PAN number is ABCDE1234F, can you help me?",
        
        # 7. OUT OF SCOPE -> Should be refused
        "What is the capital of France?"
    ]

    print("\n" + "="*80)
    print("RUNNING QUERY ROUTING TESTS")
    print("="*80)

    for i, query in enumerate(test_queries, 1):
        print(f"\n[{i}] Query: '{query}'")
        
        result = router.process_query(query)
        
        print(f"    Intent Assessed: {result['intent']}")
        print(f"    Action: {result['route_to']}")
        
        if result['route_to'] == "REFUSAL_HANDLER":
            print("    Refusal Message:")
            print("      " + result['response'].replace("\n", "\n      "))

if __name__ == "__main__":
    run_tests()
