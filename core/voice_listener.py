"""
Jarvis Voice Listener — Speech-to-Text
=======================================
Uses faster-whisper (OpenAI Whisper, CPU-optimized) for transcription.
No internet needed for transcription — fully offline.

How it works:
1. Continuously monitors microphone
2. Detects when you START speaking (energy threshold)
3. Records your voice
4. Detects when you STOP speaking (1.5s of silence)
5. Sends audio to Whisper → returns text
"""

import asyncio
import io
import wave
import tempfile
import os
import time
from typing import Optional, Callable, Awaitable

import numpy as np
import sounddevice as sd
from scipy.io import wavfile
from faster_whisper import WhisperModel
from loguru import logger

from config import config


class VoiceListener:
    """
    Listens to microphone and transcribes speech using Whisper.
    Runs Voice Activity Detection (VAD) to know when you're speaking.
    """

    def __init__(self):
        logger.info(f"⏳ Loading Whisper model '{config.WHISPER_MODEL}'...")
        logger.info("   (First run downloads ~75MB for 'tiny' model — please wait)")

        # Load Whisper model — CPU mode (int8 = faster on CPU)
        self.whisper = WhisperModel(
            config.WHISPER_MODEL,
            device="cpu",
            compute_type="int8"
        )

        self.sample_rate = config.SAMPLE_RATE
        self.channels = config.CHANNELS
        self.silence_threshold = config.SILENCE_THRESHOLD
        self.silence_duration = config.SILENCE_DURATION  # seconds of silence = end of speech
        self.is_listening = False
        self.is_recording = False
        self.is_paused = False

        logger.info("✅ Voice listener ready — Whisper loaded!")

    async def listen_and_transcribe(self) -> Optional[str]:
        """
        Listen for one voice command and return the transcribed text.

        Flow:
        - Wait for speech to start
        - Record until 1.5s of silence
        - Transcribe with Whisper
        - Return text
        """
        if self.is_paused:
            await asyncio.sleep(0.5)
            return None

        logger.debug("👂 Listening... (speak now)")

        # Run blocking audio recording in thread pool
        loop = asyncio.get_event_loop()
        audio_data = await loop.run_in_executor(None, self._record_voice)

        if audio_data is None or len(audio_data) == 0:
            return None

        # Transcribe
        text = await loop.run_in_executor(None, self._transcribe, audio_data)
        return text

    def _record_voice(self) -> Optional[np.ndarray]:
        """
        Record audio from microphone.
        Returns numpy array of audio data.
        """
        frames = []
        silence_frames = 0
        speech_started = False
        max_silence_frames = int(self.silence_duration * self.sample_rate / 1024)

        # Pre-buffer: store last 0.8 seconds of audio (approx. 12 chunks of 1024 samples at 16kHz)
        # to ensure the start of the sentence is not clipped before energy exceeds threshold.
        pre_buffer = []
        pre_buffer_limit = int(0.8 * self.sample_rate / 1024)

        # Stream audio in chunks
        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype='int16',
            blocksize=1024
        ) as stream:

            while True:
                if not self.is_listening:
                    break

                chunk, overflowed = stream.read(1024)
                chunk_flat = chunk.flatten()

                # Calculate audio energy (volume)
                energy = np.sqrt(np.mean(chunk_flat.astype(np.float32) ** 2))

                if energy > self.silence_threshold:
                    # Speech detected!
                    if not speech_started:
                        logger.debug("🎤 Speech detected — recording...")
                        speech_started = True
                        # Prepend the pre-buffered audio to the capture
                        frames.extend(pre_buffer)
                    silence_frames = 0
                    frames.append(chunk_flat)

                else:
                    if not speech_started:
                        # Maintain a sliding history of the last 0.8 seconds
                        pre_buffer.append(chunk_flat)
                        if len(pre_buffer) > pre_buffer_limit:
                            pre_buffer.pop(0)
                    else:
                        # We have speech but now silence
                        frames.append(chunk_flat)
                        silence_frames += 1

                        if silence_frames >= max_silence_frames:
                            # Enough silence — speech has ended
                            logger.debug("✋ Speech ended — processing...")
                            break


                # Safety: max 30 seconds recording
                if speech_started and len(frames) > (self.sample_rate / 1024 * 30):
                    logger.warning("⚠️ Max recording length reached (30s)")
                    break

        if not frames or not speech_started:
            return None

        return np.concatenate(frames)


    def _transcribe(self, audio_data: np.ndarray) -> Optional[str]:
        """
        Transcribe audio using faster-whisper.
        Returns the transcribed text.
        """
        try:
            # Save to temp WAV file (Whisper reads from file)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
                wavfile.write(tmp_path, self.sample_rate, audio_data)

            # Transcribe with improved accuracy settings
            segments, info = self.whisper.transcribe(
                tmp_path,
                language="en",                   # Force English (faster)
                task="transcribe",
                beam_size=5,                     # Higher = more accurate (was 1)
                vad_filter=True,                 # Remove silence/background noise
                vad_parameters=dict(
                    min_silence_duration_ms=500, # Skip short silent gaps
                    speech_pad_ms=200,           # Pad around speech for context
                ),
                condition_on_previous_text=False, # Disable context priming to prevent hallucinations/context leak
                initial_prompt="Jarvis, Umesh, Skyra-Tech.", # Prime the model to recognize key names accurately
            )

            # Collect all segments, filtering out low-confidence ones
            text_parts = []
            for segment in segments:
                # Skip segments where Whisper is unsure it heard speech
                if segment.no_speech_prob > 0.6:
                    continue
                cleaned = segment.text.strip()
                if cleaned:
                    text_parts.append(cleaned)

            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

            text = " ".join(text_parts).strip()
            if text:
                logger.info(f"📝 Transcribed: '{text}'")
            return text if text else None

        except Exception as e:
            logger.error(f"❌ Transcription error: {e}")
            return None

    def start(self) -> None:
        """Mark listener as active."""
        self.is_listening = True

    def stop(self) -> None:
        """Stop listening."""
        self.is_listening = False

    @staticmethod
    def list_microphones() -> None:
        """Print all available microphones — useful for debugging."""
        print("\n🎤 Available microphones:")
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                print(f"  [{i}] {device['name']}")
        print(f"\n  Default: {sd.query_devices(kind='input')['name']}")
        print()
