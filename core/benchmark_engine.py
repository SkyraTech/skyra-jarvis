"""
Benchmark Engine
================
Runs async parallel pings across all active provider API keys and candidate models.
Keeps only the top 3 working models for each key and updates the registry.
Implements latency_cache.json with a 24-hour TTL.
"""

import asyncio
import json
import time
import os
from pathlib import Path
from typing import List, Tuple, Dict, Any

from google import genai
from google.genai import types
from groq import Groq
from loguru import logger

from config import config
from config.settings import BENCHMARK_TIMEOUT_SECONDS, PING_PROMPT, MAX_MODELS_PER_KEY
from core.key_model_registry import KeyInfo, ModelInfo, update_registry
from core.ui_server import broadcast_ui_event

# Load the models and environment variable mappings
CONFIG_DIR = Path(__file__).parent.parent / "config"
API_KEYS_JSON_PATH = CONFIG_DIR / "api_keys.json"
CACHE_PATH = Path(__file__).parent.parent / "latency_cache.json"


def load_api_keys_config() -> Dict[str, Any]:
    """Load keys and candidate models list from JSON."""
    try:
        with open(API_KEYS_JSON_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load api_keys.json: {e}")
        return {
            "google": {
                "env_keys": ["GEMINI_API_KEY_1", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3"],
                "models": ["gemini-3.5-flash-lite", "gemini-3.7-flash", "gemini-3.5-flash"]
            },
            "groq": {
                "env_keys": [f"GROQ_API_KEY_{i}" for i in range(1, 7)],
                "models": ["groq/compound-mini", "groq/compound", "qwen/qwen3.6-27b"]
            }
        }


def _ping_google(key_value: str, model_name: str) -> None:
    """Synchronous Gemini ping request."""
    client = genai.Client(api_key=key_value)
    client.models.generate_content(
        model=model_name,
        contents=PING_PROMPT,
        config=types.GenerateContentConfig(
            max_output_tokens=1
        )
    )


def _ping_groq(key_value: str, model_name: str) -> None:
    """Synchronous Groq ping request."""
    client = Groq(api_key=key_value)
    client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": PING_PROMPT}],
        max_tokens=1
    )


async def scan_single_model(
    provider: str,
    key_id: str,
    key_value: str,
    model_name: str,
    loop: asyncio.AbstractEventLoop
) -> Tuple[str, str, str, float, bool]:
    """
    Pings a single model for latency.
    Returns:
        Tuple of (provider, key_id, model_name, latency, is_working)
    """
    start_time = time.perf_counter()
    try:
        if provider == "google":
            await asyncio.wait_for(
                loop.run_in_executor(None, _ping_google, key_value, model_name),
                timeout=BENCHMARK_TIMEOUT_SECONDS
            )
        elif provider == "groq":
            await asyncio.wait_for(
                loop.run_in_executor(None, _ping_groq, key_value, model_name),
                timeout=BENCHMARK_TIMEOUT_SECONDS
            )
        else:
            return provider, key_id, model_name, 0.0, False
            
        latency = time.perf_counter() - start_time
        return provider, key_id, model_name, latency, True
        
    except asyncio.TimeoutError:
        logger.debug(f"⏳ Timeout benchmarking {provider} model {model_name} on {key_id}")
        return provider, key_id, model_name, float("inf"), False
    except Exception as e:
        logger.debug(f"❌ Error benchmarking {provider} model {model_name} on {key_id}: {e}")
        return provider, key_id, model_name, float("inf"), False


def load_latency_cache() -> Tuple[List[KeyInfo], List[KeyInfo], bool]:
    """
    Attempts to load cached latency results.
    Validates TTL (24 hours) and matches keys against current environment variable values.
    """
    if not CACHE_PATH.exists():
        return [], [], False
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        timestamp = data.get("timestamp", 0)
        if time.time() - timestamp > 86400:
            logger.info("Latency cache expired (24h TTL). Benchmarking...")
            return [], [], False
            
        google_cached = data.get("google", [])
        groq_cached = data.get("groq", [])
        
        google_keys = []
        groq_keys = []
        
        for item in google_cached:
            env_val = os.getenv(item["key_id"], "").strip()
            if not env_val or "your_" in env_val.lower():
                return [], [], False
            google_keys.append(KeyInfo.from_dict(item, env_val))
            
        for item in groq_cached:
            env_val = os.getenv(item["key_id"], "").strip()
            if not env_val or "your_" in env_val.lower():
                return [], [], False
            groq_keys.append(KeyInfo.from_dict(item, env_val))
            
        logger.info("⚡ Valid latency cache loaded successfully. Booting instantly!")
        return google_keys, groq_keys, True
    except Exception as e:
        logger.warning(f"Failed to read latency cache: {e}")
        return [], [], False


def save_latency_cache(google_keys: List[KeyInfo], groq_keys: List[KeyInfo]) -> None:
    """Save ranked keys and latency details to cache."""
    try:
        data = {
            "timestamp": time.time(),
            "google": [k.to_dict() for k in google_keys],
            "groq": [k.to_dict() for k in groq_keys]
        }
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.debug("Latency cache saved successfully.")
    except Exception as e:
        logger.warning(f"Failed to save latency cache: {e}")


async def run_startup_benchmark() -> None:
    """
    Main entry point for startup benchmarking.
    First checks the latency cache; if missing or expired, pings all models in parallel.
    """
    # 1. Attempt to load cache first
    google_keys, groq_keys, cache_loaded = load_latency_cache()
    if cache_loaded:
        update_registry("google", google_keys)
        update_registry("groq", groq_keys)
        # Broadcast immediately
        await _broadcast_telemetry(google_keys, groq_keys)
        return

    logger.info("⚡ Initiating Pre-Session API Latency Scan across all keys...")
    api_config = load_api_keys_config()
    loop = asyncio.get_running_loop()
    
    tasks = []
    keys_map = {} # Mapping of key_id -> key_value
    
    # Register Google keys
    google_cfg = api_config.get("google", {})
    for env_key in google_cfg.get("env_keys", []):
        val = os.getenv(env_key, "").strip()
        if val and "your_" not in val.lower():
            keys_map[env_key] = val
            for model in google_cfg.get("models", []):
                tasks.append(scan_single_model("google", env_key, val, model, loop))
            
    # Register Groq keys
    groq_cfg = api_config.get("groq", {})
    for env_key in groq_cfg.get("env_keys", []):
        val = os.getenv(env_key, "").strip()
        if val and "your_" not in val.lower():
            keys_map[env_key] = val
            for model in groq_cfg.get("models", []):
                tasks.append(scan_single_model("groq", env_key, val, model, loop))
            
    if not tasks:
        logger.error("🚨 No valid active keys found in env environment to scan!")
        return
        
    logger.info(f"📊 Benchmarking {len(tasks)} model-key combinations concurrently. Please wait...")
    start_time = time.perf_counter()
    
    # Run all model scans concurrently in parallel
    results = await asyncio.gather(*tasks)
    
    # Group results by key
    key_models_map = {}
    for provider, key_id, model_name, latency, is_working in results:
        if not is_working:
            continue
        if key_id not in key_models_map:
            key_models_map[key_id] = []
        key_models_map[key_id].append(ModelInfo(name=model_name, latency=latency))
        
    # Compile KeyInfo lists
    google_keys = []
    groq_keys = []
    
    # Check all active keys
    google_cfg = api_config.get("google", {})
    for env_key in google_cfg.get("env_keys", []):
        if env_key in keys_map:
            key_info = KeyInfo(key_id=env_key, key_value=keys_map[env_key], provider="google")
            models = key_models_map.get(env_key, [])
            if models:
                key_info.models = sorted(models, key=lambda m: m.latency)[:MAX_MODELS_PER_KEY]
                google_keys.append(key_info)
            else:
                logger.warning(f"⚠️ Key {env_key} has NO working models! Check key status or connection.")
                
    groq_cfg = api_config.get("groq", {})
    for env_key in groq_cfg.get("env_keys", []):
        if env_key in keys_map:
            key_info = KeyInfo(key_id=env_key, key_value=keys_map[env_key], provider="groq")
            models = key_models_map.get(env_key, [])
            if models:
                key_info.models = sorted(models, key=lambda m: m.latency)[:MAX_MODELS_PER_KEY]
                groq_keys.append(key_info)
            else:
                logger.warning(f"⚠️ Key {env_key} has NO working models! Check key status or connection.")
                
    # Update registries
    update_registry("google", google_keys)
    update_registry("groq", groq_keys)
    
    # Save successful scan to cache
    save_latency_cache(google_keys, groq_keys)
    
    elapsed = time.perf_counter() - start_time
    logger.info(f"✅ Parallel latency scanning completed in {elapsed:.2f} seconds.")
    
    # Broadcast telemetry
    await _broadcast_telemetry(google_keys, groq_keys)


async def _broadcast_telemetry(google_keys: List[KeyInfo], groq_keys: List[KeyInfo]) -> None:
    """Helper to broadcast telemetry update to the GUI HUD."""
    from core.session_manager import session_manager
    active_cfg = await session_manager.get_active_config()
    active_key = active_cfg[1] if active_cfg else None
    active_model = active_cfg[3] if active_cfg else None
    active_latency = 0.0
    if active_cfg:
        for k in google_keys + groq_keys:
            if k.key_id == active_key:
                active_latency = k.best_latency
                break
                
    google_serial = [{"key_id": k.key_id, "latency": k.best_latency} for k in google_keys]
    groq_serial = [{"key_id": k.key_id, "latency": k.best_latency} for k in groq_keys]
    
    broadcast_ui_event({
        "type": "telemetry",
        "event": "benchmark_completed",
        "google_registry": google_serial,
        "groq_registry": groq_serial,
        "active_key": active_key,
        "active_model": active_model,
        "active_latency": active_latency
    })
