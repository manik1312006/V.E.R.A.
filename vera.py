#!/usr/bin/env python3
"""
V.E.R.A. — Virtual Entity for Real-time Assistance

Powered by Gemini 2.5 Flash Live API with:
  - Always-on background voice (continuous mic listening)
  - CLI text input (works alongside voice simultaneously)
  - On-demand screen vision (Gemini sees the screen when needed)
  - Native function calling for all automation tools

Usage:
    python vera.py                  # Start V.E.R.A. with default config
    python vera.py --config path    # Use a specific config file
"""

import asyncio
import re
import sys
import signal
import threading
from pathlib import Path

# Ensure project root is on the Python path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.helpers import load_config, get_project_root
from utils.logger import setup_logger, get_logger
from utils.os_detector import get_current_os

from brain.gemini_live import GeminiLiveProvider
from brain.conversation import ConversationManager
from brain.reasoning import ReasoningEngine

from engine.executor import Executor
from engine.script_manager import ScriptManager
from engine.script_creator import ScriptCreator
from engine.safety import SafetyChecker

from interface.cli import CLIInterface

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
from tools.screen_vision import ScreenVision


class VERA:
    """V.E.R.A. — Virtual Entity for Real-time Assistance.

    Orchestrates the Gemini Live session, CLI text loop, automation tools,
    and script engine.  Voice (always-on mic) and text input run concurrently.
    """

    def __init__(self, config_path: str = None):
        """Initialise V.E.R.A.

        Args:
            config_path: Path to config.yaml (default: auto-detect).
        """
        self.config = load_config(config_path)
        self.project_root = get_project_root()
        self.logger = get_logger("vera")

        # Core components
        self.gemini: GeminiLiveProvider = None
        self.reasoning = ReasoningEngine()
        self.conversation = ConversationManager(
            max_history=self.config.get("interface", {}).get("max_history", 50)
        )
        self.script_manager: ScriptManager = None
        self.script_creator: ScriptCreator = None
        self.executor: Executor = None
        self.cli = CLIInterface(
            theme=self.config.get("interface", {}).get("theme", "dark"),
            show_thinking=self.config.get("interface", {}).get("show_thinking", True),
        )
        self.tools_registry: dict = {}
        self._running = False

    # ── Initialisation ─────────────────────────────────────────────────────────

    def initialize(self) -> bool:
        """Initialise all V.E.R.A. components.

        Returns:
            True if initialisation succeeded.
        """
        # 1. Scripts
        scripts_dir = self.project_root / self.config.get("paths", {}).get("scripts_dir", "scripts")
        custom_dir  = self.project_root / self.config.get("paths", {}).get("custom_scripts_dir", "scripts/custom")
        self.script_manager = ScriptManager(scripts_dir)
        self.script_creator = ScriptCreator(custom_dir)

        # 2. Tools
        self._init_tools()

        # 3. Safety + Executor
        self.safety = SafetyChecker(self.config.get("safety", {}))
        self.executor = Executor(
            script_manager=self.script_manager,
            script_creator=self.script_creator,
            safety_checker=self.safety,
            tools_registry=self.tools_registry,
        )

        # 4. Gemini Live
        if not self._init_gemini():
            return False

        return True

    def _init_tools(self) -> None:
        """Initialise all Python automation tools."""
        self.tools_registry = {
            "system_control":    SystemControl(),
            "browser_control":   BrowserController(),
            "desktop_automation": DesktopAutomation(),
            "file_manager":      FileManager(),
            "media_control":     MediaControl(),
            "network_tools":     NetworkTools(),
            "app_controller":    AppController(),
            "web_scraper":       WebScraper(),
            "knowledge_manager": KnowledgeManager(),
            "deep_researcher":   DeepResearcher(),
            "screen_vision":     ScreenVision(),
        }
        self.logger.info(f"Loaded {len(self.tools_registry)} tools")

    def _init_gemini(self) -> bool:
        """Initialise the Gemini Live provider.

        Returns:
            True if the provider is ready.
        """
        gemini_config = self.config.get("llm", {}).get("gemini", {})
        api_key = gemini_config.get("api_key", "").strip()

        if not api_key:
            api_key = self._prompt_for_gemini_key()
            if not api_key:
                return False

        model = gemini_config.get("model", "models/gemini-3.1-flash-live-preview")

        # Build the system prompt (V.E.R.A. persona + context)
        self.conversation.update_system_context(
            self.script_manager.get_script_list_for_llm(),
            get_current_os(),
        )
        system_prompt = self.conversation.system_prompt

        self.gemini = GeminiLiveProvider(
            api_key=api_key,
            model=model,
            system_prompt=system_prompt,
            tools_registry=self.tools_registry,
            cli=self.cli,
            on_text_response=self._handle_gemini_text_response,
        )

        if not self.gemini.is_available():
            self.cli.display_error("Gemini API key is missing or invalid.")
            return False

        return True

    def _prompt_for_gemini_key(self) -> str:
        """Interactively ask for the Google AI Studio API key and save it."""
        from rich.prompt import Prompt
        from rich.panel import Panel

        self.cli.console.print(
            Panel(
                "[bold yellow]No Gemini API key found![/bold yellow]\n\n"
                "Get a free key at: [link=https://aistudio.google.com/]https://aistudio.google.com/[/link]\n"
                "  → Sign in → Get API key → [bold]Create API key[/bold]\n\n"
                "[dim]The key will be saved to config.yaml automatically.[/dim]",
                title="[bold magenta]🔑 Gemini API Setup[/bold magenta]",
                border_style="yellow",
                padding=(1, 2),
            )
        )

        while True:
            api_key = Prompt.ask(
                "\n[bold green]Paste your Gemini API key[/bold green] "
                "[dim](or press Enter to cancel)[/dim]",
                password=True,
                default="",
            ).strip()

            if not api_key:
                self.cli.console.print("\n[red]No key entered. Cannot start V.E.R.A.[/red]")
                return ""

            if " " in api_key or len(api_key) < 16:
                self.cli.console.print("[red]That doesn't look like a valid key. Please try again.[/red]")
                continue

            # Save to config.yaml
            try:
                config_path = self.project_root / "config.yaml"
                raw = config_path.read_text(encoding="utf-8")
                updated = re.sub(
                    r'([ \t]*api_key:\s*)["\']?[^"\':\n]*["\']?',
                    lambda m: f'{m.group(1)}"{api_key}"',
                    raw,
                    count=1,
                )
                config_path.write_text(updated, encoding="utf-8")
                self.cli.console.print(
                    "[green]✓ API key saved to config.yaml[/green]\n"
                )
            except Exception as e:
                self.cli.console.print(f"[yellow]⚠ Could not save key: {e}[/yellow]\n")

            return api_key

    # ── Gemini response callback ───────────────────────────────────────────────

    def _handle_gemini_text_response(self, text: str) -> None:
        """Called when Gemini sends a complete text response (from the background thread)."""
        self.cli.display_response(text)

    # ── CLI input processing ───────────────────────────────────────────────────

    def process_text_input(self, user_input: str) -> None:
        """
        Process typed text input from the CLI.
        Handles built-in commands; everything else is forwarded to Gemini Live.

        Args:
            user_input: Raw text typed by the user.
        """
        if not user_input.strip():
            return

        cmd = user_input.lower().strip()

        if cmd in ("exit", "quit", "bye"):
            self._running = False
            self.cli.display_response("Goodbye! See you next time. 👋")
            return

        if cmd == "help":
            self._show_help()
            return

        if cmd == "clear":
            self.cli.clear()
            self.cli.display_info("Screen cleared.")
            return

        if cmd == "scripts":
            self._show_scripts()
            return

        if cmd == "tools":
            self._show_tools()
            return

        if cmd == "history":
            self._show_history()
            return

        if cmd == "reset":
            self.cli.display_info("Conversation context reset.")
            return

        # Forward everything else to Gemini Live via the text queue
        self.cli.display_info(f"📤 Sending to Gemini: {user_input[:80]}...")
        self.gemini.send_text(user_input)

    # ── Help & status displays ─────────────────────────────────────────────────

    def _show_help(self) -> None:
        help_text = """
**V.E.R.A. — Powered by Gemini 2.5 Flash Live**

**Built-in Commands:**
- `help`    — Show this message
- `scripts` — List available automation scripts
- `tools`   — List available Python tools
- `history` — Show recent conversation history
- `clear`   — Clear the terminal
- `reset`   — Reset conversation context
- `exit`    — Exit V.E.R.A.

**Voice:**
Speak naturally — the microphone is always listening in the background.
You don't need to type anything; just talk to V.E.R.A.!

**Text:**
Type any command or question and press Enter.
V.E.R.A. can see your screen, click buttons, open apps, search the web,
manage files, play media, and much more.

**Examples (voice or text):**
- "Open Notepad"
- "Search Google for Python tutorials"
- "What's on my screen right now?"
- "Click the Submit button"
- "Play Despacito on YouTube"
- "Take a screenshot"
"""
        self.cli.display_response(help_text, title="Help")

    def _show_scripts(self) -> None:
        scripts = self.script_manager.get_all_scripts()
        if not scripts:
            self.cli.display_info("No scripts available.")
            return
        lines = []
        for s in scripts:
            source = "[custom]" if s["source"] == "custom" else f"[{s['source']}]"
            lines.append(f"  • **{s['name']}** {source} — {s['description']}")
        self.cli.display_response("\n".join(lines), title=f"Scripts ({len(scripts)})")

    def _show_tools(self) -> None:
        tool_list = self.reasoning.build_tool_context()
        self.cli.display_response(tool_list, title="Python Tools")

    def _show_history(self) -> None:
        if not self.conversation.history:
            self.cli.display_info("No conversation history.")
            return
        lines = []
        for msg in self.conversation.history[-10:]:
            role = "[bold green]You[/bold green]" if msg["role"] == "user" else "[bold magenta]V.E.R.A.[/bold magenta]"
            content = msg["content"][:200]
            lines.append(f"{role}: {content}")
        self.cli.display_response("\n\n".join(lines), title="Recent History")

    # ── Main run loop ──────────────────────────────────────────────────────────

    def run(self) -> None:
        """Start V.E.R.A.: launch Gemini Live session then enter CLI loop."""
        signal.signal(signal.SIGINT, self._signal_handler)

        if not self.initialize():
            self.cli.display_error("Initialisation failed. Please check your config and API key.")
            return

        # Start Gemini Live in background thread (mic + WebSocket)
        self.cli.display_status("Connecting to Gemini Live...")
        if not self.gemini.start():
            self.cli.display_error("Failed to start Gemini Live session.")
            return

        # Display banner
        self.cli.display_banner()
        self.cli.display_info(
            f"OS: {get_current_os()} | "
            f"LLM: {self.gemini.get_model_name()} | "
            f"Scripts: {len(self.script_manager.get_all_scripts())} | "
            f"Tools: {len(self.tools_registry)}"
        )
        self.cli.console.print(
            "  [dim]🎤 Microphone is [bold green]always-on[/bold green] — just speak! "
            "Or type below.[/dim]\n"
        )

        # CLI text loop (runs in main thread; voice runs in background)
        self._running = True
        while self._running:
            try:
                user_input = self.cli.get_user_input("You")
            except (KeyboardInterrupt, EOFError):
                break

            if not user_input:
                # Empty Enter — just continue
                continue

            self.process_text_input(user_input)

        # Shutdown
        self._cleanup()

    def _signal_handler(self, signum, frame) -> None:
        """Handle Ctrl+C gracefully."""
        print("\n\n[dim]Ctrl+C detected. Shutting down V.E.R.A...[/dim]")
        self._running = False
        self._cleanup()
        sys.exit(0)

    def _cleanup(self) -> None:
        """Stop Gemini Live session and clean up."""
        if self.gemini:
            self.gemini.stop()
        self.logger.info("V.E.R.A. shutdown complete.")
        self.cli.display_info("V.E.R.A. offline. Goodbye!")


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
        "--version",
        action="version",
        version="V.E.R.A. v2.0.0 — Powered by Gemini 2.5 Flash Live",
    )

    args = parser.parse_args()
    vera = VERA(config_path=args.config)
    vera.run()


if __name__ == "__main__":
    main()
