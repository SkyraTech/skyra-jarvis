"""
Jarvis Speaker — Text-to-Speech
================================
Uses Microsoft Edge TTS (edge-tts) for natural Indian English voice.
Completely FREE. No API key needed.
Works offline after first use (caches audio).
"""

import asyncio
import tempfile
import os
from pathlib import Path

import edge_tts
import pygame
from loguru import logger

from config import config
from utils.network import is_online
from core.ui_server import change_ui_state


class JarvisSpeaker:
    """
    Converts Jarvis's text responses to natural speech.
    Uses Microsoft Edge TTS — free, natural Indian English voice.
    """

    def __init__(self):
        # Initialize pygame mixer for audio playback
        pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
        self.voice = config.VOICE_NAME
        self.is_speaking = False
        logger.info(f"✅ Speaker initialized with voice: {self.voice}")

    async def speak(self, text: str) -> None:
        """
        Convert text to speech and play it.

        Args:
            text: The text to speak aloud
        """
        if not text or not text.strip():
            return

        # Clean text — remove markdown formatting (it sounds weird when spoken)
        clean_text = self._clean_for_speech(text)

        if not clean_text:
            return

        # Check connectivity for Edge TTS
        if not is_online():
            logger.warning("Offline state detected - skipped Edge TTS voice output.")
            print(f"\n  [OFFLINE] Jarvis: {text}\n")
            return

        self.is_speaking = True
        logger.info(f"🔊 Speaking: {clean_text[:60]}...")

        # Update 3D UI visualizer state
        change_ui_state("speaking")

        try:
            # Generate speech using Edge TTS
            communicate = edge_tts.Communicate(
                text=clean_text,
                voice=self.voice,
                rate="+10%",   # Slightly faster — sounds more natural for Jarvis
                volume="+0%",
            )

            # Save to a temp file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp_path = tmp.name

            await communicate.save(tmp_path)

            # Play the audio
            await self._play_audio(tmp_path)

            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

        except Exception as e:
            logger.error(f"❌ TTS error: {e}")
        finally:
            self.is_speaking = False
            change_ui_state("idle")

    async def _play_audio(self, file_path: str) -> None:
        """Play an audio file using pygame."""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._play_sync, file_path)
        except Exception as e:
            logger.error(f"❌ Audio playback error: {e}")

    def _play_sync(self, file_path: str) -> None:
        """Synchronous audio playback."""
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        # Wait for playback to finish
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

    def stop(self) -> None:
        """Stop current speech."""
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        self.is_speaking = False

    def _clean_for_speech(self, text: str) -> str:
        """Remove markdown and special chars that sound bad when spoken."""
        import re
        # Remove markdown bold/italic
        text = re.sub(r'\*{1,2}(.*?)\*{1,2}', r'\1', text)
        # Remove markdown headers
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        # Remove code blocks
        text = re.sub(r'```[\s\S]*?```', 'code block omitted', text)
        text = re.sub(r'`[^`]+`', '', text)
        # Remove bullet points
        text = re.sub(r'^[\*\-]\s+', '', text, flags=re.MULTILINE)
        # Remove URLs
        text = re.sub(r'http[s]?://\S+', 'link', text)
        # Clean up extra whitespace
        text = re.sub(r'\n+', '. ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
