"""
Jarvis Brain — AI Core
======================
Powered by the Pre-Session Latency Scanner & Smart Failover Router.
Maintains conversation history and context across sessions.
Now features context window compaction and an agentic self-healing terminal correction loop.
"""

import json
import asyncio
from datetime import datetime
from typing import Optional

from google.genai import types
from loguru import logger

from config import config
from utils.network import is_online
from tools import ALL_TOOLS, TOOL_MAP
from core import memory_store
from core.session_manager import session_manager
from services.smart_failover import smart_failover_router
from core.ui_server import broadcast_ui_event


class JarvisBrain:
    """
    The central intelligence of Jarvis.
    Delegates all model execution and error-handling to SmartFailoverRouter.
    """

    def __init__(self):
        # Build conversation history (list of Content objects)
        self.history: list[types.Content] = []

        # System prompt with current datetime injected
        self.system_instruction = ""

        # Track usage
        self.message_count = 0

        logger.info(f"Jarvis Brain initialized. Active model: {self.model_name}")

        # Initialize long-term semantic memory (Qdrant)
        if memory_store.initialize(config.QDRANT_PATH):
            logger.info("🧠 Long-term memory (Qdrant) initialized ✅")
        else:
            logger.warning("⚠️ Long-term memory unavailable — running without Qdrant")

    @property
    def model_name(self) -> str:
        """Dynamically retrieve the active model name from session state."""
        return session_manager.get_active_model_name_sync()

    async def _build_system_prompt(self, user_message: str = "") -> str:
        """Build system prompt with current date/time, persistent facts, and relevant memories."""
        now = datetime.now().strftime("%A, %d %B %Y, %I:%M %p")
        base = config.SYSTEM_PROMPT.replace("{current_datetime}", now)

        # Load facts memory (Tier 2)
        try:
            from core import memory_manager
            facts = await memory_manager.get_all_facts()
            if facts:
                facts_str = "\n".join([f"- {k}: {v}" for k, v in facts.items()])
                base += f"\n\nOwner Stated Facts & Preferences:\n{facts_str}"
        except Exception as e:
            logger.error(f"Failed to load memory facts: {e}")

        # Inject long-term semantic memories (Tier 3 — Qdrant)
        if user_message:
            memories = memory_store.search_memories(user_message, top_k=4)
            if memories:
                base += f"\n\n{memories}"

        return base

    def _estimate_history_tokens(self) -> int:
        """Estimate token size of conversation history using a character ratio (1 token ~ 4 chars)."""
        total_chars = 0
        for item in self.history:
            parts = getattr(item, "parts", [])
            for p in parts:
                if hasattr(p, "text") and p.text:
                    total_chars += len(p.text)
                elif hasattr(p, "function_call") and p.function_call:
                    total_chars += len(p.function_call.name) + len(json.dumps(p.function_call.args))
                elif hasattr(p, "function_response") and p.function_response:
                    total_chars += len(p.function_response.name) + len(json.dumps(p.function_response.response))
        return total_chars // 4

    async def _compact_history(self) -> None:
        """Summarize older conversation history turns into a single system memory block when context is full."""
        token_count = self._estimate_history_tokens()
        if token_count <= 8000:
            return
            
        logger.info(f"🧹 History size ({token_count} tokens) exceeds 8000. Compacting older turns...")
        
        # Keep last 8 messages (approx 4 turns) intact to preserve immediate chat context
        keep_last_n = 8
        if len(self.history) <= keep_last_n:
            return
            
        old_turns = self.history[:-keep_last_n]
        recent_turns = self.history[-keep_last_n:]
        
        compaction_prompt = (
            "Summarize the following previous conversation history in detail, preserving all facts stated by the user, "
            "all key actions taken (like tool calls, scripts compiled/run), and active context. Keep the summary dense and informative:\n\n"
        )
        
        old_text = ""
        for item in old_turns:
            role = getattr(item, "role", "user")
            parts = getattr(item, "parts", [])
            for p in parts:
                if hasattr(p, "text") and p.text:
                    old_text += f"{role.upper()}: {p.text}\n"
                elif hasattr(p, "function_call") and p.function_call:
                    old_text += f"SYSTEM: Jarvis called tool '{p.function_call.name}' with args {json.dumps(p.function_call.args)}\n"
                elif hasattr(p, "function_response") and p.function_response:
                    old_text += f"SYSTEM: Tool returned: {json.dumps(p.function_response.response)}\n"
                    
        try:
            summary_content = [
                types.Content(
                    role="user",
                    parts=[types.Part(text=compaction_prompt + old_text)]
                )
            ]
            summary_resp = await smart_failover_router.generate_content(
                contents=summary_content,
                system_instruction="You are a system compactor. Create dense summaries of conversations.",
                tools=None
            )
            summary_text = summary_resp.text.strip() if summary_resp.text else ""
            
            if summary_text:
                logger.info("✅ History compaction successful.")
                system_summary_msg = types.Content(
                    role="user",
                    parts=[types.Part(text=f"[System Memory Block - Summary of previous turns: {summary_text}]")]
                )
                self.history = [system_summary_msg] + recent_turns
            else:
                logger.warning("Compaction returned empty summary. Skipping.")
        except Exception as e:
            logger.error(f"Failed to compact history: {e}")

    async def think(self, user_message: str, source: str = "voice") -> str:
        """
        Process a user message and return Jarvis's response.
        Runs tool executions inside an agentic self-healing correction loop.
        """
        if not user_message.strip():
            return ""

        # Network check
        if not is_online():
            logger.warning("Offline state detected - skipped LLM execution.")
            return f"I am currently offline, {config.JARVIS_OWNER_NAME}. Please restore my internet connection so I can access my brain."

        self.message_count += 1
        logger.info(f"Brain [{source}]: {user_message[:80]}...")

        # Add source hint so Jarvis knows to be brief or detailed
        if source == "telegram":
            prefixed = f"[Via Telegram - detailed response is fine]: {user_message}"
        else:
            prefixed = user_message

        # Append user message to history
        self.history.append(
            types.Content(
                role="user",
                parts=[types.Part(text=prefixed)]
            )
        )

        # Compact history if context threshold exceeded
        await self._compact_history()

        try:
            # Build system prompt with memories relevant to this message
            self.system_instruction = await self._build_system_prompt(user_message)

            # Enforce sliding window — keep only last MAX_HISTORY_TURNS turns
            max_items = config.MAX_HISTORY_TURNS * 2  # *2 because each turn = user + model
            if len(self.history) > max_items:
                self.history = self.history[-max_items:]

            # Agentic Self-Correction Loop pointers
            self_correction_retries = 3
            max_total_turns = 6
            turn = 0
            reply = ""
            
            # Initial call
            response = await smart_failover_router.generate_content(
                contents=self.history,
                system_instruction=self.system_instruction,
                tools=ALL_TOOLS
            )

            # Execution loop
            while turn < max_total_turns:
                if not response.function_calls:
                    # Direct response - verbal conclusion
                    reply = response.text.strip() if response.text else ""
                    break

                # Add model's tool calls to context history
                if hasattr(response, 'raw_response') and hasattr(response.raw_response, 'candidates') and response.raw_response.candidates:
                    self.history.append(response.raw_response.candidates[0].content)
                else:
                    self.history.append(
                        types.Content(
                            role="model",
                            parts=[
                                types.Part(
                                    function_call=types.FunctionCall(
                                        name=call.name,
                                        args=call.args
                                    )
                                ) for call in response.function_calls
                            ]
                        )
                    )

                # Process all function calls requested in this turn
                response_parts = []
                for call in response.function_calls:
                    name = call.name
                    args = call.args
                    logger.info(f"Jarvis Brain: Executing tool '{name}' with arguments: {args}")

                    result_str = ""
                    success = True
                    if name in TOOL_MAP:
                        try:
                            result_str = await TOOL_MAP[name](**args)
                        except Exception as e:
                            logger.error(f"Error executing tool {name}: {e}")
                            result_str = f"Error executing tool: {e}"
                            success = False
                    else:
                        result_str = f"Error: Tool '{name}' is not registered."
                        success = False

                    # Check for non-zero exit codes or standard errors
                    is_terminal_failure = False
                    if name == "run_workspace_command":
                        has_failure_code = "Exit Code: 0" not in result_str
                        has_stderr_errors = "--- Standard Error ---\n[No Errors]" not in result_str and "--- Standard Error ---" in result_str
                        if has_failure_code or has_stderr_errors:
                            is_terminal_failure = True

                    if is_terminal_failure:
                        self_correction_retries -= 1
                        logger.warning(f"⚠️ Terminal command failed. Remaining self-correction retries: {self_correction_retries}")
                        
                        # Telemetry failed execution log
                        broadcast_ui_event({
                            "type": "telemetry",
                            "event": "tool_completed",
                            "tool_name": name,
                            "success": False,
                            "output_summary": f"Failed (Self-healing attempts left: {self_correction_retries})"
                        })
                    else:
                        # Telemetry successful execution log
                        broadcast_ui_event({
                            "type": "telemetry",
                            "event": "tool_completed",
                            "tool_name": name,
                            "success": success,
                            "output_summary": result_str[:80] + "..." if len(result_str) > 80 else result_str
                        })

                    # Add response part
                    response_parts.append(
                        types.Part.from_function_response(
                            name=name,
                            response={"result": result_str}
                        )
                    )

                # Append unified tool response turn
                self.history.append(
                    types.Content(
                        role="user",
                        parts=response_parts
                    )
                )

                # If compile errors exhausted our healing retries, stop and show output to the owner
                if self_correction_retries < 0:
                    logger.error("❌ Agentic Self-Correction turns depleted (3 retries). Exiting tool loop.")
                    reply = "I attempted to compile/execute the code but encountered errors. Here is the last execution log:\n" + result_str
                    break

                # Query LLM again for the next turn
                turn += 1
                response = await smart_failover_router.generate_content(
                    contents=self.history,
                    system_instruction=self.system_instruction,
                    tools=ALL_TOOLS
                )

            # Append final model response to history
            if reply:
                self.history.append(
                    types.Content(
                        role="model",
                        parts=[types.Part(text=reply)]
                    )
                )

            logger.info(f"Jarvis (using {self.model_name}): {reply[:100]}...")

            # Save exchange to long-term memory (async)
            if reply:
                _user_msgs = [user_message]
                _actions = []
                for h in self.history[-6:]:
                    if hasattr(h, 'parts'):
                        for p in h.parts:
                            if hasattr(p, 'function_call') and p.function_call:
                                _actions.append(p.function_call.name)
                _summary = f"{config.JARVIS_OWNER_NAME} said: '{user_message[:80]}'. Jarvis replied: '{reply[:80]}'"
                if _actions:
                    _summary += f" Actions taken: {', '.join(_actions)}"
                memory_store.save_conversation(
                    user_messages=_user_msgs,
                    jarvis_actions=_actions,
                    summary=_summary,
                )

            return reply

        except Exception as e:
            logger.error(f"Execution error: {e}")
            if self.history:
                self.history.pop()
            return (
                f"I apologize, {config.JARVIS_OWNER_NAME}. "
                f"I encountered a failure across all configured models and failover backends. "
                f"Please verify my API keys and connection status."
            )

    def clear_memory(self) -> None:
        """Reset conversation history."""
        self.history = []
        self.message_count = 0
        logger.info("Conversation memory cleared")

    def get_stats(self) -> dict:
        """Return current stats."""
        return {
            "messages_processed": self.message_count,
            "conversation_turns": len(self.history),
            "model": self.model_name,
        }
