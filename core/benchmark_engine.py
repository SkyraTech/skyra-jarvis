"""
Benchmark Engine
================
Runs async parallel pings across all active provider API keys and candidate models.
Keeps only the top 3 working models for each key and updates the registry.
Now broadcasts telemetry results directly to the 3D HUD dashboard on completion.
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


def load_api_keys_config() -> Dict[str, Any]:
    """Load keys and candidate models list from JSON."""
    try:
        with open(API_KEYS_JSON_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load api_keys.json: {e}")
        # Return fallback configuration
        return {
            "google": {
                "env_keys": ["GEMINI_API_KEY_1", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3"],
                "models": ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-3.5-flash-lite"]
            },
            "groq": {
                "env_keys": [f"GROQ_API_KEY_{i}" for i in range(1, 7)],
                "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
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
) -> Tuple[str, float, bool]:
    """
    Pings a single model for latency.
    Returns:
        Tuple of (model_name, latency, is_working)
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
            return model_name, 0.0, False
            
        latency = time.perf_counter() - start_time
        return model_name, latency, True
        
    except asyncio.TimeoutError:
        logger.debug(f"⏳ Timeout benchmarking {provider} model {model_name} on {key_id}")
        return model_name, float("inf"), False
    except Exception as e:
        logger.debug(f"❌ Error benchmarking {provider} model {model_name} on {key_id}: {e}")
        return model_name, float("inf"), False


async def scan_single_key(
    provider: str,
    key_id: str,
    key_value: str,
    candidate_models: List[str],
    loop: asyncio.AbstractEventLoop
) -> KeyInfo:
    """
    Scans candidate models sequentially until one succeeds.
    Populates all candidate models with the successful baseline latency.
    """
    key_info = KeyInfo(key_id=key_id, key_value=key_value, provider=provider)
    
    for model in candidate_models:
        model_name, latency, is_working = await scan_single_model(
            provider, key_id, key_value, model, loop
        )
        if is_working:
            # We found a working model! Populate all candidate models with this latency
            working_models = []
            for m in candidate_models:
                working_models.append(ModelInfo(name=m, latency=latency))
            key_info.models = working_models[:MAX_MODELS_PER_KEY]
            return key_info
            
    return key_info


async def run_startup_benchmark() -> None:
    """
    Main entry point for startup benchmarking.
    Scans all keys and models in parallel and prioritizes the pools.
    """
    logger.info("⚡ Initiating Pre-Session API Latency Scan across all keys...")
    api_config = load_api_keys_config()
    loop = asyncio.get_running_loop()
    
    tasks = []
    
    # Process Google keys
    google_cfg = api_config.get("google", {})
    for env_key in google_cfg.get("env_keys", []):
        val = os.getenv(env_key, "").strip()
        if val and "your_" not in val.lower():
            tasks.append(scan_single_key("google", env_key, val, google_cfg.get("models", []), loop))
            
    # Process Groq keys
    groq_cfg = api_config.get("groq", {})
    for env_key in groq_cfg.get("env_keys", []):
        val = os.getenv(env_key, "").strip()
        if val and "your_" not in val.lower():
            tasks.append(scan_single_key("groq", env_key, val, groq_cfg.get("models", []), loop))
            
    if not tasks:
        logger.error("🚨 No valid active keys found in env environment to scan!")
        return
        
    logger.info(f"📊 Benchmarking {len(tasks)} active keys concurrently. Please wait...")
    start_time = time.perf_counter()
    
    # Execute everything in parallel
    completed_keys = await asyncio.gather(*tasks)
    
    # Split into providers and update registry
    google_keys = []
    groq_keys = []
    
    for key_info in completed_keys:
        if not key_info.models:
            logger.warning(f"⚠️ Key {key_info.key_id} has NO working models! Check key status or connection.")
            continue
            
        if key_info.provider == "google":
            google_keys.append(key_info)
        elif key_info.provider == "groq":
            groq_keys.append(key_info)
            
    # Update pools
    update_registry("google", google_keys)
    update_registry("groq", groq_keys)
    
    elapsed = time.perf_counter() - start_time
    logger.info(f"✅ Latency scanning completed in {elapsed:.2f} seconds.")

    # Fetch active configuration to broadcast telemetry details
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
