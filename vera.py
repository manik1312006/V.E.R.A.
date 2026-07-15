#!/usr/bin/env python3
"""
V.E.R.A. — Virtual Entity for Real-time Assistance

A personal AI assistant powered by Mistral Large with full machine control.
Supports Mistral Cloud API and Ollama (local) as LLM backends.

Usage:
    python vera.py                  # Start V.E.R.A. with default config
    python vera.py --config path    # Use a specific config file
    python vera.py --voice         # Enable voice input/output
    python vera.py --provider ollama # Use Ollama instead of Mistral API
"""

import sys
import signal
from pathlib import Path

# Ensure project root is on the Python path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.helpers import load_config, get_project_root
from utils.logger import setup_logger, get_logger
from utils.os_detector import get_current_os

from brain.llm_provider import LLMProvider
from brain.mistral_api import MistralAPIProvider
from brain.ollama_local import OllamaProvider
from brain.reasoning import ReasoningEngine
from brain.conversation import ConversationManager

from engine.executor import Executor
from engine.script_manager import ScriptManager
from engine.script_creator import ScriptCreator
from engine.safety import SafetyChecker

from interface.cli import CLIInterface
from interface.voice_input import VoiceInput
from interface.voice_output import VoiceOutput

from tools.system_control import SystemControl
from tools.browser_control import BrowserController
from tools.desktop_automation import DesktopAutomation
from tools.file_manager import FileManager
from tools.media_control import MediaControl
from tools.network_tools import NetworkTools
from tools.app_controller import AppController
from tools.web_scraper import WebScraper
from tools.knowledge_manager import KnowledgeManager
from tools.deep_researcher import DeepResearcher


class VERA:
    """V.E.R.A. — Virtual Entity for Real-time Assistance.

    The main orchestrator that connects the LLM brain, execution engine,
    tools, and user interface together.
    """

    def __init__(self, config_path: str = None, voice_enabled: bool = None,
                 provider_override: str = None):
        """Initialize V.E.R.A.

        Args:
            config_path: Path to config.yaml (default: auto-detect).
            voice_enabled: Override voice setting from config.
            provider_override: Override LLM provider ('mistral_api' or 'ollama_local').
        """
        # Load configuration
        self.config = load_config(config_path)
        self.project_root = get_project_root()
        self.logger = get_logger("vera")

        # Override settings from CLI flags
        if provider_override:
            self.config["llm"]["provider"] = provider_override
        if voice_enabled is not None:
            self.config["voice"]["enabled"] = voice_enabled

        # Initialize components
        self.llm: LLMProvider = None
        self.reasoning = ReasoningEngine()
        self.conversation = ConversationManager(
            max_history=self.config.get("interface", {}).get("max_history", 50)
        )
        self.script_manager = None
        self.script_creator = None
        self.executor = None
        self.cli = CLIInterface(
            theme=self.config.get("interface", {}).get("theme", "dark"),
            show_thinking=self.config.get("interface", {}).get("show_thinking", True),
        )
        self.voice_in = None
        self.voice_out = None
        self.tools_registry = {}

        self._running = False

    def initialize(self) -> bool:
        """Initialize all V.E.R.A. components.

        Returns:
            True if initialization succeeded.
        """
        # 1. Initialize LLM
        if not self._init_llm():
            return False

        # 2. Initialize script engine
        scripts_dir = self.project_root / self.config.get("paths", {}).get(
            "scripts_dir", "scripts"
        )
        custom_dir = self.project_root / self.config.get("paths", {}).get(
            "custom_scripts_dir", "scripts/custom"
        )
        self.script_manager = ScriptManager(scripts_dir)
        self.script_creator = ScriptCreator(custom_dir)

        # 3. Initialize tools
        self._init_tools()

        # 4. Initialize safety
        self.safety = SafetyChecker(self.config.get("safety", {}))

        # 5. Initialize executor
        self.executor = Executor(
            script_manager=self.script_manager,
            script_creator=self.script_creator,
            safety_checker=self.safety,
            tools_registry=self.tools_registry,
        )

        # 6. Update conversation context with available scripts and tools
        self._update_llm_context()

        # 7. Initialize voice (if enabled)
        if self.config.get("voice", {}).get("enabled", False):
            self._init_voice()

        return True

    def _init_llm(self) -> bool:
        """Initialize the LLM provider.

        Returns:
            True if LLM is available.
        """
        provider_name = self.config["llm"].get("provider", "mistral_api")
        self.logger.info(f"Initializing LLM provider: {provider_name}")

        if provider_name == "mistral_api":
            mistral_config = self.config["llm"].get("mistral", {})
            api_key = mistral_config.get("api_key", "")
            if not api_key:
                api_key = self._prompt_for_mistral_key()
                if api_key == "__OLLAMA__":
                    # config was updated, recursively initialize with new provider
                    return self._init_llm()
                if not api_key:
                    return False   # user declined / left blank

            self.llm = MistralAPIProvider(
                api_key=api_key,
                model=mistral_config.get("model", "mistral-large-latest"),
                temperature=mistral_config.get("temperature", 0.7),
                max_tokens=mistral_config.get("max_tokens", 4096),
            )
        elif provider_name == "ollama_local":
            ollama_config = self.config["llm"].get("ollama", {})
            self.llm = OllamaProvider(
                model=ollama_config.get("model", "mistral"),
                base_url=ollama_config.get("base_url", "http://localhost:11434"),
                temperature=ollama_config.get("temperature", 0.7),
            )
            # Let the user pick a model interactively via arrow keys
            self._select_ollama_model()
        else:
            self.logger.error(f"Unknown LLM provider: {provider_name}")
            print(f"\n[red]Error: Unknown LLM provider '{provider_name}'[/red]")
            return False

        # Check availability
        if not self.llm.is_available():
            model_name = self.llm.get_model_name()
            self.logger.warning(f"LLM not available: {model_name}")
            self.cli.console.print(f"\n[yellow]Warning: {model_name} is not currently available.[/yellow]")
            self.cli.console.print("V.E.R.A. will still start but LLM requests may fail.\n")
        else:
            self.logger.info(f"LLM ready: {self.llm.get_model_name()}")

        return True

    def _prompt_for_mistral_key(self) -> str:
        """Interactively ask the user for their Mistral API key and save it to config.yaml.

        Returns:
            The entered API key, or empty string if the user skipped.
        """
        import re
        from rich.prompt import Prompt
        from rich.panel import Panel

        self.cli.console.print(
            Panel(
                "[bold yellow]No Mistral API key found![/bold yellow]\n\n"
                "Get a free key at: [link=https://console.mistral.ai/]https://console.mistral.ai/[/link]\n"
                "  → Sign in → API Keys → [bold]Create new key[/bold]\n\n"
                "[dim]The key will be saved to config.yaml automatically.\n"
                "Press Enter without typing to switch to Ollama instead.[/dim]",
                title="[bold magenta]🔑 Mistral API Setup[/bold magenta]",
                border_style="yellow",
                padding=(1, 2),
            )
        )

        while True:
            api_key = Prompt.ask(
                "\n[bold green]Paste your Mistral API key[/bold green] "
                "[dim](or press Enter to use Ollama)[/dim]",
                password=True,   # hides the key while typing
                default="",
            ).strip()

            if not api_key:
                self.cli.console.print("\n[yellow]No key entered. Switching to Ollama locally...[/yellow]")
                try:
                    config_path = self.project_root / "config.yaml"
                    raw = config_path.read_text(encoding="utf-8")
                    updated = re.sub(
                        r'([ \t]*provider:\s*)["\']?mistral_api["\']?',
                        r'\g<1>"ollama_local"',
                        raw,
                        count=1,
                    )
                    config_path.write_text(updated, encoding="utf-8")
                    self.config["llm"]["provider"] = "ollama_local"
                except Exception as e:
                    self.logger.error(f"Failed to switch provider in config: {e}")
                return "__OLLAMA__"

            # Basic sanity check — Mistral keys have no spaces and are reasonably long
            if " " in api_key or len(api_key) < 16:
                self.cli.console.print(
                    "[red]That doesn't look like a valid key. Please try again.[/red]"
                )
                continue

            # Save to config.yaml (preserve all comments and formatting via regex)
            try:
                config_path = self.project_root / "config.yaml"
                raw = config_path.read_text(encoding="utf-8")

                # Replace the api_key line whether it's empty or has a placeholder
                updated = re.sub(
                    r'([ \t]*api_key:\s*)["\']?[^"\'\n]*["\']?',
                    lambda m: f'{m.group(1)}"{api_key}"',
                    raw,
                    count=1,
                )
                config_path.write_text(updated, encoding="utf-8")
                self.cli.console.print(
                    "[green]✓ API key saved to config.yaml[/green] — "
                    "you won't need to enter it again.\n"
                )
            except Exception as e:
                self.cli.console.print(
                    f"[yellow]⚠ Could not save key to config.yaml: {e}\n"
                    "Key will be used this session only.[/yellow]\n"
                )

            return api_key


    def _select_ollama_model(self) -> None:
        """Query Ollama for local models and let the user pick one interactively.

        Uses an arrow-key driven menu rendered by the CLI. If Ollama is not
        running, or the user cancels, the configured default model is kept.
        """

        if not isinstance(self.llm, OllamaProvider):
            return

        # Try to fetch the list of locally available models
        try:
            models = self.llm.list_models()
        except ImportError as e:
            self.cli.display_error(
                f"{e}\n\nInstall it with:  pip install ollama"
            )
            return
        except ConnectionError as e:
            self.cli.display_error(
                f"Could not connect to Ollama.\n{e}\n\n"
                "Make sure Ollama is running:  ollama serve"
            )
            return
        except Exception as e:
            self.cli.display_error(f"Failed to list Ollama models: {e}")
            return

        if not models:
            self.cli.display_error(
                "No models found in Ollama.\n"
                "Pull a model first, for example:  ollama pull mistral\n"
                f"Keeping configured default: {self.llm.model}"
            )
            return

        # Build the menu entries. Highlight the currently configured model.
        model_names = [m["name"] for m in models]
        title = "Choose a Local Model"

        self.cli.console.print(
            f"\n[bold cyan]Found {len(models)} model(s) in Ollama.[/bold cyan] "
            f"[dim](current: {self.llm.model})[/dim]\n"
        )

        selected_idx = self.cli.select_model_interactive(
            models=models,
            title=title,
            prompt_text="↑↓ navigate · Enter confirm · Esc to keep current",
        )

        if selected_idx >= 0:
            chosen = model_names[selected_idx]
            self.llm.set_model(chosen)
            self.logger.info(f"User selected Ollama model: {chosen}")
        else:
            # User cancelled — keep the configured default
            self.cli.console.print(
                f"[dim]Keeping configured model: {self.llm.model}[/dim]\n"
            )

    def _init_tools(self) -> None:
        """Initialize all Python automation tools."""
        self.tools_registry = {
            "system_control": SystemControl(),
            "browser_control": BrowserController(),
            "desktop_automation": DesktopAutomation(),
            "file_manager": FileManager(),
            "media_control": MediaControl(),
            "network_tools": NetworkTools(),
            "app_controller": AppController(),
            "web_scraper": WebScraper(),
            "knowledge_manager": KnowledgeManager(),
            "deep_researcher": DeepResearcher(),
        }
        self.logger.info(f"Loaded {len(self.tools_registry)} tools")

    def _init_voice(self) -> None:
        """Initialize voice input/output if configured."""
        voice_config = self.config.get("voice", {})

        # Voice output (TTS)
        self.voice_out = VoiceOutput(
            engine=voice_config.get("tts", {}).get("engine", "edge_tts"),
            voice=voice_config.get("tts", {}).get("voice", "en-US-JennyNeural"),
            rate=voice_config.get("tts", {}).get("rate", "+0%"),
            volume=voice_config.get("tts", {}).get("volume", "+0%"),
        )
        self.voice_out.initialize()

        # Voice input (STT)
        self.voice_in = VoiceInput(
            model_size=voice_config.get("stt", {}).get("model_size", "base"),
            language=voice_config.get("stt", {}).get("language", "en"),
        )
        self.voice_in.initialize()

        voice_status = []
        if self.voice_in.is_available():
            voice_status.append("Speech-to-Text ✓")
            self.voice_in.start_background_listening(self.process_input)
        if self.voice_out.is_available():
            voice_status.append("Text-to-Speech ✓")

        if voice_status:
            self.cli.display_info(f"Voice: {', '.join(voice_status)}")

    def _update_llm_context(self) -> None:
        """Update the LLM conversation context with available scripts and tools."""
        # Build script context
        script_list = self.script_manager.get_script_list_for_llm()
        tool_list = self.reasoning.build_tool_context()
        current_os = get_current_os()

        self.conversation.update_system_context(script_list, current_os)
        self.logger.info(f"Updated context with {len(self.script_manager.get_all_scripts())} scripts")

    def process_input(self, user_input: str) -> None:
        """Process a user's input through the full V.E.R.A. pipeline.

        Args:
            user_input: The user's text input.
        """
        if not user_input.strip():
            return

        # Handle special commands
        if user_input.lower().strip() in ("exit", "quit", "bye"):
            self._running = False
            self.cli.display_response("Goodbye! See you next time. 👋")
            if self.voice_out and self.voice_out.is_available():
                self.voice_out.speak("Goodbye! See you next time.")
            return

        if user_input.lower().strip() == "help":
            self._show_help()
            return

        if user_input.lower().strip() == "clear":
            self.cli.clear()
            self.conversation.clear()
            self.cli.display_info("Terminal cleared and conversation history reset.")
            return

        if user_input.lower().strip() == "scripts":
            self._show_scripts()
            return

        if user_input.lower().strip() == "tools":
            self._show_tools()
            return

        if user_input.lower().strip() == "history":
            self._show_history()
            return

        if user_input.lower().strip() == "reset":
            self.conversation.clear()
            self.cli.display_info("Conversation history cleared.")
            return

        if user_input.lower().strip() == "switch":
            current = self.config.get("llm", {}).get("provider", "mistral_api")
            new_provider = "ollama_local" if current == "mistral_api" else "mistral_api"
            
            # Update config file permanently
            try:
                import re
                config_path = self.project_root / "config.yaml"
                raw = config_path.read_text(encoding="utf-8")
                updated = re.sub(
                    r'([ \t]*provider:\s*)["\']?' + current + r'["\']?',
                    r'\g<1>"' + new_provider + '"',
                    raw,
                    count=1,
                )
                config_path.write_text(updated, encoding="utf-8")
                self.config["llm"]["provider"] = new_provider
                
                # Re-initialize the LLM
                self.cli.display_status(f"Switching to {new_provider}...")
                if self._init_llm():
                    self.cli.display_info(f"Successfully switched to {new_provider}!")
                else:
                    self.cli.display_error("Failed to initialize new provider. Restart V.E.R.A.")
            except Exception as e:
                self.cli.display_error(f"Failed to switch provider: {e}")
            return

        if user_input.lower().strip() == "toggle_voice":
            current_voice = self.config.get("voice", {}).get("enabled", False)
            new_voice = not current_voice
            
            # Update config file permanently
            try:
                import re
                config_path = self.project_root / "config.yaml"
                raw = config_path.read_text(encoding="utf-8")
                
                # Replace true/false for voice enabled
                if current_voice:
                    updated = re.sub(r'([ \t]*enabled:\s*)true', r'\g<1>false', raw, flags=re.IGNORECASE, count=1)
                else:
                    updated = re.sub(r'([ \t]*enabled:\s*)false', r'\g<1>true', raw, flags=re.IGNORECASE, count=1)
                
                config_path.write_text(updated, encoding="utf-8")
                if "voice" not in self.config:
                    self.config["voice"] = {}
                self.config["voice"]["enabled"] = new_voice
                
                if new_voice:
                    self.cli.display_status("Initializing voice modules (this might take a moment)...")
                    self._init_voice()
                    self.cli.display_info("Voice is ENABLED! Just say 'Vera, <command>' or type 'v'.")
                else:
                    if self.voice_in:
                        self.voice_in.stop_background_listening()
                    if self.voice_out:
                        self.voice_out.cleanup()
                    self.voice_in = None
                    self.voice_out = None
                    self.cli.display_info("Voice is now DISABLED.")
            except Exception as e:
                self.cli.display_error(f"Failed to toggle voice: {e}")
            return
        if user_input.lower().strip() in ("v", "voice", "/voice"):
            self._handle_voice_input()
            return

        # Add user message to conversation
        self.conversation.add_user_message(user_input)

        # Get LLM response
        self.cli.display_status("Thinking")
        try:
            messages = self.conversation.get_messages()
            llm_response = self.llm.chat(messages)
        except Exception as e:
            self.cli.display_error(f"LLM error: {e}")
            self.logger.error(f"LLM chat error: {e}")
            return

        if not llm_response:
            self.cli.display_error("No response from LLM.")
            return

        # Add LLM response to conversation
        self.conversation.add_assistant_message(llm_response)

        # Parse the response to extract action commands
        parsed = self.reasoning.parse_response(llm_response)

        # Display thinking (the raw LLM response)
        if self.cli.show_thinking and parsed.get("message"):
            self.cli.display_thinking(parsed["message"])

        # Execute the action
        action_type = parsed.get("type")

        if action_type == "conversation":
            # Pure conversational response
            self.cli.display_response(parsed.get("message", llm_response))
            if self.voice_out and self.voice_out.is_available():
                self.voice_out.speak(parsed.get("message", ""))

        elif action_type == "script":
            action = parsed["action"]
            script_name = action.get("script_name", "")
            arguments = action.get("arguments", "")
            self.cli.display_action("script", f"{script_name} {arguments}")
            result = self.executor.execute(parsed)
            self.cli.display_result(result.get("output", ""), result.get("success", False))
            if result.get("error"):
                self.cli.display_error(result["error"])
            # Also show conversational message if present
            if parsed.get("message"):
                self.cli.display_response(parsed["message"])

        elif action_type == "new_script":
            action = parsed["action"]
            script_name = action.get("script_name", "")
            self.cli.display_action("new_script", f"Creating '{script_name}'")
            result = self.executor.execute(parsed)
            self.cli.display_result(
                f"Created and executed: {script_name}",
                result.get("success", False),
            )
            if result.get("error"):
                self.cli.display_error(result["error"])
            # Reload script registry
            self.script_manager.reload()
            self._update_llm_context()
            if parsed.get("message"):
                self.cli.display_response(parsed["message"])

        elif action_type == "tool":
            action = parsed["action"]
            tool_name = action.get("tool_name", "")
            tool_action = action.get("tool_action", "")
            self.cli.display_action("tool", f"{tool_name}.{tool_action}")
            result = self.executor.execute(parsed)
            tool_output = result.get("output", "")
            self.cli.display_result(tool_output, result.get("success", False))
            if result.get("error"):
                self.cli.display_error(result["error"])

            # Auto-continue: feed tool result back to LLM so it can finish the task
            if tool_output and result.get("success", False):
                self.conversation.add_user_message(
                    f"[TOOL RESULT from {tool_name}.{tool_action}]:\n{tool_output}\n\n"
                    "Now use this data to complete my original request. Do NOT call any more tools — just analyse and respond."
                )
                self.cli.display_status("Thinking")
                try:
                    messages = self.conversation.get_messages()
                    followup_response = self.llm.chat(messages)
                    if followup_response:
                        self.conversation.add_assistant_message(followup_response)
                        followup_parsed = self.reasoning.parse_response(followup_response)
                        # Only show as conversational reply, do not chain another tool
                        self.cli.display_response(
                            followup_parsed.get("message", followup_response)
                        )
                        if self.voice_out and self.voice_out.is_available():
                            self.voice_out.speak(followup_parsed.get("message", followup_response))
                except Exception as e:
                    self.logger.error(f"Auto-continue LLM error: {e}")
            elif parsed.get("message"):
                self.cli.display_response(parsed["message"])

        else:
            # Fallback: show the raw response
            self.cli.display_response(llm_response)
            if self.voice_out and self.voice_out.is_available():
                self.voice_out.speak(llm_response)


    def _show_help(self) -> None:
        """Display help information."""
        voice_line = (
            "- `v` / `voice` / `/voice` — 🎤 Activate voice input (speak your command)\n"
            if (self.voice_in and self.voice_in.is_available()) else ""
        )
        help_text = f"""
**Commands:**
- `help` — Show this help message
- `scripts` — List available automation scripts
- `tools` — List available Python tools
- `history` — Show conversation history
- `clear` — Clear the terminal
- `reset` — Clear conversation history
- `switch` — Toggle between Mistral API and Ollama Local
- `toggle_voice` — Turn voice features on or off
{voice_line}- `exit` / `quit` — Exit V.E.R.A.

**How to use:**
Just type what you want me to do! For example:
- "Open Notepad"
- "Search YouTube for Python tutorials"
- "List all running processes"
- "Take a screenshot"
- "Play Despacito on YouTube"
- "Search Google for weather today"

I can also generate new scripts for tasks I haven't seen before!
"""
        self.cli.display_response(help_text, title="Help")

    def _show_scripts(self) -> None:
        """Display available scripts."""
        scripts = self.script_manager.get_all_scripts()
        if not scripts:
            self.cli.display_info("No scripts available.")
            return

        lines = []
        for s in scripts:
            source = "[custom]" if s["source"] == "custom" else f"[{s['source']}]"
            lines.append(f"  • **{s['name']}** {source} — {s['description']}")
        self.cli.display_response(
            "\n".join(lines),
            title=f"Scripts ({len(scripts)})"
        )

    def _show_tools(self) -> None:
        """Display available tools."""
        tool_list = self.reasoning.build_tool_context()
        self.cli.display_response(tool_list, title="Python Tools")

    def _show_history(self) -> None:
        """Display conversation history."""
        if not self.conversation.history:
            self.cli.display_info("No conversation history.")
            return

        lines = []
        for msg in self.conversation.history[-10:]:
            role = "[bold green]You[/bold green]" if msg["role"] == "user" else "[bold magenta]V.E.R.A.[/bold magenta]"
            content = msg["content"][:200]
            lines.append(f"{role}: {content}")
        self.cli.display_response("\n\n".join(lines), title="Recent History")

    def _handle_voice_input(self) -> None:
        """Record from the microphone, transcribe, and process as a normal command."""
        if not self.voice_in or not self.voice_in.is_available():
            self.cli.display_error(
                "Voice input is currently disabled.\n"
                "Type 'toggle_voice' to turn it on! (Requires faster-whisper and sounddevice)"
            )
            return

        duration = self.config.get("voice", {}).get("listen_duration", 7)
        self.cli.display_info(f"🎤 Listening for {duration}s... speak now!")

        transcribed = self.voice_in.listen(duration=duration)

        if not transcribed:
            self.cli.display_error("Could not hear anything. Please try again.")
            return

        self.cli.console.print(
            f"[dim]🎤 Heard:[/dim] [bold cyan]{transcribed}[/bold cyan]\n"
        )
        self.process_input(transcribed)

    def run(self) -> None:
        """Start the V.E.R.A. interactive loop."""
        # Handle Ctrl+C gracefully
        signal.signal(signal.SIGINT, self._signal_handler)

        # Initialize
        if not self.initialize():
            return

        # Display banner
        self.cli.display_banner()
        voice_hint = "  [dim]Type [bold]v[/bold] or [bold]voice[/bold] to speak[/dim]" if (
            self.voice_in and self.voice_in.is_available()
        ) else ""
        self.cli.display_info(
            f"OS: {get_current_os()} | "
            f"LLM: {self.llm.get_model_name()} | "
            f"Scripts: {len(self.script_manager.get_all_scripts())} | "
            f"Tools: {len(self.tools_registry)}"
        )
        if voice_hint:
            self.cli.console.print(voice_hint)

        # Start the interactive loop
        self._running = True
        while self._running:
            # Show mic hint in prompt when voice is available
            prompt_label = (
                "You [dim][bold]v[/bold]=voice[/dim]"
                if (self.voice_in and self.voice_in.is_available())
                else "You"
            )
            user_input = self.cli.get_user_input(prompt_label)
            if not user_input:
                self._running = False
                self.cli.display_response("Goodbye! 👋")
                break

            self.process_input(user_input)

        # Cleanup
        self._cleanup()

    def _signal_handler(self, signum, frame) -> None:
        """Handle Ctrl+C signal."""
        print("\n\n[dim]Ctrl+C detected. Exiting V.E.R.A...[/dim]")
        self._running = False
        self._cleanup()
        sys.exit(0)

    def _cleanup(self) -> None:
        if self.voice_in:
            self.voice_in.stop_background_listening()
        if self.voice_out:
            self.voice_out.cleanup()
        self.logger.info("V.E.R.A. shutdown complete.")


def main():
    """Main entry point for V.E.R.A."""
    import argparse

    parser = argparse.ArgumentParser(
        description="V.E.R.A. — Virtual Entity for Real-time Assistance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--config", "-c",
        type=str, default=None,
        help="Path to config.yaml (default: auto-detect)",
    )
    parser.add_argument(
        "--voice", "-v",
        action="store_true", default=None,
        help="Enable voice input/output",
    )
    parser.add_argument(
        "--provider", "-p",
        type=str, default=None,
        choices=["mistral_api", "ollama_local"],
        help="Override LLM provider",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="V.E.R.A. v1.0.0 — Virtual Entity for Real-time Assistance",
    )

    args = parser.parse_args()

    vera = VERA(
        config_path=args.config,
        voice_enabled=args.voice,
        provider_override=args.provider,
    )
    vera.run()


if __name__ == "__main__":
    main()
