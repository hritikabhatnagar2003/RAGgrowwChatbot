"""Temporary analysis script to understand data characteristics for Phase 2 retrieval strategy."""
import json
from collections import Counter

# Load chunks
chunks = []
with open("data/chunks/all_chunks.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            chunks.append(json.loads(line))

print(f"Total chunks: {len(chunks)}")
unique_schemes = set(c["metadata"]["scheme_name"] for c in chunks)
unique_cats = set(c["metadata"]["fund_category"] for c in chunks)
print(f"Unique schemes: {len(unique_schemes)}")
print(f"Unique categories: {len(unique_cats)}")

# Chunk length distribution
lengths = [len(c["text"]) for c in chunks]
print(f"\nChunk length stats:")
print(f"  Min: {min(lengths)}")
print(f"  Max: {max(lengths)}")
print(f"  Avg: {sum(lengths) // len(lengths)}")
print(f"  Median: {sorted(lengths)[len(lengths) // 2]}")

# Chunks per scheme
scheme_counts = Counter(c["metadata"]["scheme_name"] for c in chunks)
print(f"\nChunks per scheme:")
for scheme, count in scheme_counts.most_common():
    print(f"  {scheme}: {count}")

# Content analysis - keyword coverage
keywords = {
    "expense_ratio": ["expense ratio", "TER"],
    "exit_load": ["exit load"],
    "min_sip": ["minimum sip", "min sip", "sip amount"],
    "nav": ["NAV", "net asset value"],
    "aum": ["AUM", "assets under management"],
    "fund_manager": ["fund manager"],
    "benchmark": ["benchmark"],
    "risk": ["riskometer", "risk level", "very high risk", "high risk", "moderate risk", "low risk"],
    "lock_in": ["lock-in", "lock in", "lockin"],
}

print("\nKeyword coverage across chunks:")
for field, kws in keywords.items():
    matching = sum(1 for c in chunks if any(kw.lower() in c["text"].lower() for kw in kws))
    pct = matching * 100 // len(chunks)
    print(f"  {field}: {matching} chunks ({pct}%)")

# Check for duplicate/near-duplicate content across schemes
print(f"\nContent similarity check (identical first-50-char prefixes):")
prefixes = Counter(c["text"][:50].lower().strip() for c in chunks)
dupes = {k: v for k, v in prefixes.items() if v > 2}
print(f"  Prefixes appearing 3+ times: {len(dupes)}")
for prefix, count in sorted(dupes.items(), key=lambda x: -x[1])[:10]:
    print(f'    "{prefix}..." x{count}')

# Sample metadata
print(f"\nSample metadata keys: {list(chunks[0]['metadata'].keys())}")
print(f"Sample metadata: {json.dumps(chunks[0]['metadata'], indent=2)}")

# Check how many chunks per scheme contain the scheme name
print("\n\nScheme name presence in chunk text:")
for scheme in sorted(unique_schemes):
    scheme_chunks = [c for c in chunks if c["metadata"]["scheme_name"] == scheme]
    with_name = sum(1 for c in scheme_chunks if scheme.lower() in c["text"].lower())
    print(f"  {scheme}: {with_name}/{len(scheme_chunks)} chunks mention the scheme name")
