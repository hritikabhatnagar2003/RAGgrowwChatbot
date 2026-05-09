"""
Phase 1.2.6 — Embedding Generation & ChromaDB Indexing Module
Generates embeddings with sentence-transformers and indexes chunks into ChromaDB.
"""

import json
import os
import sys
import logging

import chromadb
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def load_chunks(chunks_path=None):
    """Load chunks from the JSONL file."""
    path = chunks_path or os.path.join(config.CHUNKS_DIR, "all_chunks.jsonl")
    chunks = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))
    logger.info(f"Loaded {len(chunks)} chunks from {path}")
    return chunks


def create_embeddings(chunks, model=None):
    """Generate embeddings for all chunk texts."""
    if model is None:
        logger.info(f"Loading embedding model: {config.EMBEDDING_MODEL_NAME}")
        model = SentenceTransformer(config.EMBEDDING_MODEL_NAME)

    texts = [chunk["text"] for chunk in chunks]
    logger.info(f"Generating embeddings for {len(texts)} chunks...")
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)
    logger.info(f"Generated {len(embeddings)} embeddings (dim={embeddings.shape[1]})")
    return embeddings.tolist()


def index_to_chromadb(chunks, embeddings, rebuild=False):
    """Index chunks + embeddings into a persistent ChromaDB collection."""
    config.ensure_directories()

    client = chromadb.PersistentClient(path=config.VECTORSTORE_DIR)

    # Handle rebuild flag
    if rebuild:
        try:
            client.delete_collection(config.CHROMA_COLLECTION_NAME)
            logger.info(f"Deleted existing collection '{config.CHROMA_COLLECTION_NAME}'")
        except Exception:
            pass

    # Create or get collection with embedding model metadata
    collection = client.get_or_create_collection(
        name=config.CHROMA_COLLECTION_NAME,
        metadata={
            "embedding_model": config.EMBEDDING_MODEL_NAME,
            "embedding_dimension": str(config.EMBEDDING_DIMENSION),
            "description": "Mutual Fund FAQ chunks from Groww HDFC scheme pages",
        },
    )

    # Prepare data for batch insertion
    ids = []
    documents = []
    metadatas = []
    embedding_list = []

    for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        doc_id = chunk["metadata"].get("doc_id", "unknown")
        chunk_idx = chunk["metadata"].get("chunk_index", i)
        unique_id = f"{doc_id}_chunk_{chunk_idx}"

        ids.append(unique_id)
        documents.append(chunk["text"])
        metadatas.append(chunk["metadata"])
        embedding_list.append(emb)

    # Batch add (ChromaDB recommends batches of ~5000)
    batch_size = 500
    total_added = 0

    for start in range(0, len(ids), batch_size):
        end = min(start + batch_size, len(ids))
        collection.add(
            ids=ids[start:end],
            documents=documents[start:end],
            metadatas=metadatas[start:end],
            embeddings=embedding_list[start:end],
        )
        total_added += end - start
        logger.info(f"  Indexed batch {start}–{end} ({total_added}/{len(ids)})")

    logger.info("=" * 60)
    logger.info(f"Indexing complete!")
    logger.info(f"  Collection: {config.CHROMA_COLLECTION_NAME}")
    logger.info(f"  Total documents: {collection.count()}")
    logger.info(f"  Storage: {config.VECTORSTORE_DIR}")

    return collection


def index_all(rebuild=False):
    """Full indexing pipeline: load chunks → embed → store in ChromaDB."""
    chunks = load_chunks()
    if not chunks:
        logger.error("No chunks to index. Run chunker first.")
        return None

    embeddings = create_embeddings(chunks)
    collection = index_to_chromadb(chunks, embeddings, rebuild=rebuild)
    return collection


if __name__ == "__main__":
    rebuild_flag = "--rebuild" in sys.argv
    index_all(rebuild=rebuild_flag)
