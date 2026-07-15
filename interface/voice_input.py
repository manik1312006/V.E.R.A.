"""Voice input (speech-to-text) for V.E.R.A."""

from typing import Optional
from utils.logger import get_logger

logger = get_logger("vera.interface.voice")


class VoiceInput:
    """Captures voice input and converts speech to text using faster-whisper."""

    def __init__(self, model_size: str = "base", language: str = "en"):
        """Initialize voice input.

        Args:
            model_size: Whisper model size (tiny, base, small, medium, large-v3).
            language: Language code (default: en).
        """
        self.model_size = model_size
        self.language = language
        self._model = None
        self._available = False

    def initialize(self) -> bool:
        """Load the Whisper model.

        Returns:
            True if the model loaded successfully.
        """
        try:
            from faster_whisper import WhisperModel
            logger.info(f"Loading Whisper model ({self.model_size})...")
            self._model = WhisperModel(
                self.model_size,
                device="cpu",
                compute_type="int8",
            )
            self._available = True
            logger.info("Whisper model loaded successfully.")
            return True
        except ImportError:
            logger.warning(
                "faster-whisper not installed. Voice input disabled. "
                "Install with: pip install faster-whisper"
            )
            return False
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            return False

    def listen(self, duration: float = 10.0) -> Optional[str]:
        """Listen to the microphone and transcribe speech.

        Args:
            duration: Recording duration in seconds.

        Returns:
            Transcribed text string, or None if transcription failed.
        """
        if not self._available or not self._model:
            logger.error("Voice input not available. Initialize first.")
            return None

        try:
            import sounddevice as sd
            import numpy as np

            # Record audio
            logger.info(f"Listening for {duration} seconds...")
            sample_rate = 16000
            audio = sd.rec(
                int(duration * sample_rate),
                samplerate=sample_rate,
                channels=1,
                dtype=np.float32,
            )
            sd.wait()

            # Transcribe
            segments, info = self._model.transcribe(
                audio.flatten(),
                language=self.language,
                beam_size=5,
            )

            text = " ".join(segment.text for segment in segments).strip()
            logger.info(f"Transcribed: {text}")
            return text if text else None

        except ImportError:
            logger.error("sounddevice not installed. Run: pip install sounddevice")
            return None
        except Exception as e:
            logger.error(f"Voice input failed: {e}")
            return None

    def is_available(self) -> bool:
        """Check if voice input is ready.

        Returns:
            True if the model is loaded and ready.
        """
        return self._available
