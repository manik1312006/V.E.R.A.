"""CLI interface for V.E.R.A. — Rich-powered terminal interaction."""

from typing import Optional, Callable
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown
from rich.prompt import Prompt
from utils.logger import get_logger

logger = get_logger("vera.interface")


class CLIInterface:
    """Command-line interface powered by Rich for V.E.R.A."""

    def __init__(self, theme: str = "dark", show_thinking: bool = True):
        self.console = Console()
        self.theme = theme
        self.show_thinking = show_thinking
        self._on_input_callback: Optional[Callable] = None

    def display_banner(self) -> None:
        """Display V.E.R.A.'s startup banner."""
        banner = Text()
        banner.append("╔══════════════════════════════════════════════╗\n", style="cyan")
        banner.append("║                                              ║\n", style="cyan")
        banner.append("║", style="cyan")
        banner.append("    V.E.R.A. ", style="bold magenta")
        banner.append("                               ║\n", style="cyan")
        banner.append("║", style="cyan")
        banner.append("  Virtual Entity for Real-time Assistance", style="white")
        banner.append("   ║\n", style="cyan")
        banner.append("║                                              ║\n", style="cyan")
        banner.append("╚══════════════════════════════════════════════╝\n", style="cyan")
        banner.append("\nType ", style="white")
        banner.append("'help'", style="bold yellow")
        banner.append(" for commands, ", style="white")
        banner.append("'exit'", style="bold red")
        banner.append(" to quit, or just ask me anything!\n", style="white")
        self.console.print(banner)

    def display_status(self, status_text: str, spinner: bool = True) -> None:
        """Display a status message (e.g., "Thinking...").

        Args:
            status_text: Status message to display.
            spinner: Whether to show a spinner animation.
        """
        from rich.status import Status
        self.console.print(f"[dim italic]{status_text}...[/dim italic]")

    def display_response(self, text: str, title: str = "V.E.R.A.") -> None:
        """Display a response from V.E.R.A.

        Args:
            text: Response text (may contain markdown).
            title: Panel title.
        """
        if not text:
            return
        panel = Panel(
            Markdown(text),
            title=f"[bold magenta]{title}[/bold magenta]",
            border_style="magenta",
            padding=(1, 2),
        )
        self.console.print(panel)

    def display_action(self, action_type: str, details: str) -> None:
        """Display an action being executed.

        Args:
            action_type: Type of action (script, tool, etc.).
            details: Action details.
        """
        icon = {
            "script": "[yellow]▶[/yellow]",
            "new_script": "[green]✎[/green]",
            "tool": "[cyan]⚙[/cyan]",
        }.get(action_type, "[white]●[/white]")

        self.console.print(
            f"\n{icon} [dim]Executing {action_type}: {details}[/dim]"
        )

    def display_result(self, output: str, success: bool = True) -> None:
        """Display the result of an action.

        Args:
            output: Result text.
            success: Whether the action succeeded.
        """
        style = "green" if success else "red"
        icon = "✓" if success else "✗"
        if output:
            self.console.print(
                Panel(
                    f"[{style}]{output}[/{style}]",
                    title=f"[bold]{icon} Result[/bold]",
                    border_style=style,
                    padding=(0, 1),
                )
            )

    def display_error(self, error: str) -> None:
        """Display an error message.

        Args:
            error: Error text.
        """
        self.console.print(
            Panel(
                f"[red]{error}[/red]",
                title="[bold red]✗ Error[/bold red]",
                border_style="red",
                padding=(0, 1),
            )
        )

    def display_thinking(self, thought: str) -> None:
        """Display LLM thinking/reasoning (if enabled).

        Args:
            thought: The thinking text to display.
        """
        if self.show_thinking and thought:
            self.console.print(
                f"\n[dim italic]💭 {thought}[/dim italic]"
            )

    def get_user_input(self, prompt_text: str = "You") -> str:
        """Get input from the user.

        Args:
            prompt_text: Label for the input prompt.

        Returns:
            The user's input string, or empty string for exit.
        """
        try:
            user_input = Prompt.ask(
                f"\n[bold green]{prompt_text}[/bold green]"
            )
            return user_input.strip()
        except (KeyboardInterrupt, EOFError):
            return ""

    def display_info(self, text: str) -> None:
        """Display informational text.

        Args:
            text: Info text.
        """
        self.console.print(f"[dim]{text}[/dim]")

    def clear(self) -> None:
        """Clear the terminal screen."""
        self.console.clear()

    def select_model_interactive(
        self,
        models: list[dict],
        title: str = "Select a Model",
        prompt_text: str = "Use ↑↓ arrows to navigate, Enter to confirm, Esc to cancel",
    ) -> int:
        """Display an interactive model picker navigable with arrow keys.

        Args:
            models: List of model info dicts (each with at least 'name').
            title: Heading shown above the list.
            prompt_text: Instructions shown below the list.

        Returns:
            Index of the selected model, or -1 if the user cancelled (Esc).
        """
        import readchar

        if not models:
            self.display_error("No models found.")
            return -1

        selected = 0

        def render():
            """Redraw the model selection menu."""
            # Build the menu body
            lines = []
            for i, model in enumerate(models):
                name = model.get("name", "unknown")
                size = self._format_size(model.get("size", 0))
                marker = "❯" if i == selected else " "
                if i == selected:
                    lines.append(f"  [bold cyan]{marker}[/bold cyan] [bold white]{name}[/bold white]  [dim]({size})[/dim]")
                else:
                    lines.append(f"  [dim]{marker}  {name}  ({size})[/dim]")
            body = "\n".join(lines)

            panel = Panel(
                body,
                title=f"[bold magenta]{title}[/bold magenta]",
                border_style="magenta",
                padding=(1, 2),
                subtitle=f"[dim]{prompt_text}[/dim]",
            )
            self.console.print(panel)

        # Initial render
        render()

        # Build platform-safe key sets (some keys don't exist on all platforms)
        _k = readchar.key
        _up_keys    = tuple(k for k in (getattr(_k, "UP", None),    getattr(_k, "UP_ARROW", None))    if k is not None)
        _down_keys  = tuple(k for k in (getattr(_k, "DOWN", None),  getattr(_k, "DOWN_ARROW", None))  if k is not None)
        _enter_keys = tuple(k for k in (getattr(_k, "ENTER", None), getattr(_k, "CONTROL_J", None))   if k is not None)
        _esc_keys   = tuple(k for k in (getattr(_k, "ESC", None),   "\x1b")                            if k is not None)
        _ctrl_c     = getattr(_k, "CTRL_C", "\x03")

        # Input loop
        while True:
            key = readchar.readkey()

            if key in _up_keys:
                selected = (selected - 1) % len(models)
            elif key in _down_keys:
                selected = (selected + 1) % len(models)
            elif key in _enter_keys:
                # Confirm selection
                self.console.print(
                    f"\n[green]✓ Selected:[/green] [bold]{models[selected]['name']}[/bold]\n"
                )
                return selected
            elif key == _ctrl_c:
                raise KeyboardInterrupt
            elif key in _esc_keys:
                # Cancel
                self.console.print("\n[yellow]Selection cancelled.[/yellow]\n")
                return -1
            else:
                # Ignore other keys, but allow number-key shortcuts (1-9)
                if key.isdigit():
                    idx = int(key) - 1
                    if 0 <= idx < len(models):
                        selected = idx
                continue

            # Re-render: clear previous panel area and redraw
            # Move cursor up to overwrite the previous panel
            panel_height = len(models) + 6  # border + padding + subtitle
            self.console.print(f"\033[{panel_height}A\033[J", end="")
            render()

    def _format_size(self, size_bytes) -> str:
        """Format a byte count into a human-readable size string.

        Args:
            size_bytes: Size in bytes (int or str). Ollama may return either.

        Returns:
            Human-readable size (e.g., '4.1 GB', '500 MB').
        """
        if not size_bytes:
            return "unknown size"
        # Ollama can return size as a string; try to coerce to numeric first.
        try:
            size_bytes = int(size_bytes)
        except (ValueError, TypeError):
            # Already a human-readable string (e.g. "4.1 GB") — return as-is.
            return str(size_bytes)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} PB"

    def set_input_callback(self, callback: Callable) -> None:
        """Set a callback for when the user provides input.

        Args:
            callback: Function to call with user input.
        """
        self._on_input_callback = callback
