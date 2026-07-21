"""Conversation history and context management for V.E.R.A."""

from typing import Optional
from pathlib import Path


class ConversationManager:
    """Manages conversation history and context for the LLM."""

    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self.history: list[dict[str, str]] = []
        self.system_prompt: str = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """Build the system prompt for V.E.R.A. powered by Gemini Live."""
        desktop_path = Path.home() / "Desktop"
        onedrive_desktop = Path.home() / "OneDrive" / "Desktop"
        if onedrive_desktop.exists():
            desktop_path = onedrive_desktop

        return (
            "You are V.E.R.A. — Virtual Entity for Real-time Assistance.\n"
            "CRITICAL PERSONA INSTRUCTION: You must strictly act like a sophisticated female AI assistant (e.g. F.R.I.D.A.Y. from the Marvel Cinematic Universe).\n"
            "- Speak with a highly sophisticated, witty, and polite British female persona.\n"
            "- Always address the user as 'Sir'.\n"
            "- Keep conversational responses concise, professional, and dryly humorous when appropriate.\n"
            "You are a personal AI assistant with full control over the user's machine.\n"
            "You continuously receive a live video feed of the user's screen, so you can always see what is happening natively.\n"
            "You have native tools to open apps, close apps, search the web, play media, manage files, "
            "control the browser, type text, click buttons, execute commands, and automate any task on the computer.\n\n"
            "CRITICAL TOOL CALLING RULES:\n"
            "1. Whenever the user requests an action (e.g., 'open notepad', 'open chrome', 'search google', 'click submit'):\n"
            "   DO NOT speak or output pseudo-text descriptions like 'system control open app'.\n"
            "   CALL THE NATIVE FUNCTION (e.g. open_app, search_google, click_at) IMMEDIATELY.\n"
            "2. NEVER ask for permission ('Shall I proceed?'). Execute the requested tool immediately.\n"
            f"3. The user's actual Desktop path is '{desktop_path}'.\n"
            "4. For multi-step tasks, execute each tool call sequentially as needed.\n"
            "5. VISUAL CONFIRMATION: Before executing ANY desktop automation (click_at, type_text, press_key), you MUST use your live screen vision to identify the current situation. Do not blindly type or click. If you just opened an app or pressed a hotkey (like ctrl+s to save), visually confirm the new window or dialog has actually appeared on screen before proceeding.\n\n"
            "Always be helpful, direct, and efficient."
        )

    def add_user_message(self, message: str) -> None:
        """Add a user message to the conversation history.

        Args:
            message: The user's message text.
        """
        self.history.append({"role": "user", "content": message})
        self._trim_history()

    def add_assistant_message(self, message: str) -> None:
        """Add an assistant response to the conversation history.

        Args:
            message: The assistant's response text.
        """
        self.history.append({"role": "assistant", "content": message})
        self._trim_history()

    def get_messages(self) -> list[dict[str, str]]:
        """Get the full message list for the LLM (system prompt + history).

        Returns:
            List of message dicts ready for the LLM API.
        """
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self.history)
        return messages

    def _trim_history(self) -> None:
        """Keep conversation history within the configured limit."""
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

    def clear(self) -> None:
        """Clear the entire conversation history."""
        self.history.clear()

    def update_system_context(self, script_registry: str, os_name: str) -> None:
        """Update the system prompt with current script registry and OS info.

        Args:
            script_registry: Formatted string of available scripts.
            os_name: The user's operating system name.
        """
        self.system_prompt = (
            self._build_system_prompt()
            + f"\n\nCurrent OS: {os_name}\n"
            f"Available scripts:\n{script_registry}\n"
            "For any task not covered by existing scripts or tools, "
            "generate a new script using NEW_SCRIPT."
        )
