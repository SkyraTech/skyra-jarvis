"""
Jarvis Tools — Persistent Memory & Dynamic Learning
===================================================
Defines the tool interfaces that allow Gemini to store and delete 
learned facts, preferences, and configurations dynamically.
"""

from core import memory_manager
from loguru import logger


async def remember_user_fact(fact_name: str, fact_details: str) -> str:
    """
    Save or update a fact, preference, setting, or configuration about the user, 
    their business, projects, contacts, or preferences.
    
    Args:
        fact_name: The name or key of the fact (e.g. "partner_name", "workspace_directory").
        fact_details: The details to remember (e.g. "Suresh", "C:/Projects").
    """
    try:
        await memory_manager.save_fact(fact_name, fact_details)
        return f"Successfully saved to memory: '{fact_name}' is now set to '{fact_details}'."
    except Exception as e:
        logger.error(f"Failed to remember fact: {e}")
        return f"Failed to save to memory: {e}"


async def forget_user_fact(fact_name: str) -> str:
    """
    Delete a saved fact, preference, setting, or configuration from your memory.
    
    Args:
        fact_name: The name or key of the fact to forget (e.g. "partner_name").
    """
    try:
        success = await memory_manager.delete_fact(fact_name)
        if success:
            return f"Successfully deleted '{fact_name}' from my memory."
        return f"Could not find any fact named '{fact_name}' in my memory."
    except Exception as e:
        logger.error(f"Failed to forget fact: {e}")
        return f"Failed to delete from memory: {e}"
