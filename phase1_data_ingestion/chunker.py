"""
Phase 1.2.5 — Text Chunking Module
Splits cleaned documents into overlapping chunks using LangChain's
RecursiveCharacterTextSplitter, attaches metadata, and serializes to JSONL.
"""

import json
import os
import logging

from langchain_text_splitters import RecursiveCharacterTextSplitter

import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def load_manifest_lookup() -> dict:
    with open(config.URLS_MANIFEST, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    return {entry["doc_id"]: entry for entry in manifest}


def chunk_document(text, doc_id, metadata, chunk_size=None, chunk_overlap=None):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size or config.CHUNK_SIZE,
        chunk_overlap=chunk_overlap or config.CHUNK_OVERLAP,
        separators=config.CHUNK_SEPARATORS,
        length_function=len,
        is_separator_regex=False,
    )
    text_chunks = splitter.split_text(text)
    chunks = []
    for i, chunk_text in enumerate(text_chunks):
        if len(chunk_text.strip()) < config.MIN_CHUNK_LENGTH:
            continue
        chunk_record = {
            "text": chunk_text.strip(),
            "metadata": {
                "doc_id": doc_id,
                "chunk_index": i,
                "source_url": metadata.get("url", ""),
                "doc_type": metadata.get("doc_type", "scheme_page"),
                "scheme_name": metadata.get("scheme_name", ""),
                "fund_category": metadata.get("fund_category", ""),
                "plan_type": metadata.get("plan_type", "Direct Growth"),
                "last_updated": metadata.get("last_accessed", ""),
            },
        }
        chunks.append(chunk_record)
    return chunks


def chunk_all():
    config.ensure_directories()
    manifest_lookup = load_manifest_lookup()
    cleaned_files = sorted([f for f in os.listdir(config.CLEANED_DIR) if f.endswith(".txt")])

    if not cleaned_files:
        logger.warning("No cleaned files found. Run cleaner first.")
        return {"total_chunks": 0, "chunks_per_doc": {}, "output_path": ""}

    all_chunks = []
    chunks_per_doc = {}
    logger.info(f"Chunking {len(cleaned_files)} cleaned documents...")

    for filename in cleaned_files:
        doc_id = filename.replace(".txt", "")
        cleaned_path = os.path.join(config.CLEANED_DIR, filename)
        with open(cleaned_path, "r", encoding="utf-8") as f:
            text = f.read()
        metadata = manifest_lookup.get(doc_id, {})
        chunks = chunk_document(text, doc_id, metadata)
        all_chunks.extend(chunks)
        chunks_per_doc[doc_id] = len(chunks)
        scheme_name = metadata.get("scheme_name", doc_id)
        logger.info(f"  ✓ {scheme_name}: {len(chunks)} chunks")

    output_path = os.path.join(config.CHUNKS_DIR, "all_chunks.jsonl")
    with open(output_path, "w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    logger.info("=" * 60)
    logger.info(f"Chunking complete! Total chunks: {len(all_chunks)}")
    logger.info(f"  Output: {output_path}")
    for doc_id, count in chunks_per_doc.items():
        scheme = manifest_lookup.get(doc_id, {}).get("scheme_name", doc_id)
        logger.info(f"    {scheme}: {count}")

    return {"total_chunks": len(all_chunks), "chunks_per_doc": chunks_per_doc, "output_path": output_path}


if __name__ == "__main__":
    chunk_all()
