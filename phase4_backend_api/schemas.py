"""
Phase 4: API Schemas (Pydantic Models)
"""

from pydantic import BaseModel, Field
from typing import Optional

class ChatRequest(BaseModel):
    query: str = Field(..., description="The user's query string.")
    session_id: Optional[str] = Field(default=None, description="Optional session identifier for future chat history.")

class ChatResponse(BaseModel):
    answer: str = Field(..., description="The assistant's response.")
    query_type: str = Field(..., description="The classified intent of the query (e.g., FACTUAL, ADVISORY).")
    source_url: Optional[str] = Field(default=None, description="The URL of the source document used to answer the query.")
    refused: bool = Field(..., description="True if the query was blocked or safely refused; False if answered by RAG.")
