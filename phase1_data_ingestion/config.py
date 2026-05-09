"""
Centralized configuration for Phase 1: Corpus Collection & Data Ingestion.
All constants, paths, and tunable parameters live here.
"""

import os

# ── Base Paths ────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
CLEANED_DIR = os.path.join(DATA_DIR, "cleaned")
CHUNKS_DIR = os.path.join(DATA_DIR, "chunks")
VECTORSTORE_DIR = os.path.join(DATA_DIR, "vectorstore")
URLS_MANIFEST = os.path.join(BASE_DIR, "urls.json")

# ── Scraping Configuration ────────────────────────────────────────────────────
SCRAPE_DELAY_SECONDS = 3          # Delay between page requests
SCRAPE_TIMEOUT_MS = 60000         # Playwright page timeout (60s)
MIN_CONTENT_LENGTH = 200          # Minimum chars to consider a scrape successful
MAX_RETRIES = 3                   # Retry count on failure
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]

# ── Cleaning Configuration ────────────────────────────────────────────────────
# Common boilerplate patterns to remove during cleaning
BOILERPLATE_PATTERNS = [
    "Mutual Funds Sahi Hai",
    "Download the App",
    "Install the Groww App",
    "Sign up for free",
    "Create a free account",
    "Popular Mutual Funds",
    "All rights reserved",
    "Terms and Conditions",
    "Privacy Policy",
    "Disclaimer:",
    "Groww, 46 & 47",                  # Groww office address prefix
    "CIN - U67190KA2016PTC093492",     # Groww CIN number
    "SEBI Registration No.",
    "Grievance Redressal",
    "Score Card",
    "Trending on Groww",
    "Explore all Mutual Funds",
]

# ── Chunking Configuration ─────────────────────────────────────────────────────
CHUNK_SIZE = 600               # Characters per chunk
CHUNK_OVERLAP = 120            # Overlap between consecutive chunks
CHUNK_SEPARATORS = ["\n\n", "\n", ". ", " "]
MIN_CHUNK_LENGTH = 50          # Discard chunks shorter than this

# ── Embedding Configuration ────────────────────────────────────────────────────
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

# ── ChromaDB Configuration ─────────────────────────────────────────────────────
CHROMA_COLLECTION_NAME = "mutual_fund_faq"


def ensure_directories():
    """Create all required data directories if they don't exist."""
    for directory in [RAW_DIR, CLEANED_DIR, CHUNKS_DIR, VECTORSTORE_DIR]:
        os.makedirs(directory, exist_ok=True)
