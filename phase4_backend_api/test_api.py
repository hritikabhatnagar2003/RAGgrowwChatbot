"""
Test script to verify the Phase 4 FastAPI Backend.
Run this script while the FastAPI server is running in another terminal.
"""

import pytest
pytest.skip("Manual API smoke-test script, not a pytest test module.", allow_module_level=True)

import requests
import json
from pprint import pprint

BASE_URL = "http://127.0.0.1:8000"

def test_health():
    print("\n--- Testing GET /api/health ---")
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        print(f"Status: {response.status_code}")
        pprint(response.json())
    except Exception as e:
        print(f"Failed to connect: {e}")

def test_examples():
    print("\n--- Testing GET /api/examples ---")
    try:
        response = requests.get(f"{BASE_URL}/api/examples")
        print(f"Status: {response.status_code}")
        pprint(response.json())
    except Exception as e:
        print(f"Failed to connect: {e}")

def test_chat(query: str, desc: str):
    print(f"\n--- Testing POST /api/chat ({desc}) ---")
    payload = {"query": query}
    try:
        response = requests.post(f"{BASE_URL}/api/chat", json=payload)
        print(f"Status: {response.status_code}")
        
        data = response.json()
        print("\nResponse:")
        print(f"  Intent:  {data.get('query_type')}")
        print(f"  Refused: {data.get('refused')}")
        print(f"  Source:  {data.get('source_url')}")
        print("\n  Answer:")
        print("  " + data.get('answer', '').replace('\n', '\n  '))
        
    except Exception as e:
        print(f"Failed to connect: {e}")

if __name__ == "__main__":
    # Check health and examples
    test_health()
    test_examples()
    
    # Test 1: Factual (Should pass to RAG)
    test_chat("What is the expense ratio of HDFC Mid-Cap Fund?", "Factual Query")
    
    # Test 2: Advisory (Should trigger Refusal Handler)
    test_chat("Should I invest in HDFC Small Cap Fund?", "Advisory Query")
    
    # Test 3: PII (Should trigger Refusal Handler instantly)
    test_chat("My phone is 9876543210, please call me", "PII Query")
