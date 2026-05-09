"""Test retrieval patterns against ChromaDB to understand score distributions.

This file is named like a test, so pytest will try to collect it. If the local
vectorstore/collection isn't present (common in fresh checkouts/CI), we skip.
"""

import pytest

import chromadb
from chromadb.errors import NotFoundError
from sentence_transformers import SentenceTransformer

client = chromadb.PersistentClient(path="data/vectorstore")
try:
    collection = client.get_collection("mutual_fund_faq")
except NotFoundError:
    pytest.skip(
        "Chroma collection 'mutual_fund_faq' not found; run Phase 1 ingestion first.",
        allow_module_level=True,
    )

print(f"Collection count: {collection.count()}")
print(f"Collection metadata: {collection.metadata}")

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Test different query types
test_queries = [
    # Scheme-specific factual
    "What is the expense ratio of HDFC Mid-Cap Fund?",
    # Different scheme-specific
    "What is the exit load for HDFC Small Cap Fund?",
    # Generic factual (no scheme name)
    "What is an exit load in mutual funds?",
    # Very generic keyword
    "expense ratio",
    # Scheme name only
    "HDFC ELSS Tax Saver Fund",
    # Category-based
    "debt fund corporate bond",
    # Procedural
    "How to invest in mutual funds on Groww?",
    # Advisory (should be refused but let's see what retrieval gives)
    "Should I invest in HDFC Mid Cap Fund?",
]

for q in test_queries:
    emb = model.encode([q])[0].tolist()
    results = collection.query(
        query_embeddings=[emb], n_results=5,
        include=["metadatas", "distances", "documents"]
    )
    schemes = [m["scheme_name"] for m in results["metadatas"][0]]
    dists = results["distances"][0]
    unique_schemes = len(set(schemes))
    
    print(f'\n{"="*60}')
    print(f'Query: "{q}"')
    print(f"  Top-5 L2 distances: {[f'{d:.3f}' for d in dists]}")
    print(f"  Schemes in top-5: {schemes}")
    print(f"  Unique schemes: {unique_schemes}")
    print(f"  Top result preview: {results['documents'][0][0][:120]}...")
    
    # Check if results from same scheme cluster together
    if unique_schemes == 1:
        print(f"  [!] All results from single scheme -- may need diversity")
    elif unique_schemes >= 4:
        print(f"  [!] Results scattered across schemes -- weak relevance signal")

# Test metadata filtering
print(f'\n{"="*60}')
print("METADATA FILTERING TEST:")
emb = model.encode(["expense ratio"])[0].tolist()

# Without filter
results_no_filter = collection.query(query_embeddings=[emb], n_results=3, include=["metadatas", "distances"])
print(f"\n  No filter - schemes: {[m['scheme_name'] for m in results_no_filter['metadatas'][0]]}")
print(f"  No filter - dists: {[f'{d:.3f}' for d in results_no_filter['distances'][0]]}")

# With scheme filter
results_filtered = collection.query(
    query_embeddings=[emb], n_results=3,
    where={"scheme_name": "HDFC Mid-Cap Fund"},
    include=["metadatas", "distances"]
)
print(f"\n  Filter(HDFC Mid-Cap) - schemes: {[m['scheme_name'] for m in results_filtered['metadatas'][0]]}")
print(f"  Filter(HDFC Mid-Cap) - dists: {[f'{d:.3f}' for d in results_filtered['distances'][0]]}")

# With category filter
results_cat = collection.query(
    query_embeddings=[emb], n_results=3,
    where={"fund_category": "ELSS (Tax Saving)"},
    include=["metadatas", "distances"]
)
print(f"\n  Filter(ELSS) - schemes: {[m['scheme_name'] for m in results_cat['metadatas'][0]]}")
print(f"  Filter(ELSS) - dists: {[f'{d:.3f}' for d in results_cat['distances'][0]]}")
