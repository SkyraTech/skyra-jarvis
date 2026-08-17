"""
Jarvis Persistent Memory Manager
================================
Handles reading and writing user facts and settings to memory.json.
Integrates with Qdrant collection vectors with a clean fallback to local JSON storage if Qdrant is unreachable.
Features thread-safe file operations using asyncio locks.
"""

import json
import os
import asyncio
from pathlib import Path
from typing import Optional, List, Any
from loguru import logger

MEMORY_FILE_PATH = Path(__file__).parent.parent / "memory.json"
_lock = asyncio.Lock()
_qdrant_client = None


def get_qdrant_client() -> Optional[Any]:
    """Dynamically get or initialize QdrantClient, returning None if unreachable or unavailable."""
    global _qdrant_client
    if _qdrant_client is not None:
        return _qdrant_client
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(url="http://127.0.0.1:6333", timeout=2.0)
        # Verify connection by checking collections
        client.get_collections()
        _qdrant_client = client
        logger.info("🧠 Qdrant Memory Client connected successfully ✅")
        return _qdrant_client
    except Exception as e:
        logger.debug(f"Qdrant client not available: {e}. Falling back to local JSON memory.")
        return None


async def init_qdrant_collection(client: Any) -> None:
    """Initialize the 'skyra_memory' collection if it doesn't exist."""
    try:
        collections = client.get_collections().collections
        exists = any(c.name == "skyra_memory" for c in collections)
        if not exists:
            from qdrant_client.models import Distance, VectorParams
            client.create_collection(
                collection_name="skyra_memory",
                vectors_config=VectorParams(size=768, distance=Distance.COSINE)
            )
            logger.info("Created Qdrant collection 'skyra_memory'")
    except Exception as e:
        logger.warning(f"Failed to initialize Qdrant collection: {e}")


async def get_embedding_vector(text: str) -> List[float]:
    """Asynchronously get embedding vector from Gemini or fall back to a deterministic dummy vector."""
    try:
        from core.session_manager import session_manager
        cfg = await session_manager.get_active_config()
        if cfg and cfg[0] == "google":
            from google import genai
            client = genai.Client(api_key=cfg[2])
            resp = client.models.embed_content(
                model="text-embedding-004",
                contents=text
            )
            if resp and resp.embeddings:
                return resp.embeddings[0].values
    except Exception as e:
        logger.debug(f"Failed to fetch Gemini embedding: {e}. Using deterministic dummy vector.")
        
    # Fallback: simple deterministic hash-based 768-dim vector
    import hashlib
    vector = []
    seed = hashlib.sha256(text.encode("utf-8")).digest()
    for i in range(768):
        val = hashlib.sha256(seed + bytes([i % 256])).digest()
        vector.append((val[0] / 255.0) * 2.0 - 1.0)
    return vector


def _read_memory_sync() -> dict:
    """Synchronous read helper."""
    if not MEMORY_FILE_PATH.exists():
        return {}
    try:
        with open(MEMORY_FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.warning("memory.json was corrupted. Resetting memory.")
        return {}
    except Exception as e:
        logger.error(f"Failed to read memory file: {e}")
        return {}


def _write_memory_sync(data: dict) -> None:
    """Synchronous write helper."""
    try:
        with open(MEMORY_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to write memory file: {e}")


async def get_all_facts() -> dict:
    """Retrieve all saved facts and configurations."""
    async with _lock:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _read_memory_sync)


async def save_fact(key: str, value: str) -> None:
    """
    Save or update a fact in memory.json and Qdrant (if available).
    """
    clean_key = key.strip().lower().replace(" ", "_")
    
    # 1. Save to local JSON
    async with _lock:
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, _read_memory_sync)
        data[clean_key] = value
        await loop.run_in_executor(None, _write_memory_sync, data)
        logger.info(f"🧠 Memory: Learned fact '{clean_key}' = '{value}'")
        
    # 2. Save to Qdrant if available
    client = get_qdrant_client()
    if client:
        try:
            await init_qdrant_collection(client)
            vector = await get_embedding_vector(f"{clean_key}: {value}")
            from qdrant_client.models import PointStruct
            import uuid
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, clean_key))
            client.upsert(
                collection_name="skyra_memory",
                points=[
                    PointStruct(
                        id=point_id,
                        vector=vector,
                        payload={"key": clean_key, "value": value}
                    )
                ]
            )
            logger.info(f"🧠 Qdrant: Indexed fact '{clean_key}'")
        except Exception as e:
            logger.warning(f"Failed to save fact to Qdrant: {e}")


async def delete_fact(key: str) -> bool:
    """
    Delete a saved fact from memory.json and Qdrant (if available).
    """
    clean_key = key.strip().lower().replace(" ", "_")
    deleted = False
    
    # 1. Delete from local JSON
    async with _lock:
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, _read_memory_sync)
        if clean_key in data:
            del data[clean_key]
            await loop.run_in_executor(None, _write_memory_sync, data)
            logger.info(f"🧠 Memory: Forgot fact '{clean_key}'")
            deleted = True
            
    # 2. Delete from Qdrant if available
    client = get_qdrant_client()
    if client:
        try:
            import uuid
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, clean_key))
            client.delete(
                collection_name="skyra_memory",
                points_selector=[point_id]
            )
            logger.info(f"🧠 Qdrant: Deleted fact '{clean_key}'")
        except Exception as e:
            logger.warning(f"Failed to delete fact from Qdrant: {e}")
            
    return deleted


async def get_fact(key: str) -> Optional[str]:
    """
    Get a single fact value from Qdrant or memory.json.
    """
    clean_key = key.strip().lower().replace(" ", "_")
    
    # Try retrieving from Qdrant first
    client = get_qdrant_client()
    if client:
        try:
            import uuid
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, clean_key))
            points = client.retrieve(
                collection_name="skyra_memory",
                ids=[point_id]
            )
            if points:
                return points[0].payload.get("value")
        except Exception as e:
            logger.warning(f"Failed to retrieve from Qdrant: {e}. Falling back to JSON.")
            
    # Fallback to local JSON
    async with _lock:
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, _read_memory_sync)
        return data.get(clean_key)


async def search_facts_semantic(query: str, limit: int = 5) -> List[dict]:
    """
    Semantic search across saved facts.
    Returns list of matching dicts containing {"key", "value", "score"}.
    """
    client = get_qdrant_client()
    if client:
        try:
            await init_qdrant_collection(client)
            vector = await get_embedding_vector(query)
            results = client.search(
                collection_name="skyra_memory",
                query_vector=vector,
                limit=limit
            )
            matched = []
            for r in results:
                if r.score >= 0.75:
                    matched.append({"key": r.payload.get("key"), "value": r.payload.get("value"), "score": r.score})
            return matched
        except Exception as e:
            logger.warning(f"Failed semantic search: {e}. Falling back to substring match.")
            
    # Substring matching fallback
    async with _lock:
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, _read_memory_sync)
        matched = []
        q_clean = query.strip().lower()
        for k, v in data.items():
            if q_clean in k or q_clean in v.lower():
                matched.append({"key": k, "value": v, "score": 1.0})
        return matched[:limit]
