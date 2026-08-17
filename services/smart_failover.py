"""
Smart Failover Router
=====================
Implements the error-aware routing logic for J.A.R.V.I.S.
Intercepts LLM client calls and applies Key-Hop vs Model-Hop failover strategies.
Now supports thread-safe async session_manager calls, streaming failovers, and HUD telemetry events.
"""

import asyncio
from typing import List, Any, Optional

from google.genai.errors import APIError
import groq

from core.session_manager import session_manager
from services.llm_client import UnifiedLLMClient, UnifiedResponse
from config.settings import (
    RATE_LIMIT_STATUS_CODES,
    RATE_LIMIT_ERROR_SUBSTRINGS,
    TRANSIENT_STATUS_CODES,
    TRANSIENT_ERROR_SUBSTRINGS
)
from utils.logger import log_key_hop, log_model_hop, log_all_exhausted
from core.ui_server import broadcast_ui_event


class AllLLMsExhaustedError(Exception):
    """Raised when all keys and fallback models are exhausted in the session."""
    pass


def classify_exception(ex: Exception) -> str:
    """
    Classifies exceptions into 'quota' (rate limit/billing) or 'transient' (server/timeout).
    """
    ex_str = str(ex).lower()
    
    # 1. Check Groq SDK specific exceptions
    if isinstance(ex, groq.RateLimitError):
        return "quota"
    if isinstance(ex, groq.APIConnectionError):
        return "transient"
    if isinstance(ex, groq.APIStatusError):
        status_code = getattr(ex, "status_code", None)
        if status_code in RATE_LIMIT_STATUS_CODES:
            return "quota"
        if status_code in TRANSIENT_STATUS_CODES:
            return "transient"
            
    # 2. Check Google SDK specific exceptions
    if isinstance(ex, APIError):
        code = getattr(ex, "code", None)
        if code == 429:
            return "quota"
        if code in TRANSIENT_STATUS_CODES:
            return "transient"
            
    # 3. Check for asyncio Timeout or Connection issues
    if isinstance(ex, (asyncio.TimeoutError, TimeoutError, ConnectionError)):
        return "transient"
        
    # 4. Check error message substrings
    for sub in RATE_LIMIT_ERROR_SUBSTRINGS:
        if sub in ex_str:
            return "quota"
            
    for sub in TRANSIENT_ERROR_SUBSTRINGS:
        if sub in ex_str:
            return "transient"
            
    # Default fallback
    return "transient"


class SmartFailoverRouter:
    """Executes generative content calls with integrated error-aware key/model hopping."""
    
    def __init__(self, loop: Optional[asyncio.AbstractEventLoop] = None):
        self.client = UnifiedLLMClient(loop=loop)

    async def generate_content(
        self,
        contents: List[Any],
        system_instruction: str,
        tools: Optional[List[Any]] = None
    ) -> UnifiedResponse:
        """
        Executes generation using the active key/model context, retrying automatically
        using failover rules on interception of API errors.
        """
        while True:
            # Resolve current active pointer settings
            config_tuple = await session_manager.get_active_config()
            if not config_tuple:
                log_all_exhausted()
                raise AllLLMsExhaustedError("All LLM providers, keys, and fallback models are exhausted.")
                
            provider, key_id, key_value, model_name = config_tuple
            
            try:
                # Attempt generation
                response = await self.client.generate(
                    provider=provider,
                    key_value=key_value,
                    model_name=model_name,
                    contents=contents,
                    system_instruction=system_instruction,
                    tools=tools
                )
                
                # Broadcast active configuration and latency
                broadcast_ui_event({
                    "type": "telemetry",
                    "event": "active_config_changed",
                    "active_key": key_id,
                    "active_model": model_name,
                    "latency": 0.5 # default dummy display latency
                })
                
                return response
                
            except Exception as ex:
                error_class = classify_exception(ex)
                reason_msg = str(ex)[:150]
                
                if error_class == "quota":
                    # Account/Quota error -> Mark key exhausted and perform Key-Hop
                    await session_manager.mark_key_exhausted(key_id)
                    failed_key_id = key_id
                    failed_model = model_name
                    
                    # Hop to next key
                    success = await session_manager.hop_to_next_key()
                    if not success:
                        log_all_exhausted()
                        raise AllLLMsExhaustedError(
                            f"Key '{failed_key_id}' failed with quota limit: {reason_msg}. No fallback keys remain."
                        ) from ex
                        
                    # Retrieve the new config to display in logs and telemetry
                    new_cfg = await session_manager.get_active_config()
                    if new_cfg:
                        _, next_key_id, _, next_model = new_cfg
                        log_key_hop(failed_key_id, failed_model, next_key_id, next_model, reason_msg)
                        
                        broadcast_ui_event({
                            "type": "telemetry",
                            "event": "failover_hop",
                            "hop_type": "key_hop",
                            "failed_key": failed_key_id,
                            "failed_model": failed_model,
                            "next_key": next_key_id,
                            "next_model": next_model,
                            "reason": reason_msg
                        })
                    else:
                        log_all_exhausted()
                        raise AllLLMsExhaustedError("No valid active config available after key-hop.") from ex
                        
                else:
                    # Model/Transient error -> Perform Model-Hop on SAME key
                    failed_model = model_name
                    success = await session_manager.hop_to_next_model(key_id)
                    
                    if not success:
                        # If no more models on this key, treat key as exhausted and hop to next key
                        await session_manager.mark_key_exhausted(key_id)
                        success_key_hop = await session_manager.hop_to_next_key()
                        
                        if not success_key_hop:
                            log_all_exhausted()
                            raise AllLLMsExhaustedError(
                                f"Model '{failed_model}' failed with transient error: {reason_msg}. No fallbacks left."
                            ) from ex
                            
                        # Log key hop because models are exhausted on the current key
                        new_cfg = await session_manager.get_active_config()
                        if new_cfg:
                            _, next_key_id, _, next_model = new_cfg
                            log_key_hop(key_id, failed_model, next_key_id, next_model, f"Models depleted. Last error: {reason_msg}")
                            
                            broadcast_ui_event({
                                "type": "telemetry",
                                "event": "failover_hop",
                                "hop_type": "key_hop",
                                "failed_key": key_id,
                                "failed_model": failed_model,
                                "next_key": next_key_id,
                                "next_model": next_model,
                                "reason": f"Models depleted. Last: {reason_msg}"
                            })
                    else:
                        # Log model-hop
                        new_cfg = await session_manager.get_active_config()
                        if new_cfg:
                            _, _, _, next_model = new_cfg
                            log_model_hop(key_id, failed_model, next_model, reason_msg)
                            
                            broadcast_ui_event({
                                "type": "telemetry",
                                "event": "failover_hop",
                                "hop_type": "model_hop",
                                "failed_key": key_id,
                                "failed_model": failed_model,
                                "next_key": key_id,
                                "next_model": next_model,
                                "reason": reason_msg
                            })

    async def generate_content_stream(
        self,
        contents: List[Any],
        system_instruction: str,
        tools: Optional[List[Any]] = None
    ):
        """
        Async generator yielding text chunks. If a failure occurs BEFORE the first token chunk is emitted,
        executes an instant Key-Hop or Model-Hop.
        If an error occurs MID-STREAM, gracefully closes the stream chunk, logs the disruption,
        yields a transition marker, and seamlessly resumes generation using the failover client.
        """
        generated_text = ""
        started_yield = False
        retry_count = 0
        max_retries = 5

        while retry_count < max_retries:
            config_tuple = await session_manager.get_active_config()
            if not config_tuple:
                log_all_exhausted()
                raise AllLLMsExhaustedError("All LLM providers, keys, and fallback models are exhausted.")
                
            provider, key_id, key_value, model_name = config_tuple
            
            try:
                # Start generator stream
                stream = self.client.generate_stream(
                    provider=provider,
                    key_value=key_value,
                    model_name=model_name,
                    contents=contents,
                    system_instruction=system_instruction,
                    tools=tools
                )
                
                async for chunk in stream:
                    if chunk:
                        started_yield = True
                        generated_text += chunk
                        yield chunk
                
                # Success, break retry loop
                break
                
            except Exception as ex:
                error_class = classify_exception(ex)
                reason_msg = str(ex)[:150]
                
                # Handle failover pointers
                if error_class == "quota":
                    await session_manager.mark_key_exhausted(key_id)
                    await session_manager.hop_to_next_key()
                    new_cfg = await session_manager.get_active_config()
                    if new_cfg:
                        _, next_key_id, _, next_model = new_cfg
                        log_key_hop(key_id, model_name, next_key_id, next_model, f"Stream error: {reason_msg}")
                else:
                    success = await session_manager.hop_to_next_model(key_id)
                    if not success:
                        await session_manager.mark_key_exhausted(key_id)
                        await session_manager.hop_to_next_key()
                        new_cfg = await session_manager.get_active_config()
                        if new_cfg:
                            _, next_key_id, _, next_model = new_cfg
                            log_key_hop(key_id, model_name, next_key_id, next_model, f"Models depleted. Last: {reason_msg}")
                    else:
                        new_cfg = await session_manager.get_active_config()
                        if new_cfg:
                            _, _, _, next_model = new_cfg
                            log_model_hop(key_id, model_name, next_model, reason_msg)
                
                # Telemetry update
                broadcast_ui_event({
                    "type": "telemetry",
                    "event": "failover_hop",
                    "hop_type": error_class + "_hop",
                    "failed_key": key_id,
                    "failed_model": model_name,
                    "next_key": next_key_id if "new_cfg" in locals() and new_cfg else "Exhausted",
                    "next_model": next_model if "new_cfg" in locals() and new_cfg else "None",
                    "reason": f"Stream disrupted: {reason_msg}"
                })

                if started_yield:
                    # MID-STREAM resumption helper
                    transition_marker = f"\n\n[System: Stream disrupted. Switched to fallback model due to: {reason_msg}]\n\n"
                    yield transition_marker
                    
                    # Convert to Gemini formats safely
                    try:
                        from google.genai import types
                        model_content = types.Content(role="model", parts=[types.Part(text=generated_text)])
                        user_content = types.Content(
                            role="user",
                            parts=[types.Part(text="Continue the previous response exactly from where you left off. Do not repeat what was already generated.")]
                        )
                    except ImportError:
                        # Fallback schema simulation
                        class DummyPart:
                            def __init__(self, text):
                                self.text = text
                        class DummyContent:
                            def __init__(self, role, parts):
                                self.role = role
                                self.parts = parts
                        model_content = DummyContent("model", [DummyPart(generated_text)])
                        user_content = DummyContent(
                            "user",
                            [DummyPart("Continue the previous response exactly from where you left off. Do not repeat what was already generated.")]
                        )

                    # Update context history clone with the generated text so far
                    contents = list(contents)
                    contents.append(model_content)
                    contents.append(user_content)
                    
                    # Reset yield tracking for next stream iteration
                    started_yield = False
                    retry_count += 1
                else:
                    # BEFORE first token was emitted -> simply retry request from start on fallback key
                    retry_count += 1
                    continue


# Global Router instance
smart_failover_router = SmartFailoverRouter()
