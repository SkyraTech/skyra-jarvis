"""
Jarvis Long-Term Memory Store
==============================
Uses Qdrant (local vector database) + sentence-transformers for semantic
memory storage and retrieval.

Stores:
  - Conversation summaries with key decisions and actions
  - Project information and known facts
  - Agent task outputs

Queried:
  - At the start of each think() call to inject relevant past context
  - Before any agent task to recall similar past work
"""

import os
import uuid
from datetime import datetime
from typing import Optional
from pathlib import Path

from loguru import logger
from config import config


# Lazy imports — only loaded when Qdrant is enabled
_qdrant_client = None
_embedding_model = None
_QDRANT_AVAILABLE = False


def _load_qdrant(qdrant_path: str) -> bool:
    """
    Lazy-load Qdrant client.
    Returns True if successfully initialized, False otherwise.
    """
    global _qdrant_client, _QDRANT_AVAILABLE

    if _QDRANT_AVAILABLE:
        return True

    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams, PointStruct
        from google import genai

        Path(qdrant_path).mkdir(parents=True, exist_ok=True)
        _qdrant_client = QdrantClient(path=qdrant_path)

        # Ensure collections exist
        existing = [c.name for c in _qdrant_client.get_collections().collections]

        # Use 3072 dimensions for Google's gemini-embedding-2
        for coll_name in ["jarvis_conversations", "jarvis_projects"]:
            recreate = False
            if coll_name in existing:
                info = _qdrant_client.get_collection(coll_name)
                # Check vector size, handle nesting safely across various qdrant-client versions
                try:
                    current_size = info.config.params.vectors.size
                except Exception:
                    try:
                        current_size = info.config.params.vectors[''].size
                    except Exception:
                        current_size = 3072 # fallback
                
                if current_size != 3072:
                    logger.warning(f"🧠 Memory: Schema mismatch for collection '{coll_name}' ({current_size}d vs 3072d). Recreating...")
                    _qdrant_client.delete_collection(coll_name)
                    recreate = True
            else:
                recreate = True

            if recreate:
                _qdrant_client.create_collection(
                    collection_name=coll_name,
                    vectors_config=VectorParams(size=3072, distance=Distance.COSINE),
                )
                logger.info(f"🧠 Memory: Created '{coll_name}' collection (3072d)")

        _QDRANT_AVAILABLE = True
        return True

    except ImportError:
        logger.warning("⚠️ Qdrant/google-genai not installed. Long-term memory disabled.")
        logger.warning("   Run: pip install qdrant-client google-genai")
        return False
    except Exception as e:
        logger.error(f"❌ Memory store initialization failed: {e}")
        return False


_genai_client = None

def _get_genai_client():
    global _genai_client
    if _genai_client is None:
        from google import genai
        active_key = config.GEMINI_API_KEYS[0] if config.GEMINI_API_KEYS else None
        _genai_client = genai.Client(api_key=active_key)
    return _genai_client


def _embed(text: str) -> list[float]:
    """Convert text to a 3072-dimensional vector using Google's cloud API."""
    try:
        client = _get_genai_client()
        response = client.models.embed_content(
            model="gemini-embedding-2",
            contents=text
        )
        # Handle single vs list return types safely
        embeddings = response.embeddings
        if embeddings and len(embeddings) > 0:
            return embeddings[0].values
        return [0.0] * 3072
    except Exception as e:
        logger.error(f"❌ Memory Store: Embedding generation failed: {e}")
        return [0.0] * 3072




# ── PUBLIC API ────────────────────────────────────────────────────────────────

def initialize(qdrant_path: str) -> bool:
    """Initialize the memory store. Call once at startup."""
    return _load_qdrant(qdrant_path)


def save_conversation(
    user_messages: list[str],
    jarvis_actions: list[str],
    summary: str,
    projects_mentioned: list[str] | None = None,
) -> bool:
    """
    Save a conversation summary to long-term memory.
    Called at the end of each think() cycle.

    Args:
        user_messages: List of user utterances in this conversation turn
        jarvis_actions: List of tools called or responses given
        summary: LLM-generated 1-2 sentence summary of what happened
        projects_mentioned: Any project names mentioned
    """
    if not _QDRANT_AVAILABLE:
        return False

    try:
        from qdrant_client.models import PointStruct

        vector = _embed(summary)
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "date": datetime.now().isoformat(),
                "summary": summary,
                "user_messages": user_messages[:5],   # Keep last 5
                "jarvis_actions": jarvis_actions[:10],
                "projects_mentioned": projects_mentioned or [],
            }
        )
        _qdrant_client.upsert(
            collection_name="jarvis_conversations",
            points=[point]
        )
        logger.debug(f"🧠 Memory saved: {summary[:80]}...")
        return True
    except Exception as e:
        logger.error(f"❌ Memory save failed: {e}")
        return False


def search_memories(query: str, top_k: int = 4) -> str:
    """
    Search long-term memory for context relevant to the query.
    Returns formatted string ready to inject into system prompt.

    Args:
        query: The current user message or topic to search for
        top_k: Number of most relevant memories to return
    """
    if not _QDRANT_AVAILABLE:
        return ""

    try:
        vector = _embed(query)
        results = _qdrant_client.query_points(
            collection_name="jarvis_conversations",
            query=vector,
            limit=top_k,
            score_threshold=0.45,
        ).points


        if not results:
            return ""

        lines = ["📚 Relevant context from your long-term memory:"]
        for hit in results:
            payload = hit.payload
            date = payload.get("date", "")[:10]   # Just the date part
            summary = payload.get("summary", "")
            lines.append(f"  • [{date}] {summary}")

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"❌ Memory search failed: {e}")
        return ""


def save_project(name: str, description: str, github_url: str = "", status: str = "active") -> bool:
    """
    Save or update a project in long-term memory.

    Args:
        name: Project name (e.g. 'skyra-github-service')
        description: Short description of the project
        github_url: GitHub repository URL if available
        status: 'active', 'completed', 'archived'
    """
    if not _QDRANT_AVAILABLE:
        return False

    try:
        from qdrant_client.models import PointStruct

        text = f"{name}: {description}"
        vector = _embed(text)
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "project_name": name,
                "description": description,
                "github_url": github_url,
                "status": status,
                "last_discussed": datetime.now().isoformat(),
            }
        )
        _qdrant_client.upsert(
            collection_name="jarvis_projects",
            points=[point]
        )
        logger.info(f"🧠 Project memory saved: {name}")
        return True
    except Exception as e:
        logger.error(f"❌ Project memory save failed: {e}")
        return False
