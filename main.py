"""
Jarvis — Main Entry Point
==========================
Starts everything together:
  1. Voice listener (microphone -> Whisper -> Gemini -> speaker)
  2. Telegram bot (runs in parallel)

Usage:
  python main.py              -> Full mode (voice + Telegram)
  python main.py --no-voice   -> Telegram only (no microphone)
  python main.py --no-telegram → Voice only (no Telegram)
  python main.py --list-mics  → Show available microphones
"""

import asyncio
import sys
import io
import os
import warnings
import signal
from datetime import datetime

# Silence Pygame startup support message
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

# Suppress HuggingFace cache and other library runtime warnings
warnings.filterwarnings("ignore")

# Force UTF-8 output on Windows — prevents emoji encoding crashes
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# ── Local modules ─────────────────────────────────────────────────────────
from config import config
from core.brain import JarvisBrain
from core.speaker import JarvisSpeaker
from core.voice_listener import VoiceListener
from integrations.telegram_bot import TelegramBot
from utils.network import is_online
from core.ui_server import change_ui_state
from core.benchmark_engine import run_startup_benchmark


# ── Setup logging ─────────────────────────────────────────────────────────
logger.remove()  # Remove default handler
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    level=config.LOG_LEVEL,
    colorize=True
)
logger.add(
    "jarvis.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="DEBUG",
    rotation="10 MB",
    retention="7 days"
)

console = Console()


def print_banner() -> None:
    """Print the Jarvis startup banner."""
    print()
    print("  =========================================")
    print("   J.A.R.V.I.S  --  Skyra-Tech")
    print("  =========================================")
    print(f"   Ready to serve, {config.JARVIS_OWNER_NAME}.")
    print(f"   Voice : {config.VOICE_NAME}")
    print(f"   Model : gemini-2.0-flash")
    print(f"   Whisper: {config.WHISPER_MODEL}")
    print("  =========================================")
    print()


async def voice_loop(
    listener: VoiceListener,
    brain: JarvisBrain,
    speaker: JarvisSpeaker,
    telegram: TelegramBot | None
) -> None:
    """
    Main voice interaction loop.
    Continuously listens → transcribes → thinks → speaks.
    """
    listener.start()
    logger.info("🎤 Voice loop started. Speak to Jarvis!")

    while listener.is_listening:
        try:
            # Set UI to listening state
            change_ui_state("listening")

            # Listen for speech
            transcribed = await listener.listen_and_transcribe()

            # Set UI back to idle state
            change_ui_state("idle")

            if not transcribed:
                # No speech detected — keep listening
                continue

            # Skip empty or single-character noise transcriptions
            if not transcribed.strip() or len(transcribed.strip()) <= 1:
                logger.debug(f"Ignored single-character noise: '{transcribed}'")
                continue

            console.print(f"\n  [bold cyan]You:[/bold cyan] {transcribed}")

            # Check for voice pause commands
            text_lower = transcribed.lower().strip()
            if any(cmd in text_lower for cmd in ["pause listening", "stop listening", "go to sleep", "mute microphone", "pause microphone"]):
                reply = "Understood. I will pause my microphone. You can resume me anytime via Telegram."
                console.print(f"  [bold yellow]{config.JARVIS_NAME}:[/bold yellow] {reply}\n")
                change_ui_state("offline")
                await speaker.speak(reply)
                listener.is_paused = True
                continue

            # Don't process if Jarvis is currently speaking
            if speaker.is_speaking:
                speaker.stop()

            # Set UI to thinking state during AI processing
            change_ui_state("thinking")

            # Get AI response
            response = await brain.think(transcribed, source="voice")
            
            # Reset if no response generated (otherwise, the speaker will transition speaking -> idle)
            if not response:
                change_ui_state("idle")

            if response:
                console.print(f"  [bold yellow]{config.JARVIS_NAME}:[/bold yellow] {response}\n")

                # Speak the response
                await speaker.speak(response)

                # Also notify via Telegram (optional — uncomment if wanted)
                # if telegram:
                #     await telegram.send_message(
                #         f"🎤 *Voice*\n\n*You:* {transcribed}\n\n*{config.JARVIS_NAME}:* {response}"
                #     )

        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"❌ Voice loop error: {e}")
            await asyncio.sleep(1)  # Brief pause before retrying


async def main(use_voice: bool = True, use_telegram: bool = True) -> None:
    """Main orchestrator — starts all components."""

    print_banner()

    # ── Validate config ───────────────────────────────────────────────────
    try:
        config.validate()
    except ValueError as e:
        console.print(f"\n[bold red]{e}[/bold red]\n")
        sys.exit(1)

    # ── Pre-Session Latency Scanner ───────────────────────────────────────
    if is_online():
        await run_startup_benchmark()
    else:
        logger.warning("System offline — skipping pre-session API latency benchmarks.")

    # ── Initialize components ─────────────────────────────────────────────
    logger.info("🚀 Starting Jarvis...")

    # Brain (shared between voice and Telegram)
    brain = JarvisBrain()

    # Speaker
    speaker = JarvisSpeaker()

    # Voice listener
    listener = None
    if use_voice:
        listener = VoiceListener()

    # Telegram bot
    telegram = None
    if use_telegram:
        telegram = TelegramBot(
            brain=brain,
            speaker=speaker,
            voice_listener=listener
        )

    # ── Startup message ───────────────────────────────────────────────────
    online = is_online()
    if online:
        startup_msg = (
            f"Good {'morning' if datetime.now().hour < 12 else 'afternoon' if datetime.now().hour < 17 else 'evening'}, "
            f"{config.JARVIS_OWNER_NAME}. "
            f"Jarvis is online and ready."
        )
    else:
        startup_msg = (
            f"Good {'morning' if datetime.now().hour < 12 else 'afternoon' if datetime.now().hour < 17 else 'evening'}, "
            f"{config.JARVIS_OWNER_NAME}. "
            f"I am running, but currently offline."
        )
        logger.warning("System offline - running in offline fallback mode.")

    logger.info(f"Jarvis ready: {startup_msg}")

    # Register current event loop and text input callback for the UI Chatbox
    from core import ui_server
    ui_server.backend_loop = asyncio.get_running_loop()

    async def process_ui_text(text: str):
        if not text.strip():
            return

        # Stop speaking if active
        if speaker.is_speaking:
            speaker.stop()

        console.print(f"\n  [bold cyan]You (UI):[/bold cyan] {text}")
        
        # Log to the dashboard terminal feed too so the user sees their message
        ui_server.broadcast_ui_event({
            "type": "agent_message",
            "sender": "You",
            "message": text
        })
        
        change_ui_state("thinking")

        # Get AI response
        response = await brain.think(text, source="ui")
        change_ui_state("idle")

        if response:
            console.print(f"  [bold yellow]{config.JARVIS_NAME}:[/bold yellow] {response}\n")
            # Log the response to the dashboard terminal feed
            ui_server.broadcast_ui_event({
                "type": "agent_message",
                "sender": config.JARVIS_NAME,
                "message": response
            })
            # Speak the response so the user gets audio feedback
            await speaker.speak(response)

    ui_server.text_input_callback = process_ui_text

    # Speak startup message (voice only, before blocking tasks start)
    if use_voice:
        await speaker.speak(startup_msg)


    # ── Run everything concurrently ───────────────────────────────────────
    tasks = []

    if use_telegram:
        # run() initializes the bot first, then sends the startup message
        tasks.append(asyncio.create_task(
            telegram.run_with_startup(startup_msg)
        ))

    if use_voice and listener:
        tasks.append(asyncio.create_task(
            voice_loop(listener, brain, speaker, telegram)
        ))

    if not tasks:
        logger.error("No interfaces enabled! Use --voice or --telegram flags.")
        return

    print()
    print("  Jarvis is running!")
    print("  - Speak into your microphone (voice is always listening)" if use_voice else "  - Voice: disabled")
    print("  - Message your Telegram bot from anywhere" if use_telegram else "  - Telegram: disabled")
    print("  - Press Ctrl+C to stop")
    print()

    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        pass
    finally:
        # Graceful shutdown
        logger.info("Shutting down Jarvis...")

        if listener:
            listener.stop()

        if telegram:
            try:
                await telegram.send_message(
                    f"*{config.JARVIS_NAME} is going offline.*\nSee you soon, {config.JARVIS_OWNER_NAME}!"
                )
            except Exception:
                pass
            await telegram.stop()

        logger.info("Jarvis offline. Goodbye!")


if __name__ == "__main__":
    # ── Parse arguments ───────────────────────────────────────────────────
    use_voice    = "--no-voice"    not in sys.argv
    use_telegram = "--no-telegram" not in sys.argv
    no_gui       = "--no-gui"      in sys.argv

    # Show available microphones
    if "--list-mics" in sys.argv:
        VoiceListener.list_microphones()
        sys.exit(0)

    # ── Start UI Server ───────────────────────────────────────────────────
    from core.ui_server import start_ui_server
    start_ui_server()

    # ── Run Async Backend in Background Thread ─────────────────────────────
    import threading
    from concurrent.futures import ThreadPoolExecutor
    
    def run_backend():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        # Allocate 64 workers to run all 9 keys & models parallel scans without thread queueing
        executor = ThreadPoolExecutor(max_workers=64)
        loop.set_default_executor(executor)
        try:
            loop.run_until_complete(main(use_voice=use_voice, use_telegram=use_telegram))
        except Exception as e:
            logger.error(f"Backend loop error: {e}")
            
    backend_thread = threading.Thread(target=run_backend, daemon=True)
    backend_thread.start()

    # ── Run UI Desktop Window on Main Thread ────────────────────────────────
    if not no_gui:
        try:
            import webview
            logger.info("Opening Jarvis 3D Hologram Core window...")
            webview.create_window(
                "J.A.R.V.I.S Core Status",
                "http://127.0.0.1:8000",
                width=700,
                height=700,
                resizable=True,
                background_color="#020205"
            )
            webview.start()
        except Exception as e:
            logger.error(f"Failed to start GUI: {e}. Running in headless mode.")
            import time
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
    else:
        # Headless mode — just block main thread
        import time
        logger.info("Jarvis running in headless mode (no GUI).")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    print("\n  Goodbye!")
