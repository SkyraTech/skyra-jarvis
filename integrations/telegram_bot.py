"""
Jarvis Telegram Bot Integration
================================
Allows you to talk to Jarvis via Telegram from your phone.

Commands:
  /start   — Welcome message
  /help    — List all commands  
  /clear   — Clear conversation memory
  /status  — Show Jarvis stats
  /mute    — Pause voice output
  /unmute  — Resume voice output

Features:
  - Send text messages → Jarvis replies with text
  - Send voice notes → Jarvis transcribes → replies with text + voice
  - Same brain as voice interface (shared conversation history)
  - Only responds to your chat ID (secure — no strangers can use it)
"""

import asyncio
from typing import Optional

from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.request import HTTPXRequest
from telegram.constants import ChatAction
from loguru import logger

from config import config
from core.ui_server import change_ui_state


class TelegramBot:
    """
    Telegram bot interface for Jarvis.
    Shares the same brain as the voice interface.
    """

    def __init__(self, brain, speaker, voice_listener=None):
        """
        Args:
            brain: JarvisBrain instance (shared with voice interface)
            speaker: JarvisSpeaker instance (for voice output)
            voice_listener: VoiceListener for transcribing voice notes (optional)
        """
        self.brain = brain
        self.speaker = speaker
        self.voice_listener = voice_listener
        self.voice_muted = False
        self.is_connected = False
        self.reconnect_task = None

        # Admin chat ID — only this person can use Jarvis
        self.admin_chat_id = int(config.TELEGRAM_ADMIN_CHAT_ID) if config.TELEGRAM_ADMIN_CHAT_ID else None

        # Build the Telegram application with extended timeouts for slow connections
        t_request = HTTPXRequest(connect_timeout=20.0, read_timeout=20.0)
        self.app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).request(t_request).build()
        self._register_handlers()

        logger.info(f"Telegram bot initialized (admin: {self.admin_chat_id})")

    def _register_handlers(self) -> None:
        """Register all message and command handlers."""
        # Commands
        self.app.add_handler(CommandHandler("start",  self._cmd_start))
        self.app.add_handler(CommandHandler("help",   self._cmd_help))
        self.app.add_handler(CommandHandler("clear",  self._cmd_clear))
        self.app.add_handler(CommandHandler("status", self._cmd_status))
        self.app.add_handler(CommandHandler("mute",   self._cmd_mute))
        self.app.add_handler(CommandHandler("unmute", self._cmd_unmute))
        self.app.add_handler(CommandHandler("pause",  self._cmd_pause))
        self.app.add_handler(CommandHandler("resume", self._cmd_resume))

        # Text messages
        self.app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_text)
        )

        # Voice messages
        self.app.add_handler(
            MessageHandler(filters.VOICE, self._handle_voice)
        )

    def _is_authorized(self, update: Update) -> bool:
        """Check if message is from the admin (owner)."""
        if not self.admin_chat_id:
            return True  # If no admin ID set, allow all (not recommended)
        return update.effective_chat.id == self.admin_chat_id

    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        if not self._is_authorized(update):
            await update.message.reply_text("⛔ Unauthorized.")
            return

        await update.message.reply_text(
            f"👋 Hello, {config.JARVIS_OWNER_NAME}!\n\n"
            f"I'm **{config.JARVIS_NAME}**, your personal AI assistant from Skyra-Tech.\n\n"
            f"✨ *What I can do:*\n"
            f"• Answer any question\n"
            f"• Help with tasks, writing, coding\n"
            f"• Send voice messages (I speak back!)\n"
            f"• Remember our conversation context\n\n"
            f"Just type your message or send a voice note!\n"
            f"Use /help to see all commands.",
            parse_mode="Markdown"
        )

    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command."""
        if not self._is_authorized(update): return

        await update.message.reply_text(
            f"🤖 *{config.JARVIS_NAME} Commands*\n\n"
            f"/start  — Welcome message\n"
            f"/help   — Show this help\n"
            f"/clear  — Clear conversation memory\n"
            f"/status — Show system stats\n"
            f"/mute   — Stop voice output on laptop\n"
            f"/unmute — Resume voice output on laptop\n"
            f"/pause  — Pause laptop microphone listening\n"
            f"/resume — Resume laptop microphone listening\n\n"
            f"*How to use:*\n"
            f"• Type any message → I'll reply\n"
            f"• Send a voice note → I'll transcribe + reply",
            parse_mode="Markdown"
        )

    async def _cmd_clear(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Clear conversation history."""
        if not self._is_authorized(update): return

        self.brain.clear_memory()
        await update.message.reply_text(
            "🧹 Memory cleared! Starting fresh.",
        )

    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show current stats."""
        if not self._is_authorized(update): return

        stats = self.brain.get_stats()
        await update.message.reply_text(
            f"📊 *{config.JARVIS_NAME} Status*\n\n"
            f"🧠 Model: `{stats['model']}`\n"
            f"💬 Messages processed: `{stats['messages_processed']}`\n"
            f"🔄 Conversation turns: `{stats['conversation_turns']}`\n"
            f"🔊 Voice: `{'muted' if self.voice_muted else 'active'}`\n"
            f"✅ Status: Online",
            parse_mode="Markdown"
        )

    async def _cmd_mute(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Mute voice output."""
        if not self._is_authorized(update): return
        self.voice_muted = True
        await update.message.reply_text("🔇 Voice output muted on laptop.")

    async def _cmd_unmute(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Unmute voice output."""
        if not self._is_authorized(update): return
        self.voice_muted = False
        await update.message.reply_text("🔊 Voice output active on laptop.")

    async def _cmd_pause(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Pause laptop microphone listening."""
        if not self._is_authorized(update): return
        if self.voice_listener:
            self.voice_listener.is_paused = True
            change_ui_state("offline") # Red color for paused core
            await update.message.reply_text("⏸️ Laptop microphone PAUSED. Jarvis will stop listening.")
        else:
            await update.message.reply_text("⚠️ Microphone is not active on the laptop (running in no-voice mode).")

    async def _cmd_resume(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Resume laptop microphone listening."""
        if not self._is_authorized(update): return
        if self.voice_listener:
            self.voice_listener.is_paused = False
            change_ui_state("idle") # Blue color for active core
            await update.message.reply_text("▶️ Laptop microphone ACTIVE. Jarvis is listening now.")
        else:
            await update.message.reply_text("⚠️ Microphone is not active on the laptop (running in no-voice mode).")

    async def _handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Process incoming text messages."""
        if not self._is_authorized(update): return

        user_message = update.message.text

        # Show typing indicator
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING
        )

        # Get response from brain
        response = await self.brain.think(user_message, source="telegram")

        # Send text reply
        await update.message.reply_text(response)

        # Also speak on laptop (if not muted)
        if not self.voice_muted:
            asyncio.create_task(self.speaker.speak(response))

        logger.info(f"Telegram text: '{user_message[:50]}' -> replied")

    async def _handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Process incoming voice messages."""
        if not self._is_authorized(update): return

        await update.message.reply_text("🎤 Transcribing your voice note...")
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING
        )

        try:
            # Download voice file from Telegram
            voice_file = await update.message.voice.get_file()
            voice_bytes = await voice_file.download_as_bytearray()

            # Save to temp file for Whisper
            import tempfile, os
            with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
                tmp.write(voice_bytes)
                tmp_path = tmp.name

            # Transcribe using Whisper
            loop = asyncio.get_event_loop()
            if self.voice_listener:
                whisper_client = self.voice_listener.whisper
            else:
                # Lazy-load Whisper model if running in --no-voice mode
                if not hasattr(self, '_lazy_whisper'):
                    from faster_whisper import WhisperModel
                    logger.info(f"Loading Whisper model '{config.WHISPER_MODEL}' for Telegram bot...")
                    self._lazy_whisper = await loop.run_in_executor(
                        None,
                        lambda: WhisperModel(config.WHISPER_MODEL, device="cpu", compute_type="int8")
                    )
                whisper_client = self._lazy_whisper

            segments, _ = await loop.run_in_executor(
                None,
                lambda: whisper_client.transcribe(
                    tmp_path, language="en", beam_size=1
                )
            )
            transcribed = " ".join(s.text for s in segments).strip()
            
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

            if not transcribed:
                await update.message.reply_text(
                    "❌ Could not transcribe voice note. Please try again or type your message."
                )
                return

            # Show what was transcribed
            await update.message.reply_text(f"📝 *You said:* _{transcribed}_", parse_mode="Markdown")

            # Process through brain
            response = await self.brain.think(transcribed, source="telegram")

            # Reply
            await update.message.reply_text(response)

            # Speak on laptop
            if not self.voice_muted:
                asyncio.create_task(self.speaker.speak(response))

        except Exception as e:
            logger.error(f"Voice message error: {e}")
            await update.message.reply_text(
                "❌ Error processing voice note. Please try typing your message."
            )

    async def send_message(self, text: str) -> None:
        """Send a proactive message to the admin (called by other parts of Jarvis)."""
        if not self.admin_chat_id:
            return
        try:
            await self.app.bot.send_message(
                chat_id=self.admin_chat_id,
                text=text,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")

    async def run_with_startup(self, startup_msg: str) -> None:
        """Start the Telegram bot and send startup notification after init."""
        await self.run()

    async def run(self) -> None:
        """Start the Telegram bot (runs indefinitely)."""
        logger.info("Starting Telegram bot...")
        try:
            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling(
                allowed_updates=["message"],
                drop_pending_updates=True,
            )
            logger.info("Telegram bot is running!")
            self.is_connected = True

            # Send startup notification NOW (after bot is fully initialized)
            await self.send_message(
                f"*{config.JARVIS_NAME} is online!*\n\n"
                f"Good {'morning' if __import__('datetime').datetime.now().hour < 12 else 'afternoon' if __import__('datetime').datetime.now().hour < 17 else 'evening'}, {config.JARVIS_OWNER_NAME}."
                f" Jarvis is ready.\n\nType /help to see commands."
            )
        except Exception as e:
            logger.error(f"Telegram connection failed (running in offline mode): {e}")
            self.is_connected = False
            # Start background reconnection loop
            self.reconnect_task = asyncio.create_task(self._reconnect_loop())

        # Keep running until stopped
        import asyncio as _asyncio
        while self.app.running:
            await _asyncio.sleep(1)

    async def _reconnect_loop(self) -> None:
        """Background loop to continuously retry connection to Telegram when offline."""
        logger.info("Starting Telegram reconnection loop...")
        while not self.is_connected and self.app.running:
            await asyncio.sleep(15)
            logger.info("Retrying Telegram bot connection...")
            try:
                # Retry start_polling
                await self.app.updater.start_polling(
                    allowed_updates=["message"],
                    drop_pending_updates=True,
                )
                logger.info("Telegram bot successfully reconnected!")
                self.is_connected = True
                
                # Send reconnected notification
                await self.send_message(
                    f"🟢 *{config.JARVIS_NAME} reconnected!*\n\n"
                    f"My connection has been restored, {config.JARVIS_OWNER_NAME}."
                )
            except Exception as e:
                logger.debug(f"Telegram reconnection attempt failed: {e}")

    async def stop(self) -> None:
        """Gracefully stop the Telegram bot."""
        if self.reconnect_task:
            self.reconnect_task.cancel()
        
        try:
            # Check if updater is active before calling stop to prevent crash
            if self.app.updater and self.app.updater.running:
                await self.app.updater.stop()
        except Exception:
            pass

        try:
            if self.app.running:
                await self.app.stop()
                await self.app.shutdown()
        except Exception:
            pass
            
        logger.info("Telegram bot stopped")
