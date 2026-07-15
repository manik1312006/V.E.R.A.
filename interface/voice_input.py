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
            True if ready.
        """
        return self._available

    def start_background_listening(self, callback) -> None:
        """Starts a background thread that listens continuously for a wake word.

        Args:
            callback: Function to call when wake word is detected. Receives the command text.
        """
        if not self._available or not self._model:
            logger.error("Cannot start background listening: model not loaded.")
            return

        if hasattr(self, "_listening_thread") and self._listening_thread:
            return

        import threading
        self._stop_listening = False
        self._listening_thread = threading.Thread(
            target=self._background_listen_loop,
            args=(callback,),
            daemon=True
        )
        self._listening_thread.start()
        logger.info("Background voice listener started.")

    def stop_background_listening(self) -> None:
        """Stops the background listening thread."""
        self._stop_listening = True
        if hasattr(self, "_listening_thread") and self._listening_thread:
            self._listening_thread.join(timeout=2.0)
            self._listening_thread = None
            logger.info("Background voice listener stopped.")

    def _background_listen_loop(self, callback) -> None:
        import sounddevice as sd
        import numpy as np
        import queue
        import re

        sample_rate = 16000
        audio_queue = queue.Queue()

        def audio_callback(indata, frames, time, status):
            if status:
                logger.warning(f"Audio status: {status}")
            audio_queue.put(indata.copy())

        buffer = []
        is_speaking = False
        silence_timer = 0.0

        try:
            with sd.InputStream(samplerate=sample_rate, channels=1, dtype=np.float32, callback=audio_callback, blocksize=4000):
                while not self._stop_listening:
                    try:
                        data = audio_queue.get(timeout=0.1)
                        # VAD: Check if max amplitude exceeds a threshold (e.g. 0.05)
                        volume = np.max(np.abs(data))
                        
                        if volume > 0.01:
                            if not is_speaking:
                                logger.debug(f"Speech detected (vol: {volume:.4f})...")
                            is_speaking = True
                            silence_timer = 0.0
                        
                        if is_speaking:
                            buffer.append(data)
                            silence_timer += len(data) / sample_rate
                            
                            # If silent for 1.5 seconds, process the buffer
                            if silence_timer > 1.5:
                                audio_data = np.concatenate(buffer).flatten()
                                buffer = []
                                is_speaking = False
                                
                                # Process if longer than 0.5s
                                if len(audio_data) > sample_rate * 0.5:
                                    try:
                                        segments, _ = self._model.transcribe(audio_data, language=self.language, beam_size=1)
                                        text = " ".join(s.text for s in segments).strip()
                                        if not text:
                                            continue
                                            
                                        # Check for wake word
                                        clean_text = re.sub(r'^[^a-zA-Z0-9]+', '', text).lower()
                                        if clean_text.startswith("vera"):
                                            # Strip wake word and punctuation
                                            command = text[len("vera"):].strip(' ,.!?\n')
                                            if command:
                                                logger.info(f"Wake word detected! Command: {command}")
                                                callback(command)
                                    except Exception as e:
                                        logger.error(f"Background transcribe error: {e}")
                    except queue.Empty:
                        pass
        except Exception as e:
            logger.error(f"Background stream error: {e}")
