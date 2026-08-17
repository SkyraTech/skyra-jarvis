"""
Jarvis Persistent Memory Manager
================================
Handles reading and writing user facts and settings to `memory.json`.
Features thread-safe file operations using asyncio locks.
"""

import json
import os
import asyncio
from pathlib import Path
from typing import Optional
from loguru import logger

MEMORY_FILE_PATH = Path(__file__).parent.parent / "memory.json"
_lock = asyncio.Lock()


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
    Save or update a fact in the persistent memory.
    
    Args:
        key: The configuration identifier or fact name (e.g. "partner_name")
        value: The value details to store (e.g. "Suresh")
    """
    async with _lock:
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, _read_memory_sync)
        
        # Normalize key formatting
        clean_key = key.strip().lower().replace(" ", "_")
        data[clean_key] = value
        
        await loop.run_in_executor(None, _write_memory_sync, data)
        logger.info(f"🧠 Memory: Learned fact '{clean_key}' = '{value}'")


async def delete_fact(key: str) -> bool:
    """
    Delete a saved fact from memory.
    
    Args:
        key: The fact key to delete
        
    Returns:
        True if deleted, False if key was not found
    """
    async with _lock:
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, _read_memory_sync)
        
        clean_key = key.strip().lower().replace(" ", "_")
        if clean_key in data:
            del data[clean_key]
            await loop.run_in_executor(None, _write_memory_sync, data)
            logger.info(f"🧠 Memory: Forgot fact '{clean_key}'")
            return True
            
        return False


async def get_fact(key: str) -> Optional[str]:
    """
    Get a single fact value from memory.
    """
    async with _lock:
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, _read_memory_sync)
        clean_key = key.strip().lower().replace(" ", "_")
        return data.get(clean_key)
