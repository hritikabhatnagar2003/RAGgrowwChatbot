"""
Centralized configuration for Phase 2: RAG Pipeline.
"""

import os

# ── Base Paths ────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Point to the Phase 1 vectorstore
VECTORSTORE_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "phase1_data_ingestion", "data", "vectorstore"))

# ── Retrieval Configuration ───────────────────────────────────────────────────
CHROMA_COLLECTION_NAME = "mutual_fund_faq"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K_CHUNKS = 4

# L2 Distance threshold (lower is more similar). 
# A score of 0.8 L2 corresponds roughly to 0.6 cosine similarity for normalized vectors.
MAX_L2_DISTANCE = 0.85 

# List of known schemes to extract from queries for metadata filtering
KNOWN_SCHEMES = [
    "HDFC Mid-Cap Fund",
    "HDFC Equity Fund",
    "HDFC Large Cap Fund",
    "HDFC Silver ETF Fund of Fund",
    "HDFC Small Cap Fund",
    "HDFC Gold ETF Fund of Fund",
    "HDFC Nifty 50 Index Fund",
    "HDFC Defence Fund",
    "HDFC ELSS Tax Saver Fund",
    "HDFC Medium Term Opportunities Fund",
    "HDFC Corporate Debt Opportunities Fund",
    "HDFC Arbitrage Fund",
    "HDFC Dividend Yield Fund",
    "HDFC Banking & Financial Services Fund",
    "HDFC Children's Fund"
]

# ── LLM Generator Configuration (Phase 2.2.3) ───────────────────────────────
LLM_MODEL = "llama-3.3-70b-versatile"
LLM_TEMPERATURE = 0.1
LLM_MAX_TOKENS = 250
LLM_TOP_P = 0.9

