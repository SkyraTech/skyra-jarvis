"""
Session Manager
               
Manages in-memory active pointers (active provider, key, model index) and tracking of exhausted keys.
Provides error-free transitions across keys and models based on routing rules.
Now includes thread-safety locks and dynamic cooldown quarantine pools.
"""

import time
import asyncio
from typing import Optional, Tuple, Dict
from loguru import logger
from core.key_model_registry import get_prioritized_keys, KeyInfo, ModelInfo
from core.ui_server import broadcast_ui_event


class SessionManager:
    """Manages active pointers and fallback search space across provider key pools with thread-safety."""
    
    def __init__(self):
        # We start with "google" as preferred provider, and fallback to "groq"
        self.active_provider = "google"
        
        # Pointers for key indices per provider
        self.key_pointers = {
            "google": 0,
            "groq": 0
        }
        
        # Pointers for model indices per key_id
        # Format: { key_id: model_index }
        self.model_pointers = {}
        
        # Cooldown quarantine dictionary: { key_id: timestamp_expiry }
        self.quarantine: Dict[str, float] = {}
        
        # Probation pool for keys whose cooldown has expired
        self.probation_pool = set()
        
        # Thread safety lock (lazily initialized)
        self._lock: Optional[asyncio.Lock] = None

    def _get_lock(self) -> asyncio.Lock:
        """Lazily initialize and return the asyncio Lock."""
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def reset(self) -> None:
        """Reset all session pointers, exhausted states, and quarantine pools."""
        async with self._get_lock():
            self.active_provider = "google"
            self.key_pointers = {"google": 0, "groq": 0}
            self.model_pointers = {}
            self.quarantine.clear()
            self.probation_pool.clear()
            logger.info("Session manager state reset.")

    async def get_active_config(self) -> Optional[Tuple[str, str, str, str]]:
        """
        Get the currently active execution configuration.
        Returns:
            Tuple of (provider, key_id, key_value, model_name) or None if all are exhausted.
        """
        async with self._get_lock():
            return await self._resolve_active_config()

    async def mark_key_exhausted(self, key_id: str) -> None:
        """Mark an API key as temporarily quarantined (cooldown for 60 seconds)."""
        async with self._get_lock():
            now = time.time()
            cooldown_duration = 60.0
            expiry = now + cooldown_duration
            self.quarantine[key_id] = expiry
            if key_id in self.probation_pool:
                self.probation_pool.remove(key_id)
            logger.warning(f"🚨 API Key {key_id} quarantined (429/Exhausted) for {cooldown_duration} seconds.")
            
            # Broadcast event to Webview HUD
            broadcast_ui_event({
                "type": "telemetry",
                "event": "failover_hop",
                "hop_type": "key_hop",
                "failed_key": key_id,
                "failed_model": "llama-3.1-8b-instant" if "groq" in key_id.lower() else "gemini-2.5-flash",
                "next_key": "Exhausted/Quarantined",
                "next_model": "None",
                "reason": "Quota limits / HTTP 429 Exceeded"
            })

    async def hop_to_next_key(self) -> bool:
        """
        Perform a Key-hop transition (on rate-limit/quota error).
        Switches immediately to the next best key (starting at Model 1).
        Returns True if successful, False if all keys/providers are exhausted.
        """
        async with self._get_lock():
            provider = self.active_provider
            keys = get_prioritized_keys(provider)
            current_idx = self.key_pointers[provider]
            
            # Move key pointer forward
            self.key_pointers[provider] = current_idx + 1
            
            # If we exhausted all keys for this provider, try falling back to the next provider
            if self.key_pointers[provider] >= len(keys):
                if provider == "google":
                    logger.warning("⚠️ All Google keys exhausted/quarantined. Transitioning to Groq key pool.")
                    self.active_provider = "groq"
                    self.key_pointers["groq"] = 0
                else:
                    logger.error("❌ All Google and Groq key pools are completely exhausted/quarantined!")
                    return False
                    
            return True

    async def hop_to_next_model(self, key_id: str) -> bool:
        """
        Perform a Model-hop transition (on transient engine/5xx/timeout errors).
        Falls back to Model 2 or Model 3 of the same key.
        Returns True if a fallback model exists on this key, False otherwise.
        """
        async with self._get_lock():
            current_model_idx = self.model_pointers.get(key_id, 0)
            
            # Resolve the key to see how many models it has
            key_info = self._find_key_by_id(key_id)
            if not key_info:
                return False
                
            next_model_idx = current_model_idx + 1
            if next_model_idx < len(key_info.models):
                self.model_pointers[key_id] = next_model_idx
                new_model = key_info.models[next_model_idx].name
                logger.info(f"🔄 Transient error fallback: Hopping to Model {next_model_idx + 1} ({new_model}) on same key {key_id}.")
                return True
                
            logger.warning(f"⚠️ Key {key_id} has no more models left to attempt.")
            return False

    def _find_key_by_id(self, key_id: str) -> Optional[KeyInfo]:
        """Find KeyInfo object by its key ID across all provider pools."""
        for provider in ["google", "groq"]:
            for k in get_prioritized_keys(provider):
                if k.key_id == key_id:
                    return k
        return None

    async def _resolve_active_config(self) -> Optional[Tuple[str, str, str, str]]:
        """Find the first valid configuration that is not quarantined. Expired quarantines are restored."""
        now = time.time()
        # Clean up quarantine expired keys
        expired_keys = [k for k, expiry in self.quarantine.items() if now >= expiry]
        for k in expired_keys:
            del self.quarantine[k]
            self.probation_pool.add(k)
            logger.info(f"♻️ API Key {k} cooldown quarantine has expired. Moved to PROBATION pool for retry.")
            
        providers_to_try = [self.active_provider]
        if self.active_provider == "google":
            providers_to_try.append("groq")
            
        for provider in providers_to_try:
            keys = get_prioritized_keys(provider)
            start_idx = self.key_pointers[provider]
            
            for idx in range(start_idx, len(keys)):
                key_info = keys[idx]
                
                # Check if this key is currently quarantined
                if key_info.key_id in self.quarantine:
                    continue
                    
                # We found a valid non-quarantined key, update our pointer
                self.active_provider = provider
                self.key_pointers[provider] = idx
                
                # Get the model pointer for this key
                model_idx = self.model_pointers.setdefault(key_info.key_id, 0)
                if model_idx < len(key_info.models):
                    model_info = key_info.models[model_idx]
                    return (provider, key_info.key_id, key_info.key_value, model_info.name)
                else:
                    # Models exhausted for this key, quarantine it and continue
                    # inline marking exhausted to avoid re-entering lock
                    expiry = now + 60.0
                    self.quarantine[key_info.key_id] = expiry
                    if key_info.key_id in self.probation_pool:
                        self.probation_pool.remove(key_info.key_id)
                    logger.warning(f"🚨 API Key {key_info.key_id} models exhausted. Quarantining key.")
                    
        return None


    def get_active_model_name_sync(self) -> str:
        """Get the active model name synchronously without acquiring locks, for read-only metadata."""
        try:
            provider = self.active_provider
            keys = get_prioritized_keys(provider)
            idx = self.key_pointers[provider]
            if idx < len(keys):
                key_info = keys[idx]
                model_idx = self.model_pointers.get(key_info.key_id, 0)
                if model_idx < len(key_info.models):
                    return key_info.models[model_idx].name
        except Exception:
            pass
        return "None"


# Global Session Manager Singleton
session_manager = SessionManager()
