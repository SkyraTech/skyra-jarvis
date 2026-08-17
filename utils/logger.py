"""
Failover Logger Utility
=======================
Custom logger helper functions for structured logging of failover, key-hops, model-hops and benchmarks.
"""

from loguru import logger


def log_benchmark_result(provider: str, key_id: str, model_name: str, latency: float, success: bool) -> None:
    """Log the latency benchmark result for a key's model."""
    if success:
        logger.info(
            f"⚡ [Scan] {provider.upper()} | Key: {key_id} | Model: {model_name} | Latency: {latency:.3f}s"
        )
    else:
        logger.warning(
            f"❌ [Scan] {provider.upper()} | Key: {key_id} | Model: {model_name} | FAILED or TIMEOUT"
        )


def log_key_hop(failed_key_id: str, failed_model: str, next_key_id: str, next_model: str, reason: str) -> None:
    """Log key transition due to account limit / exhaustion errors."""
    logger.critical(
        f"🔄 [FAILOVER HOPS] Account Exceeded/Rate-Limited on key '{failed_key_id}' running '{failed_model}'. "
        f"Reason: {reason}. HOPPING KEY: -> Switch to key '{next_key_id}' starting at model '{next_model}'."
    )


def log_model_hop(key_id: str, failed_model: str, next_model: str, reason: str) -> None:
    """Log model fallback transition within the same key due to engine / transient errors."""
    logger.warning(
        f"🔄 [FAILOVER HOPS] Transient/Server Error on model '{failed_model}' using key '{key_id}'. "
        f"Reason: {reason}. HOPPING MODEL: -> Fall back to model '{next_model}' on the SAME API key."
    )


def log_all_exhausted() -> None:
    """Log total failure indicating no operational API keys remain."""
    logger.critical(
        "🚨 [FAILOVER PANIC] All configured API keys and fallback models for both Google and Groq are completely exhausted!"
    )
