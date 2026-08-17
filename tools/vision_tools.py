"""
Jarvis Vision Tools
===================
Exposes screen capture analysis capabilities to Gemini.
Calls the skyra-vision-service (port 8006).

Available tools:
  - analyze_screen_with_vision → Captures the current screen and runs Gemini Vision analysis
"""

from loguru import logger
from utils.network import call_local_api
from config import config

VISION_SERVICE_URL = config.VISION_SERVICE_URL


async def analyze_screen_with_vision(prompt: str = "") -> str:
    """
    Capture the current display screen (primary monitor) and run a multimodal
    AI analysis on it using Gemini 2.5 Flash Vision.

    Use this tool whenever the user asks "what is on my screen", "explain this image/window",
    "solve this question/MCQ on screen", or requests any visual analysis of their current desktop context.

    Args:
        prompt: Optional specific query or instruction to guide the visual analysis (e.g. "solve this question", "what window is open?").
    """
    logger.info("👁️ Tool Call: Triggering screen capture and vision analysis...")
    payload = {"notify_telegram": True}
    if prompt:
        payload["prompt"] = prompt

    success, data, err = await call_local_api("POST", f"{VISION_SERVICE_URL}/vision/analyze", payload)

    if success and data.get("success"):
        analysis = data.get("analysis", "")
        telegram_status = "delivered to Telegram" if data.get("telegram_delivered") else "failed to deliver to Telegram"
        return f"Analysis completed successfully ({telegram_status}):\n\n{analysis}"
    
    return f"Failed to perform vision analysis: {err or data.get('error')}"
