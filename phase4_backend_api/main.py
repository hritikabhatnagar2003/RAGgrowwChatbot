"""
Phase 4: FastAPI Backend Application
Glues together Phase 3 (Routing) and Phase 2 (RAG Pipeline).
"""

import sys
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add sibling directories and parent to Python path so we can import our previous work
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(BASE_DIR, "..")))
sys.path.append(os.path.abspath(os.path.join(BASE_DIR, "..", "phase3_query_routing")))
sys.path.append(os.path.abspath(os.path.join(BASE_DIR, "..", "phase2_rag_pipeline")))

from phase4_backend_api.schemas import ChatRequest, ChatResponse
from router import QueryRouter
from retriever import Retriever
from prompt_builder import build_context, get_system_prompt, build_user_prompt
from generator import Generator
from phase4_backend_api.rate_limit import RateLimitMiddleware
from phase4_backend_api.security import (
    detect_pii,
    is_unsafe_output,
    PII_BLOCK_MESSAGE,
    SAFETY_FALLBACK_MESSAGE,
)

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances of our ML/Routing modules
router = None
retriever = None
generator = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load models and clients on startup."""
    global router, retriever, generator
    logger.info("Initializing Backend Services...")
    try:
        if os.environ.get("TEST_MODE") == "1":
            # Test doubles: no external API calls / vectorstore required.
            class _FakeRouter:
                def process_query(self, query: str):
                    return {"route_to": "RAG_PIPELINE", "intent": "FACTUAL", "response": None, "metadata": {}}

            class _FakeRetriever:
                def retrieve(self, query: str):
                    return [{"text": "Dummy context.", "metadata": {"source_url": "https://example.com", "last_updated": "2026-05-03"}}]

            class _FakeGenerator:
                def generate(self, system_prompt: str, user_prompt: str, context_metadata: list):
                    # Intentionally safe by default.
                    return {
                        "answer": "Dummy answer.\n\nSource: https://example.com\nLast updated from sources: 2026-05-03",
                        "status": "success",
                        "retries": 0,
                    }

            router = _FakeRouter()
            retriever = _FakeRetriever()
            generator = _FakeGenerator()
        else:
            router = QueryRouter()
            retriever = Retriever()
            generator = Generator()
        logger.info("All services initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise RuntimeError("Startup failed.")
    yield

# Initialize FastAPI App
app = FastAPI(
    title="Mutual Fund FAQ API",
    description="Backend API for the RAG-based MF chatbot.",
    version="1.0.0",
    lifespan=lifespan
)

# Phase 5: CORS locked to configured origins (no wildcard by default)
allowed_origins_env = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
)
allowed_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Phase 5: Rate limiting (default 30 req/min per IP)
rate_limit_per_min = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "30"))
app.add_middleware(RateLimitMiddleware, requests_per_minute=rate_limit_per_min)

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Phase 5: Avoid leaking internal stack traces to clients.
    logger.error(f"Unhandled server error: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})

@app.get("/api/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "message": "Mutual Fund FAQ API is running."}

@app.get("/api/examples")
async def get_examples():
    """Returns example questions for the frontend UI chips to test the system."""
    return {
        "examples": [
            "What is the expense ratio of HDFC Mid-Cap Fund?",
            "What is the exit load for HDFC Defence Fund?",
            "Tell me about HDFC Nifty 50 Index Fund.",
            "Compare HDFC Small Cap and Large Cap funds."
        ]
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main Chat API.
    1. Routes the query using Phase 3.
    2. If refused, returns safe template immediately.
    3. If factual, runs Phase 2 RAG and returns the generated answer.
    """
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    logger.info(f"Received query: '{query}'")

    if router is None or retriever is None or generator is None:
        raise HTTPException(status_code=503, detail="Services not initialized")

    # Phase 5: API-layer PII block (defense in depth; also covers account numbers)
    pii = detect_pii(query)
    if pii is not None:
        logger.info(f"PII blocked at API layer. Type: {pii.pii_type}")
        return ChatResponse(
            answer=PII_BLOCK_MESSAGE,
            query_type="PII_DETECTED",
            source_url=None,
            refused=True,
        )

    # Step 1: Routing (Phase 3)
    route_result = router.process_query(query)
    intent = route_result["intent"]
    action = route_result["route_to"]

    # Step 2: Handle Refusals
    if action == "REFUSAL_HANDLER":
        logger.info(f"Query Refused. Intent: {intent}")
        return ChatResponse(
            answer=route_result["response"],
            query_type=intent,
            source_url=None,
            refused=True
        )

    # Step 3: Handle RAG Pipeline (Phase 2)
    logger.info(f"Query Approved. Intent: {intent}. Sending to RAG Pipeline...")
    
    # 3a: Retrieve
    chunks = retriever.retrieve(query)
    
    # 3b: Build Prompts
    context_str = build_context(chunks)
    system_prompt = get_system_prompt()
    user_prompt = build_user_prompt(context_str, query)
    context_metadata = [chunk["metadata"] for chunk in chunks]

    # 3c: Generate
    gen_result = generator.generate(system_prompt, user_prompt, context_metadata)
    
    # Extract source_url if we actually found one
    source_url = None
    if chunks:
        source_url = chunks[0]["metadata"].get("source_url")
    
    # If the generator failed for API reasons
    if gen_result["status"] == "error":
        return ChatResponse(
            answer=gen_result["answer"],
            query_type="ERROR",
            source_url=None,
            refused=True
        )

    # Phase 5: Output safety validation (blocks advice/comparisons/predictions)
    if is_unsafe_output(gen_result["answer"]):
        logger.warning("Unsafe output detected; returning safe fallback.")
        return ChatResponse(
            answer=SAFETY_FALLBACK_MESSAGE,
            query_type="SAFETY_BLOCK",
            source_url=None,
            refused=True,
        )

    return ChatResponse(
        answer=gen_result["answer"],
        query_type=intent,
        source_url=source_url,
        refused=False
    )
