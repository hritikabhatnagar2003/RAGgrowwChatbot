"""
Phase 2.2.1 — Retriever Module
Handles embedding queries, applying metadata filters based on scheme name extraction,
and retrieving relevant chunks from ChromaDB.
"""

import logging
import re
from typing import List, Dict, Any

import chromadb
from sentence_transformers import SentenceTransformer
import torch

# Limit PyTorch to 1 thread to drastically reduce memory usage on Render free tier
torch.set_num_threads(1)

import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class SchemeExtractor:
    """Extracts known scheme names from user queries for metadata filtering."""
    
    def __init__(self, known_schemes: List[str]):
        self.known_schemes = known_schemes
        # Map lowercased variations to the official scheme name
        self.scheme_map = {s.lower(): s for s in known_schemes}
        
        # Build common abbreviations/aliases map for better matching
        self.aliases = self._build_aliases(known_schemes)
        
    def _build_aliases(self, schemes: List[str]) -> Dict[str, str]:
        aliases = {}
        for scheme in schemes:
            lower_scheme = scheme.lower()
            # E.g., "hdfc mid-cap fund" -> "mid cap", "mid-cap"
            # Remove "hdfc" and "fund" to find core keywords
            core_name = lower_scheme.replace("hdfc", "").replace("fund", "").replace("direct", "").replace("growth", "").strip()
            if core_name:
                aliases[core_name] = scheme
                # Also without hyphens
                aliases[core_name.replace("-", " ")] = scheme
        return aliases

    def extract(self, query: str) -> str:
        """
        Extract the scheme name from the query.
        Returns the official scheme name if found, otherwise None.
        """
        lower_query = query.lower()
        
        # 1. Exact match attempt
        for scheme_lower, official_name in self.scheme_map.items():
            if scheme_lower in lower_query:
                return official_name
                
        # 2. Alias match attempt (e.g., "mid cap")
        # Sort aliases by length descending to match longest phrases first
        sorted_aliases = sorted(self.aliases.keys(), key=len, reverse=True)
        for alias in sorted_aliases:
            # Require word boundaries to prevent partial matches
            pattern = r'\b' + re.escape(alias) + r'\b'
            if re.search(pattern, lower_query):
                return self.aliases[alias]
                
        return None


class Retriever:
    """Core Retrieval Module interacting with ChromaDB."""
    
    def __init__(self):
        logger.info(f"Connecting to ChromaDB at {config.VECTORSTORE_DIR}")
        try:
            self.client = chromadb.PersistentClient(path=config.VECTORSTORE_DIR)
            self.collection = self.client.get_collection(config.CHROMA_COLLECTION_NAME)
        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB or collection not found: {e}")
            raise RuntimeError(f"Ensure Phase 1 ingestion has been run. Details: {e}")

        logger.info(f"Loading embedding model: {config.EMBEDDING_MODEL_NAME}")
        self.model = SentenceTransformer(config.EMBEDDING_MODEL_NAME)
        self.extractor = SchemeExtractor(config.KNOWN_SCHEMES)

    def retrieve(self, query: str, top_k: int = None, max_distance: float = None) -> List[Dict[str, Any]]:
        """
        Embed the query and retrieve relevant chunks.
        Strict rule applied: If no scheme name is detected in the query, return empty.
        """
        top_k = top_k or config.TOP_K_CHUNKS
        max_distance = max_distance or config.MAX_L2_DISTANCE

        # 1. Extract Scheme Name
        detected_scheme = self.extractor.extract(query)
        
        # STRICT RULE: No global search if no scheme is specified
        if not detected_scheme:
            logger.warning("No scheme name detected in query. Global search is disabled.")
            return []

        logger.info(f"Query: '{query}' -> Detected Scheme: '{detected_scheme}'")

        # 2. Embed the query
        query_embedding = self.model.encode([query])[0].tolist()

        # 3. Query ChromaDB with metadata filter
        where_filter = {"scheme_name": detected_scheme}
        
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )
        except Exception as e:
            logger.error(f"Error querying ChromaDB: {e}")
            return []

        # 4. Format and threshold results
        retrieved_chunks = []
        if not results["documents"] or not results["documents"][0]:
            return retrieved_chunks

        for i, (doc, meta, dist) in enumerate(zip(results["documents"][0], results["metadatas"][0], results["distances"][0])):
            # Apply distance threshold to filter out irrelevant chunks
            if dist > max_distance:
                logger.debug(f"Chunk {i} rejected (distance {dist:.3f} > {max_distance})")
                continue
                
            chunk_data = {
                "text": doc,
                "metadata": meta,
                "distance": float(dist)
            }
            retrieved_chunks.append(chunk_data)

        logger.info(f"Retrieved {len(retrieved_chunks)} relevant chunks (filtered from {len(results['documents'][0])})")
        return retrieved_chunks
