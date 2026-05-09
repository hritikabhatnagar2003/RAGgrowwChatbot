"""
Phase 2.2.2 — Context Assembly & Prompt Engineering
Handles constructing the context block from retrieved chunks and managing
the strict system/user prompts for the Groq LLM.
"""

from typing import List, Dict, Any

def build_context(chunks: List[Dict[str, Any]]) -> str:
    """
    Concatenate retrieved chunks into a single context block.
    Prepends each chunk with its source_url and last_updated date for the LLM.
    """
    if not chunks:
        return "No relevant context found."

    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        meta = chunk.get("metadata", {})
        source_url = meta.get("source_url", "Unknown Source")
        last_updated = meta.get("last_updated", "Unknown Date")
        text = chunk.get("text", "").strip()

        chunk_str = f"[Document {i}]\nSource: {source_url}\nLast Updated: {last_updated}\nContent:\n{text}\n"
        context_parts.append(chunk_str)

    return "\n".join(context_parts)


def get_system_prompt() -> str:
    """
    Returns the strict system prompt enforcing the rules for the facts-only assistant.
    """
    return """You are a facts-only mutual fund FAQ assistant for Groww.
RULES:
1. Answer ONLY using the provided context. Do NOT use prior knowledge.
2. Maximum 3 sentences per answer.
3. Include exactly ONE source citation link from the context metadata, UNLESS you do not have the answer.
4. End every response with: "Last updated from sources: <date>"
5. NEVER provide investment advice, opinions, or recommendations.
6. NEVER compare fund performance or calculate returns.
7. If the context does not contain the answer, say EXACTLY:
   "I don't have this information in my current sources. Please check the official AMC website." Do NOT include any links.
"""


def build_user_prompt(context: str, user_query: str) -> str:
    """
    Constructs the final user prompt injecting the assembled context and query.
    """
    return f"""Context:
---
{context}
---

User Question: {user_query}

Answer (max 3 sentences, 1 citation, include last updated footer):"""
