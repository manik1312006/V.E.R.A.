"""
Gemini 2.5 Flash Live API provider for V.E.R.A.

Handles:
  - Persistent WebSocket session to gemini-2.5-flash via google-genai SDK
  - Real-time microphone audio streaming (16kHz PCM, 16-bit)
  - On-demand screen capture (JPEG frames via mss)
  - Native audio response playback via pyaudio
  - Gemini function declarations → dispatches to V.E.R.A. tool registry
  - Barge-in support (user can interrupt V.E.R.A. mid-speech)
  - Dual-mode: always-on background voice + CLI text input
"""

import asyncio
import base64
import io
import json
import queue
import re
import threading
import traceback
from pathlib import Path
from typing import Optional, Callable

from utils.logger import get_logger

logger = get_logger("vera.gemini_live")

# ── Audio constants ────────────────────────────────────────────────────────────
MIC_SAMPLE_RATE   = 16000   # Gemini Live input: 16 kHz
MIC_CHANNELS      = 1
MIC_CHUNK_FRAMES  = 1024
SPEAKER_SAMPLE_RATE = 24000 # Gemini Live output: 24 kHz PCM
SPEAKER_CHANNELS  = 1
SPEAKER_CHUNK     = 1024

# ── Screen capture ─────────────────────────────────────────────────────────────
SCREEN_JPEG_QUALITY = 70   # Lower = faster, smaller payload


class GeminiLiveProvider:
    """
    Wraps the Gemini Multimodal Live API session.

    Responsibilities:
      1. Open / close the persistent WebSocket session.
      2. Stream microphone audio continuously in the background.
      3. Capture and send a screen frame on-demand (when V.E.R.A. requests it).
      4. Play back Gemini's audio responses via the system speaker.
      5. Intercept function-call requests from Gemini and route them to
         the V.E.R.A. tool registry, returning results back to the session.
      6. Echo text transcripts to the CLI.
    """

    # ── Gemini function declarations (map to V.E.R.A. tools) ──────────────────
    TOOL_DECLARATIONS = [
        # system_control
        {
            "name": "open_app",
            "description": "Opens an application by name on the user's computer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "Name of the application to open (e.g. 'notepad', 'chrome', 'spotify')"}
                },
                "required": ["app_name"]
            }
        },
        {
            "name": "close_app",
            "description": "Closes/kills a running application by name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "Name of the application to close"}
                },
                "required": ["app_name"]
            }
        },
        {
            "name": "list_processes",
            "description": "Lists all currently running processes on the computer.",
            "parameters": {"type": "object", "properties": {}}
        },
        {
            "name": "kill_process",
            "description": "Kills a process by its name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "process_name": {"type": "string"}
                },
                "required": ["process_name"]
            }
        },
        {
            "name": "shutdown_computer",
            "description": "Shuts down the computer.",
            "parameters": {"type": "object", "properties": {}}
        },
        {
            "name": "restart_computer",
            "description": "Restarts the computer.",
            "parameters": {"type": "object", "properties": {}}
        },
        # browser_control
        {
            "name": "open_url",
            "description": "Opens a URL in the default web browser.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Full URL to open"}
                },
                "required": ["url"]
            }
        },
        {
            "name": "search_google",
            "description": "Searches Google for a query and opens the results in the browser.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        },
        {
            "name": "search_youtube",
            "description": "Searches YouTube for a query and opens the results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        },
        {
            "name": "play_youtube",
            "description": "Plays a specific YouTube video by URL or video ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "video_url": {"type": "string", "description": "YouTube URL or video ID"}
                },
                "required": ["video_url"]
            }
        },
        # desktop_automation
        {
            "name": "click_at",
            "description": "Moves the mouse and clicks at the specified screen coordinates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X coordinate in pixels"},
                    "y": {"type": "integer", "description": "Y coordinate in pixels"}
                },
                "required": ["x", "y"]
            }
        },
        {
            "name": "type_text",
            "description": "Types text using the keyboard (simulates keypresses).",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to type"}
                },
                "required": ["text"]
            }
        },
        {
            "name": "press_key",
            "description": "Presses a keyboard key (e.g. 'enter', 'escape', 'ctrl+c').",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"}
                },
                "required": ["key"]
            }
        },
        {
            "name": "scroll",
            "description": "Scrolls the mouse wheel up or down.",
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {"type": "string", "enum": ["up", "down"]},
                    "amount": {"type": "integer", "description": "Number of scroll steps", "default": 3}
                },
                "required": ["direction"]
            }
        },
        # file_manager
        {
            "name": "list_files",
            "description": "Lists files in a directory. Use 'desktop', 'downloads', 'documents' as shortcuts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path or shortcut"}
                },
                "required": ["path"]
            }
        },
        {
            "name": "read_file",
            "description": "Reads and returns the contents of a text file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"}
                },
                "required": ["path"]
            }
        },
        {
            "name": "open_file",
            "description": "Opens a file with its default application.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"}
                },
                "required": ["path"]
            }
        },
        {
            "name": "create_folder",
            "description": "Creates a new folder at the given path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"}
                },
                "required": ["path"]
            }
        },
        {
            "name": "copy_file",
            "description": "Copies a file from source to destination.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {"type": "string"},
                    "destination": {"type": "string"}
                },
                "required": ["source", "destination"]
            }
        },
        {
            "name": "delete_file",
            "description": "Deletes a file or folder. USE WITH CAUTION.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"}
                },
                "required": ["path"]
            }
        },
        # network_tools
        {
            "name": "search_web",
            "description": "Searches the web for a query and returns a text summary of results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        },
        {
            "name": "check_internet",
            "description": "Checks whether the computer is connected to the internet.",
            "parameters": {"type": "object", "properties": {}}
        },
        {
            "name": "ping_host",
            "description": "Pings a hostname or IP address and returns latency.",
            "parameters": {
                "type": "object",
                "properties": {
                    "host": {"type": "string"}
                },
                "required": ["host"]
            }
        },
        # app_controller
        {
            "name": "focus_app",
            "description": "Brings a running application window to the foreground.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string"}
                },
                "required": ["app_name"]
            }
        },
        {
            "name": "type_in_app",
            "description": "Focuses an application window and types text into it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string"},
                    "text": {"type": "string"}
                },
                "required": ["app_name", "text"]
            }
        },
        {
            "name": "list_windows",
            "description": "Lists all currently open application windows.",
            "parameters": {"type": "object", "properties": {}}
        },
        # media_control
        {
            "name": "volume_up",
            "description": "Increases the system volume.",
            "parameters": {"type": "object", "properties": {}}
        },
        {
            "name": "volume_down",
            "description": "Decreases the system volume.",
            "parameters": {"type": "object", "properties": {}}
        },
        {
            "name": "mute_audio",
            "description": "Mutes the system audio.",
            "parameters": {"type": "object", "properties": {}}
        },
        {
            "name": "unmute_audio",
            "description": "Unmutes the system audio.",
            "parameters": {"type": "object", "properties": {}}
        },
        # screen vision (on-demand)
        {
            "name": "capture_screen",
            "description": "Captures the current screen and analyzes it. Use this when you need to see what is currently visible on the user's monitor — e.g. to find button locations, read text, or verify state.",
            "parameters": {"type": "object", "properties": {}}
        },
        # knowledge_manager
        {
            "name": "search_knowledge",
            "description": "Searches V.E.R.A.'s local knowledge base for stored information on a topic.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"}
                },
                "required": ["topic"]
            }
        },
        {
            "name": "save_knowledge",
            "description": "Saves a piece of information to V.E.R.A.'s local knowledge base.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "content": {"type": "string"}
                },
                "required": ["topic", "content"]
            }
        },
        {
            "name": "list_knowledge_topics",
            "description": "Lists all topics stored in V.E.R.A.'s knowledge base.",
            "parameters": {"type": "object", "properties": {}}
        },
        # deep_researcher
        {
            "name": "deep_research",
            "description": "Performs autonomous deep web research on a topic — searches, scrapes and summarises multiple articles.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"}
                },
                "required": ["topic"]
            }
        },
    ]

    def __init__(
        self,
        api_key: str,
        model: str = "models/gemini-3.1-flash-live-preview",
        system_prompt: str = "",
        tools_registry: dict = None,
        cli=None,
        on_text_response: Optional[Callable[[str], None]] = None,
    ):
        self.api_key = api_key
        self.model = model
        self.system_prompt = system_prompt
        self.tools_registry = tools_registry or {}
        self.cli = cli
        self.on_text_response = on_text_response   # callback for CLI display

        self._session = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False

        # Audio I/O
        self._pyaudio = None
        self._mic_stream = None
        self._speaker_stream = None
        self._audio_out_queue: queue.Queue = queue.Queue()

        # Text input queue (from CLI)
        self._text_input_queue: asyncio.Queue = None

        # State flags for echo & interleaving prevention
        self._is_speaking = False
        self._is_processing_text = False

        logger.info(f"GeminiLiveProvider initialised — model: {self.model}")

    # ── Public API ─────────────────────────────────────────────────────────────

    def is_available(self) -> bool:
        """Returns True if the API key is set."""
        return bool(self.api_key)

    def get_model_name(self) -> str:
        return self.model

    def start(self) -> bool:
        """
        Start the Gemini Live session in a dedicated background thread with
        its own asyncio event loop.  Returns True if started successfully.
        """
        if self._running:
            return True
        if not self.api_key:
            logger.error("Gemini API key not set.")
            return False

        self._running = True
        self._thread = threading.Thread(
            target=self._run_event_loop, daemon=True, name="GeminiLiveThread"
        )
        self._thread.start()
        logger.info("Gemini Live session thread started.")
        return True

    def stop(self) -> None:
        """Stop the Gemini Live session and clean up audio resources."""
        self._running = False
        if self._loop and self._loop.is_running():
            # Wake up the text_sender so it can exit cleanly
            if hasattr(self, "_text_input_queue") and self._text_input_queue:
                self._loop.call_soon_threadsafe(
                    self._text_input_queue.put_nowait, "EXIT_SIGNAL"
                )
        if self._thread:
            self._thread.join(timeout=2)
        self._cleanup_audio()
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        logger.info("Gemini Live session stopped.")

    def send_text(self, text: str) -> None:
        """
        Send a text message to Gemini from the CLI (thread-safe).
        This puts the message into the async queue consumed by the session loop.
        """
        if self._loop and self._text_input_queue:
            self._loop.call_soon_threadsafe(
                self._text_input_queue.put_nowait, text
            )

    # ── Internal event loop ────────────────────────────────────────────────────

    def _run_event_loop(self) -> None:
        """Entry point for the background thread — owns its own event loop."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._session_loop())
        except Exception as e:
            logger.error(f"Gemini Live session error: {e}\n{traceback.format_exc()}")
        finally:
            self._loop.close()

    async def _session_loop(self) -> None:
        """
        Core async loop — opens the Gemini Live session and keeps it alive.

        Wraps the WebSocket connection in an outer reconnection loop so that
        if Gemini closes the session (e.g. after an idle timeout or a turn
        boundary that closes the stream), V.E.R.A. automatically reconnects
        within 2 seconds without requiring a restart.

        Audio I/O (PyAudio) is initialised once before the loop and shared
        across all reconnections.  The text-input queue also persists so that
        CLI messages queued while a reconnect is in progress are not lost.
        """
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            raise ImportError(
                "google-genai SDK not installed. Run: pip install google-genai"
            )

        client = genai.Client(api_key=self.api_key)

        # Create the text queue once — survives reconnects
        self._text_input_queue = asyncio.Queue()

        # Build session config (created once, reused on reconnect)
        config = types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            system_instruction=self.system_prompt,
            tools=[{"function_declarations": self.TOOL_DECLARATIONS}],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Aoede"   # British-sounding female voice
                    )
                )
            ),
        )

        # Initialise audio I/O once — shared across all reconnections
        self._init_audio()

        # ── Persistent reconnection loop ───────────────────────────────────
        reconnect_delay = 2   # seconds between reconnect attempts
        while self._running:
            try:
                logger.info(f"Connecting to Gemini Live: {self.model}")
                async with client.aio.live.connect(
                    model=self.model, config=config
                ) as session:
                    self._session = session
                    logger.info("Gemini Live WebSocket connected.")

                    if self.cli:
                        self.cli.display_info(
                            "🔗 Gemini Live connected — listening..."
                        )

                    # Run all coroutines concurrently.
                    # return_exceptions=True prevents one failing task from
                    # immediately cancelling the others.
                    results = await asyncio.gather(
                        self._mic_sender(session),
                        self._response_receiver(session),
                        self._speaker_player(),
                        self._text_sender(session),
                        self._screen_sender(session),
                        return_exceptions=True,
                    )

                    # Log any task-level exceptions
                    for i, result in enumerate(results):
                        if isinstance(result, Exception):
                            task_names = ["mic_sender", "response_receiver",
                                          "speaker_player", "text_sender", "screen_sender"]
                            logger.warning(
                                f"Task '{task_names[i]}' ended with: {result}"
                            )

            except Exception as e:
                if not self._running:
                    break
                logger.warning(
                    f"Gemini Live session dropped ({e}). "
                    f"Reconnecting in {reconnect_delay}s..."
                )
                if self.cli:
                    self.cli.console.print(
                        f"[yellow dim]⚡ Session dropped — reconnecting in "
                        f"{reconnect_delay}s...[/yellow dim]"
                    )

            if not self._running:
                break

            # Brief pause before reconnecting
            await asyncio.sleep(reconnect_delay)
            if self._running and self.cli:
                self.cli.console.print(
                    "[dim]🔄 Reconnecting to Gemini Live...[/dim]"
                )

    # ── Microphone streaming ───────────────────────────────────────────────────

    def _init_audio(self) -> None:
        """Initialise PyAudio for mic input and speaker output."""
        try:
            import pyaudiowpatch as pyaudio
            self._pyaudio = pyaudio.PyAudio()

            # Microphone input stream
            self._mic_stream = self._pyaudio.open(
                format=pyaudio.paInt16,
                channels=MIC_CHANNELS,
                rate=MIC_SAMPLE_RATE,
                input=True,
                frames_per_buffer=MIC_CHUNK_FRAMES,
            )

            # Speaker output stream
            self._speaker_stream = self._pyaudio.open(
                format=pyaudio.paInt16,
                channels=SPEAKER_CHANNELS,
                rate=SPEAKER_SAMPLE_RATE,
                output=True,
                frames_per_buffer=SPEAKER_CHUNK,
            )
            logger.info("PyAudio mic and speaker initialised.")
        except ImportError:
            raise ImportError("pyaudiowpatch not installed. Run: pip install pyaudiowpatch")
        except Exception as e:
            logger.error(f"Audio init failed: {e}")
            raise

    def _cleanup_audio(self) -> None:
        """Close PyAudio streams."""
        try:
            if self._mic_stream:
                self._mic_stream.stop_stream()
                self._mic_stream.close()
            if self._speaker_stream:
                self._speaker_stream.stop_stream()
                self._speaker_stream.close()
            if self._pyaudio:
                self._pyaudio.terminate()
        except Exception as e:
            logger.warning(f"Audio cleanup warning: {e}")

    async def _mic_sender(self, session) -> None:
        """
        Reads audio from PyAudio microphone stream and sends it to Gemini Live.
        """
        logger.info("Mic sender started.")
        loop = asyncio.get_event_loop()
        
        try:
            while self._running and self._session is session:
                # Do not send mic data if the model is speaking or processing a text turn
                if self._is_speaking or self._is_processing_text:
                    await asyncio.sleep(0.1)
                    continue

                if self._mic_stream:
                    # Read from microphone
                    data = await loop.run_in_executor(
                        None, self._mic_stream.read, MIC_CHUNK_FRAMES, False
                    )
                    
                    # Send to Gemini
                    await session.send_realtime_input(
                        audio={"mime_type": f"audio/pcm;rate={MIC_SAMPLE_RATE}", "data": data}
                    )
                
                # Yield control to the event loop
                await asyncio.sleep(0.001)
                
        except Exception as e:
            if self._running:
                logger.debug(f"Mic sender exiting: {e}")

    # ── Text input (CLI) ───────────────────────────────────────────────────────

    async def _text_sender(self, session) -> None:
        """
        Picks up text messages from the CLI input queue and sends them to Gemini.
        Waits for previous audio playback to complete before sending to avoid
        interleaving collisions mid-speech.
        """
        from google.genai import types
        logger.info("Text sender ready.")
        while self._running and self._session is session:
            try:
                text = await asyncio.wait_for(
                    self._text_input_queue.get(), timeout=0.5
                )
                if self._session is not session:
                    # Session closed mid-wait — put the text back and exit
                    self._text_input_queue.put_nowait(text)
                    break

                # If user submits a new prompt while V.E.R.A. is speaking, drain old audio queue & reset flag
                while not self._audio_out_queue.empty():
                    try:
                        self._audio_out_queue.get_nowait()
                    except Exception:
                        break
                self._is_speaking = False

                if self.cli:
                    self.cli.console.print(f"[dim yellow]DEBUG: _text_sender is sending '{text[:20]}' to Gemini...[/dim yellow]")

                self._is_processing_text = True
                await session.send_client_content(
                    turns=types.Content(
                        role="user",
                        parts=[types.Part(text=text)]
                    ),
                    turn_complete=True,
                )
                if self.cli:
                    self.cli.console.print("[dim yellow]DEBUG: _text_sender successfully sent client content![/dim yellow]")
                logger.info(f"Sent text to Gemini: {text[:80]}")
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                if self._running:
                    logger.debug(f"Text sender error: {e}")
                break

    # ── Response receiver ──────────────────────────────────────────────────────

    async def _response_receiver(self, session) -> None:
        """
        Listens to the Gemini WebSocket, decodes server responses, and pushes
        audio to the speaker queue.
        """
        handled_call_ids = set()
        transcript_parts = []
        speaking = False

        while self._running and self._session is session:
            try:
                async for response in session.receive():
                    # Any server message means server is responding
                    self._is_processing_text = False

                    # --- Iterate individual parts (audio / text / thought / function call) ---
                    if (response.server_content
                            and response.server_content.model_turn
                            and response.server_content.model_turn.parts):
                        for part in response.server_content.model_turn.parts:
                            # Audio chunk
                            if getattr(part, "inline_data", None):
                                audio_bytes = part.inline_data.data
                                if audio_bytes:
                                    self._is_speaking = True
                                    if not speaking and self.cli:
                                        self.cli.console.print(
                                            "[dim magenta]🔊 V.E.R.A. speaking...[/dim magenta]"
                                        )
                                        speaking = True
                                    self._audio_out_queue.put_nowait(audio_bytes)

                            # Spoken text transcript
                            elif getattr(part, "text", None) and part.text.strip():
                                t = part.text.strip()
                                if t not in transcript_parts:
                                    transcript_parts.append(t)
                                    if self.cli:
                                        self.cli.console.print(
                                            f"[dim italic cyan]V.E.R.A.: {t}[/dim italic cyan]"
                                        )

                            # Thought / reasoning
                            elif getattr(part, "thought", None) and part.thought:
                                thought_text = getattr(part, "text", "") or ""
                                if thought_text.strip() and self.cli:
                                    self.cli.console.print(
                                        f"[dim italic]💭 {thought_text.strip()[:120]}[/dim italic]"
                                    )

                            # Function call inside part
                            elif getattr(part, "function_call", None):
                                fc = part.function_call
                                call_id = getattr(fc, "id", None) or fc.name
                                logger.info(f"Received part.function_call: {fc.name}, id: {call_id}")
                                if call_id not in handled_call_ids:
                                    handled_call_ids.add(call_id)
                                    await self._handle_function_call(session, fc)

                    # Top-level tool call (older format fallback)
                    if response.tool_call:
                        for fc in response.tool_call.function_calls:
                            call_id = getattr(fc, "id", None) or fc.name
                            if call_id not in handled_call_ids:
                                handled_call_ids.add(call_id)
                                await self._handle_function_call(session, fc)

                    if response.server_content and response.server_content.turn_complete:
                        if speaking and self.cli:
                            self.cli.console.print("[dim]✓ Done[/dim]")
                        speaking = False
                        self._is_processing_text = False
                        if transcript_parts and self.on_text_response:
                            full_transcript = " ".join(transcript_parts).strip()
                            self.on_text_response(full_transcript)
                        transcript_parts.clear()
                        handled_call_ids.clear()
                        break

            except asyncio.CancelledError:
                break
            except Exception as e:
                if self._running:
                    logger.error(f"Response receiver error: {e}\n{traceback.format_exc()}")
                break

    # ── Speaker playback ───────────────────────────────────────────────────────

    async def _speaker_player(self) -> None:
        """
        Reads audio chunks from the output queue and plays them via PyAudio.
        Exits when the session closes (detected via _session becoming None or
        the running flag being cleared).
        """
        logger.info("Speaker player started.")
        loop = asyncio.get_event_loop()
        session_ref = self._session   # capture current session for lifetime check
        while self._running and self._session is session_ref:
            try:
                chunk = self._audio_out_queue.get_nowait()
                self._is_speaking = True
                await loop.run_in_executor(None, self._speaker_stream.write, chunk)
                if self._audio_out_queue.empty():
                    # 0.35s hangover delay so room reverb/speaker sound decay before unmuting mic
                    await asyncio.sleep(0.35)
                    if self._audio_out_queue.empty():
                        self._is_speaking = False
            except queue.Empty:
                await asyncio.sleep(0.01)
            except Exception as e:
                if self._running:
                    logger.error(f"Speaker error: {e}")
                await asyncio.sleep(0.05)

    # ── Function call dispatcher ───────────────────────────────────────────────

    async def _handle_function_call(self, session, function_call) -> None:
        """
        Receives a Gemini function call, executes the corresponding V.E.R.A.
        tool, and returns the result back to the session.
        """
        from google.genai import types

        fn_name = function_call.name
        fn_args = dict(function_call.args) if function_call.args else {}
        call_id = getattr(function_call, "id", None) or fn_name

        logger.info(f"Function call received: {fn_name}({fn_args})")

        # Show prominently in CLI so it's always visible
        if self.cli:
            self.cli.console.print(
                f"\n[bold magenta]⚙ TOOL CALL:[/bold magenta] "
                f"[cyan]{fn_name}[/cyan]([yellow]{fn_args}[/yellow])"
            )

        result_str = ""
        try:
            result_str = await asyncio.get_event_loop().run_in_executor(
                None, self._dispatch_tool, fn_name, fn_args
            )
        except Exception as e:
            result_str = f"Error executing {fn_name}: {e}"
            logger.error(result_str)

        # Determine success by checking for error keywords (ignore base64 strings)
        is_success = not any(
            kw in result_str.lower()
            for kw in ("error", "failed", "fail", "exception", "unknown")
        )

        if self.cli:
            # Truncate long result displays in CLI for clean output
            display_text = result_str[:250] + "..." if len(result_str) > 250 else result_str
            self.cli.display_result(display_text, success=is_success)

        # Allow text input again after tool execution finishes
        self._is_processing_text = False

        # Return result to Gemini so it can confirm the action
        try:
            # Strictly use the exact ID provided by the server, or None if omitted.
            # Do NOT fallback to fn_name for the ID, as this corrupts the server's dialog state!
            actual_id = getattr(function_call, "id", None)
            
            if self.cli:
                self.cli.console.print(f"[dim yellow]DEBUG: Sending tool response with id={actual_id} for fn={fn_name}[/dim yellow]")

            await session.send_tool_response(
                function_responses=[
                    types.FunctionResponse(
                        id=actual_id,
                        name=fn_name,
                        response={"result": result_str},
                    )
                ]
            )
        except Exception as e:
            logger.error(f"Failed to send tool response for {fn_name}: {e}")

    def _dispatch_tool(self, fn_name: str, fn_args: dict) -> str:
        """
        Maps Gemini function call names to V.E.R.A. tool registry calls.
        Returns a string result to feed back to Gemini.
        """
        tools = self.tools_registry

        try:
            # ── system_control ─────────────────────────────────────────────
            if fn_name == "open_app":
                return str(tools["system_control"].open_app(fn_args["app_name"]))
            if fn_name == "close_app":
                return str(tools["system_control"].close_app(fn_args["app_name"]))
            if fn_name == "list_processes":
                return str(tools["system_control"].list_processes())
            if fn_name == "kill_process":
                return str(tools["system_control"].kill_process(fn_args["process_name"]))
            if fn_name == "shutdown_computer":
                return str(tools["system_control"].shutdown())
            if fn_name == "restart_computer":
                return str(tools["system_control"].restart())

            # ── browser_control ────────────────────────────────────────────
            if fn_name == "open_url":
                return str(tools["browser_control"].open_url(fn_args["url"]))
            if fn_name == "search_google":
                return str(tools["browser_control"].search_google(fn_args["query"]))
            if fn_name == "search_youtube":
                return str(tools["browser_control"].search_youtube(fn_args["query"]))
            if fn_name == "play_youtube":
                return str(tools["browser_control"].play_youtube(fn_args["video_url"]))


            # ── desktop_automation ─────────────────────────────────────────
            if fn_name == "click_at":
                return str(tools["desktop_automation"].click_at(fn_args["x"], fn_args["y"]))
            if fn_name == "type_text":
                return str(tools["desktop_automation"].type_text(fn_args["text"]))
            if fn_name == "press_key":
                return str(tools["desktop_automation"].press_key(fn_args["key"]))
            if fn_name == "scroll":
                amount = fn_args.get("amount", 3)
                return str(tools["desktop_automation"].scroll(fn_args["direction"], amount))

            # ── file_manager ───────────────────────────────────────────────
            if fn_name == "list_files":
                return str(tools["file_manager"].list_files(fn_args["path"]))
            if fn_name == "read_file":
                return str(tools["file_manager"].read_file(fn_args["path"]))
            if fn_name == "open_file":
                return str(tools["file_manager"].open_file(fn_args["path"]))
            if fn_name == "create_folder":
                return str(tools["file_manager"].create_folder(fn_args["path"]))
            if fn_name == "copy_file":
                return str(tools["file_manager"].copy_file(fn_args["source"], fn_args["destination"]))
            if fn_name == "delete_file":
                return str(tools["file_manager"].delete_file(fn_args["path"]))

            # ── network_tools ──────────────────────────────────────────────
            if fn_name == "search_web":
                return str(tools["network_tools"].search_web(fn_args["query"]))
            if fn_name == "check_internet":
                return str(tools["network_tools"].check_internet())
            if fn_name == "ping_host":
                return str(tools["network_tools"].ping(fn_args["host"]))

            # ── app_controller ─────────────────────────────────────────────
            if fn_name == "focus_app":
                return str(tools["app_controller"].focus_app(fn_args["app_name"]))
            if fn_name == "type_in_app":
                param = f"{fn_args['app_name']}:{fn_args['text']}"
                return str(tools["app_controller"].type_in_app(param))
            if fn_name == "list_windows":
                return str(tools["app_controller"].list_windows())

            # ── media_control ──────────────────────────────────────────────
            if fn_name == "volume_up":
                return str(tools["media_control"].volume_up())
            if fn_name == "volume_down":
                return str(tools["media_control"].volume_down())
            if fn_name == "mute_audio":
                return str(tools["media_control"].mute())
            if fn_name == "unmute_audio":
                return str(tools["media_control"].unmute())

            # ── knowledge_manager ──────────────────────────────────────────
            if fn_name == "search_knowledge":
                return str(tools["knowledge_manager"].search_knowledge(fn_args["topic"]))
            if fn_name == "save_knowledge":
                return str(tools["knowledge_manager"].save_knowledge(fn_args["topic"], fn_args["content"]))
            if fn_name == "list_knowledge_topics":
                return str(tools["knowledge_manager"].list_topics())

            # ── deep_researcher ────────────────────────────────────────────
            if fn_name == "deep_research":
                return str(tools["deep_researcher"].run_deep_research(fn_args["topic"]))

            return f"Unknown function: {fn_name}"

        except KeyError as e:
            return f"Tool not available: {e}"
        except Exception as e:
            return f"Tool error ({fn_name}): {e}"

    async def _screen_sender(self, session) -> None:
        """
        Continuously captures the screen and sends it as video frames to Gemini Live at 1 FPS.
        """
        logger.info("Screen sender started.")
        loop = asyncio.get_event_loop()
        
        try:
            import mss
            from PIL import Image
            
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                
                while self._running and self._session is session:
                    # Capture screen
                    shot = await loop.run_in_executor(None, sct.grab, monitor)
                    img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
                    
                    # Resize to conserve tokens and bandwidth
                    max_width = 1024
                    if img.width > max_width:
                        ratio = max_width / img.width
                        img = img.resize(
                            (max_width, int(img.height * ratio)),
                            Image.LANCZOS
                        )
                    
                    # Send image frame directly to Gemini session using video=img
                    try:
                        await session.send_realtime_input(video=img)
                    except Exception as e:
                        if self._running:
                            logger.error(f"Screen sender send error: {e}")
                    
                    # Wait before next frame (1 FPS)
                    await asyncio.sleep(1.0)
                    
        except ImportError:
            logger.error("Screen capture unavailable — install mss and pillow")
        except Exception as e:
            if self._running:
                logger.error(f"Screen sender exiting: {e}")
