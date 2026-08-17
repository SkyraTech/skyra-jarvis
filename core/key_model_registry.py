"""
Key Model Registry
==================
In-memory store of scanned API keys, their top 3 lowest-latency models, and prioritized pools.
"""

from typing import Dict, List, Any
from loguru import logger


class ModelInfo:
    """Represents benchmarked information for a specific model under a key."""
    def __init__(self, name: str, latency: float):
        self.name = name
        self.latency = latency

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "latency": self.latency}


class KeyInfo:
    """Represents a benchmarked API Key containing its top working models."""
    def __init__(self, key_id: str, key_value: str, provider: str):
        self.key_id = key_id          # e.g. "GEMINI_API_KEY_1" or "GROQ_API_KEY_3"
        self.key_value = key_value    # The actual API key credential string
        self.provider = provider      # "google" or "groq"
        self.models: List[ModelInfo] = []  # Top 3 working models, sorted by latency (fastest first)

    @property
    def best_latency(self) -> float:
        """Get latency of the fastest model, used for key ranking."""
        return self.models[0].latency if self.models else float("inf")

    @classmethod
    def from_dict(cls, data: Dict[str, Any], key_value: str) -> "KeyInfo":
        k = cls(key_id=data["key_id"], key_value=key_value, provider=data["provider"])
        k.models = [ModelInfo(name=m["name"], latency=m["latency"]) for m in data.get("models", [])]
        return k

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key_id": self.key_id,
            "provider": self.provider,
            "best_latency": self.best_latency,
            "models": [m.to_dict() for m in self.models]
        }


# Global Registry Map
# Format: { "google": [KeyInfo, ...], "groq": [KeyInfo, ...] }
# Lists are sorted by KeyInfo.best_latency ascending (fastest key first)
_registry: Dict[str, List[KeyInfo]] = {
    "google": [],
    "groq": []
}


def update_registry(provider: str, key_info_list: List[KeyInfo]) -> None:
    """
    Update the global key model registry for a provider.
    Sorts the keys by their best performing model latency.
    """
    # Sort the key registry by best latency
    sorted_keys = sorted(key_info_list, key=lambda k: k.best_latency)
    _registry[provider] = sorted_keys
    
    logger.info(f"Registry updated for {provider}. Ranked keys:")
    for idx, key_info in enumerate(sorted_keys):
        best_model = key_info.models[0].name if key_info.models else "None"
        logger.info(
            f"  [{idx + 1}] {key_info.key_id} | Best Model: {best_model} | Latency: {key_info.best_latency:.3f}s"
        )


def get_prioritized_keys(provider: str) -> List[KeyInfo]:
    """Retrieve prioritized (sorted by latency) list of active KeyInfo objects for a provider."""
    return _registry.get(provider, [])


def get_all_keys() -> Dict[str, List[KeyInfo]]:
    """Get the full in-memory registry map."""
    return _registry
