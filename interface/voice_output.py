"""Voice output (text-to-speech) for V.E.R.A."""

import asyncio
import tempfile
import os
from typing import Optional
from utils.logger import get_logger

logger = get_logger("vera.interface.voice")


class VoiceOutput:
    """Converts text responses to speech using edge-tts or pyttsx3."""

    def __init__(self, engine: str = "edge_tts", voice: str = "en-US-JennyNeural",
                 rate: str = "+0%", volume: str = "+0%"):
        """Initialize voice output.

        Args:
            engine: TTS engine ('edge_tts' or 'pyttsx3').
            voice: Voice name.
            rate: Speech rate adjustment (e.g., '+10%', '-10%').
            volume: Volume adjustment.
        """
        self.engine = engine
        self.voice = voice
        self.rate = rate
        self.volume = volume
        self._engine = None
        self._available = False

    def initialize(self) -> bool:
        """Initialize the TTS engine.

        Returns:
            True if initialization succeeded.
        """
        if self.engine == "edge_tts":
            return self._init_edge_tts()
        elif self.engine == "pyttsx3":
            return self._init_pyttsx3()
        else:
            logger.error(f"Unknown TTS engine: {self.engine}")
            return False

    def _init_edge_tts(self) -> bool:
        try:
            import edge_tts
            self._available = True
            logger.info("Edge TTS engine ready.")
            return True
        except ImportError:
            logger.warning(
                "edge-tts not installed. Falling back to pyttsx3. "
                "Install with: pip install edge-tts"
            )
            self.engine = "pyttsx3"
            return self._init_pyttsx3()

    def _init_pyttsx3(self) -> bool:
        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            self._available = True
            logger.info("pyttsx3 TTS engine ready.")
            return True
        except ImportError:
            logger.warning(
                "pyttsx3 not installed. Voice output disabled. "
                "Install with: pip install pyttsx3"
            )
            return False
        except Exception as e:
            logger.error(f"Failed to initialize pyttsx3: {e}")
            return False

    def speak(self, text: str) -> bool:
        """Speak the given text.

        Args:
            text: Text to convert to speech.

        Returns:
            True if speech played successfully.
        """
        if not self._available:
            return False

        # Truncate very long text for TTS
        text = text[:2000]

        if self.engine == "edge_tts":
            return self._speak_edge_tts(text)
        elif self.engine == "pyttsx3":
            return self._speak_pyttsx3(text)
        return False

    def _speak_edge_tts(self, text: str) -> bool:
        try:
            import edge_tts
            # edge_tts is async, so we run it in a new event loop
            async def _generate():
                communicate = edge_tts.Communicate(
                    text, self.voice, rate=self.rate, volume=self.volume
                )
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                    temp_path = f.name
                await communicate.save(temp_path)
                return temp_path

            loop = asyncio.new_event_loop()
            temp_path = loop.run_until_complete(_generate())
            loop.close()

            # Play the audio file
            self._play_audio(temp_path)

            # Clean up
            try:
                os.unlink(temp_path)
            except OSError:
                pass

            return True
        except Exception as e:
            logger.error(f"Edge TTS failed: {e}")
            return False

    def _speak_pyttsx3(self, text: str) -> bool:
        try:
            self._engine.say(text)
            self._engine.runAndWait()
            return True
        except Exception as e:
            logger.error(f"pyttsx3 speech failed: {e}")
            return False

    def _play_audio(self, file_path: str) -> None:
        """Play an audio file using the system's default player."""
        import platform
        import subprocess

        system = platform.system().lower()
        try:
            if system == "windows":
                # Use a hidden PowerShell process to avoid console noise
                subprocess.run(
                    ["powershell", "-c",
                     f"(New-Object Media.SoundPlayer '{file_path}').PlaySync()"],
                    capture_output=True, timeout=120,
                )
            elif system == "darwin":
                subprocess.run(["afplay", file_path],
                               capture_output=True, timeout=120)
            else:
                # Try mpg123 first, then aplay, then ffplay
                for player in ["mpg123", "aplay", "ffplay"]:
                    try:
                        subprocess.run([player, file_path],
                                       capture_output=True, timeout=120)
                        break
                    except FileNotFoundError:
                        continue
        except Exception as e:
            logger.error(f"Audio playback failed: {e}")

    def is_available(self) -> bool:
        """Check if voice output is ready.

        Returns:
            True if TTS engine is available.
        """
        return self._available

    def cleanup(self) -> None:
        """Clean up TTS resources."""
        if self._engine and self.engine == "pyttsx3":
            try:
                self._engine.stop()
            except Exception:
                pass
