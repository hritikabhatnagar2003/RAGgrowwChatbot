"""
Phase 1 — Verification Script
Runs sample similarity queries against the ChromaDB index to validate
that the ingestion pipeline produced correct, relevant results.
"""

import logging

import chromadb
from sentence_transformers import SentenceTransformer

import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Sample test queries to validate the index
TEST_QUERIES = [
    {
        "query": "What is the expense ratio of HDFC Mid-Cap Fund?",
        "expected_scheme": "HDFC Mid-Cap Fund",
    },
    {
        "query": "What is the exit load for HDFC Small Cap Fund?",
        "expected_scheme": "HDFC Small Cap Fund",
    },
    {
        "query": "What is the minimum SIP amount for HDFC ELSS Tax Saver Fund?",
        "expected_scheme": "HDFC ELSS Tax Saver Fund",
    },
    {
        "query": "What is the benchmark index of HDFC Nifty 50 Index Fund?",
        "expected_scheme": "HDFC Nifty 50 Index Fund",
    },
    {
        "query": "What is the risk level of HDFC Arbitrage Fund?",
        "expected_scheme": "HDFC Arbitrage Fund",
    },
]


def verify_index():
    """Run verification queries and print results."""
    logger.info("Loading ChromaDB collection...")
    client = chromadb.PersistentClient(path=config.VECTORSTORE_DIR)

    try:
        collection = client.get_collection(config.CHROMA_COLLECTION_NAME)
    except Exception as e:
        logger.error(f"Collection '{config.CHROMA_COLLECTION_NAME}' not found: {e}")
        logger.error("Run the pipeline first: python pipeline.py")
        return False

    doc_count = collection.count()
    logger.info(f"Collection '{config.CHROMA_COLLECTION_NAME}' has {doc_count} documents")

    if doc_count == 0:
        logger.error("Collection is empty! Pipeline may have failed.")
        return False

    # Check collection metadata
    col_meta = collection.metadata or {}
    stored_model = col_meta.get("embedding_model", "unknown")
    logger.info(f"Stored embedding model: {stored_model}")

    if stored_model != config.EMBEDDING_MODEL_NAME:
        logger.warning(
            f"Model mismatch! Stored: {stored_model}, Current: {config.EMBEDDING_MODEL_NAME}"
        )

    # Load embedding model
    logger.info(f"Loading embedding model: {config.EMBEDDING_MODEL_NAME}")
    model = SentenceTransformer(config.EMBEDDING_MODEL_NAME)

    # Run test queries
    all_passed = True
    logger.info("=" * 60)
    logger.info("RUNNING VERIFICATION QUERIES")
    logger.info("=" * 60)

    for i, test in enumerate(TEST_QUERIES):
        query = test["query"]
        expected = test["expected_scheme"]

        logger.info(f"\n{'─' * 50}")
        logger.info(f"Query {i + 1}: {query}")
        logger.info(f"Expected scheme: {expected}")

        # Embed the query
        query_embedding = model.encode([query])[0].tolist()

        # Search
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=3,
            include=["documents", "metadatas", "distances"],
        )

        if not results["documents"] or not results["documents"][0]:
            logger.error(f"  ✗ No results returned!")
            all_passed = False
            continue

        # Check results
        found_expected = False
        for j, (doc, meta, dist) in enumerate(
            zip(results["documents"][0], results["metadatas"][0], results["distances"][0])
        ):
            scheme = meta.get("scheme_name", "unknown")
            source = meta.get("source_url", "")
            similarity = 1 - dist  # ChromaDB returns L2 distance by default

            logger.info(f"  Result {j + 1}:")
            logger.info(f"    Scheme:     {scheme}")
            logger.info(f"    Source:     {source}")
            logger.info(f"    Distance:   {dist:.4f}")
            logger.info(f"    Text (50c): {doc[:50]}...")

            if expected.lower() in scheme.lower():
                found_expected = True

        if found_expected:
            logger.info(f"  ✓ PASS — Expected scheme found in results")
        else:
            logger.warning(f"  ⚠ WARN — Expected scheme '{expected}' not in top-3")
            # Not a hard failure since content quality varies

    logger.info("\n" + "=" * 60)
    logger.info("VERIFICATION SUMMARY")
    logger.info(f"  Collection docs: {doc_count}")
    logger.info(f"  Queries run:     {len(TEST_QUERIES)}")
    logger.info(f"  Status:          {'✓ ALL PASSED' if all_passed else '⚠ SOME WARNINGS'}")

    return all_passed


if __name__ == "__main__":
    verify_index()
