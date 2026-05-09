"""
Phase 1 — End-to-End Pipeline Orchestrator
Runs all steps: scrape → clean → chunk → index.
Supports running individual steps or the full pipeline.
"""

import argparse
import logging
import sys
import time

import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

VALID_STEPS = ["scrape", "clean", "chunk", "index"]


def run_scrape():
    """Step 1: Scrape all URLs from the manifest."""
    logger.info("=" * 60)
    logger.info("STEP 1: SCRAPING")
    logger.info("=" * 60)
    from scraper import scrape_all
    return scrape_all()


def run_clean():
    """Step 2: Clean all raw documents."""
    logger.info("=" * 60)
    logger.info("STEP 2: CLEANING")
    logger.info("=" * 60)
    from cleaner import clean_all
    return clean_all()


def run_chunk():
    """Step 3: Chunk all cleaned documents."""
    logger.info("=" * 60)
    logger.info("STEP 3: CHUNKING")
    logger.info("=" * 60)
    from chunker import chunk_all
    return chunk_all()


def run_index(rebuild=False):
    """Step 4: Generate embeddings and index into ChromaDB."""
    logger.info("=" * 60)
    logger.info("STEP 4: INDEXING")
    logger.info("=" * 60)
    from indexer import index_all
    return index_all(rebuild=rebuild)


def run_pipeline(step=None, rebuild=False):
    """
    Run the full pipeline or a specific step.

    Args:
        step: Optional specific step to run ('scrape', 'clean', 'chunk', 'index').
        rebuild: If True, clear existing ChromaDB collection before indexing.
    """
    config.ensure_directories()
    start_time = time.time()

    logger.info("╔══════════════════════════════════════════════════════════╗")
    logger.info("║  Phase 1: Corpus Collection & Data Ingestion Pipeline   ║")
    logger.info("╚══════════════════════════════════════════════════════════╝")

    if step:
        logger.info(f"Running single step: {step}")
        if step == "scrape":
            run_scrape()
        elif step == "clean":
            run_clean()
        elif step == "chunk":
            run_chunk()
        elif step == "index":
            run_index(rebuild=rebuild)
        else:
            logger.error(f"Unknown step: {step}. Valid steps: {VALID_STEPS}")
            sys.exit(1)
    else:
        logger.info("Running full pipeline: scrape → clean → chunk → index")
        run_scrape()
        run_clean()
        run_chunk()
        run_index(rebuild=rebuild)

    elapsed = time.time() - start_time
    logger.info("=" * 60)
    logger.info(f"Pipeline completed in {elapsed:.1f} seconds ({elapsed / 60:.1f} minutes)")


def main():
    parser = argparse.ArgumentParser(
        description="Phase 1: Corpus Collection & Data Ingestion Pipeline"
    )
    parser.add_argument(
        "--step",
        choices=VALID_STEPS,
        help="Run a specific step only (default: run all steps)",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Clear existing ChromaDB collection before indexing",
    )
    args = parser.parse_args()
    run_pipeline(step=args.step, rebuild=args.rebuild)


if __name__ == "__main__":
    main()
