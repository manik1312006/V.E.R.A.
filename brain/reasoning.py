"""Reasoning engine for V.E.R.A. — task analysis and decision making."""

import json
import re
from typing import Optional
from utils.logger import get_logger

logger = get_logger("vera.brain")


class ReasoningEngine:
    """Analyzes user requests and extracts structured action commands from LLM responses.

    The LLM returns responses with special prefixes indicating what action to take:
    - SCRIPT:<name>:<args>       → Run an existing script
    - NEW_SCRIPT:<name>:<desc>:<code> → Generate and save a new script
    - TOOL:<tool>:<action>:<params>    → Call a Python automation tool
    - (no prefix)               → Plain conversational response
    """

    PREFIX_SCRIPT = "SCRIPT:"
    PREFIX_NEW_SCRIPT = "NEW_SCRIPT:"
    PREFIX_TOOL = "TOOL:"

    def __init__(self):
        pass

    def parse_response(self, llm_response: str) -> dict:
        """Parse the LLM's response to extract an action command.

        Args:
            llm_response: Raw text response from the LLM.

        Returns:
            Dict with keys:
            - 'type': 'script', 'new_script', 'tool', or 'conversation'
            - 'action': extracted action details
            - 'message': conversational text (if any)
        """
        # Try to find action commands in the response
        result = self._extract_command(llm_response)

        if result:
            # Extract any conversational text outside the command
            clean_response = llm_response.replace(result["raw_command"], "").strip()
            result["message"] = clean_response if clean_response else None
            logger.info(f"Parsed action: {result['type']} → {result.get('action', {})}")
            return result

        # No command found — pure conversation
        return {
            "type": "conversation",
            "action": None,
            "message": llm_response.strip(),
        }

    def _extract_command(self, text: str) -> Optional[dict]:
        """Extract a structured command from the LLM response text.

        Args:
            text: The LLM response to scan.

        Returns:
            Command dict if a valid command is found, None otherwise.

        Note:
            NEW_SCRIPT must be checked before SCRIPT because the
            'SCRIPT:' pattern would match inside 'NEW_SCRIPT:'.
        """
        # Look for NEW_SCRIPT: prefix (check FIRST — before SCRIPT:)
        match = re.search(r"NEW_SCRIPT:([^:]+):([^:]+):(.*)", text, re.DOTALL | re.IGNORECASE)
        if match:
            return {
                "type": "new_script",
                "raw_command": match.group(0),
                "action": {
                    "script_name": match.group(1).strip(),
                    "description": match.group(2).strip(),
                    "code": match.group(3).strip(),
                },
            }

        # Look for SCRIPT: prefix (use negative lookbehind to avoid matching NEW_SCRIPT)
        match = re.search(r"(?<!NEW_)SCRIPT:([^:]+):(.*)", text, re.IGNORECASE)
        if match:
            return {
                "type": "script",
                "raw_command": match.group(0),
                "action": {
                    "script_name": match.group(1).strip(),
                    "arguments": match.group(2).strip(),
                },
            }

        # Look for TOOL: prefix
        match = re.search(r"TOOL:([^:]+):([^:]+):(.*)", text, re.DOTALL | re.IGNORECASE)
        if match:
            return {
                "type": "tool",
                "raw_command": match.group(0),
                "action": {
                    "tool_name": match.group(1).strip(),
                    "tool_action": match.group(2).strip(),
                    "parameters": match.group(3).strip(),
                },
            }

        return None

    def build_script_context(self, available_scripts: list[dict]) -> str:
        """Build a formatted string of available scripts for the LLM's context.

        Args:
            available_scripts: List of script info dicts with 'name' and 'description'.

        Returns:
            Formatted string listing all available scripts.
        """
        if not available_scripts:
            return "No scripts available."

        lines = []
        for script in available_scripts:
            lines.append(
                f"  - {script['name']}: {script.get('description', 'No description')}"
            )
        return "\n".join(lines)

    def build_tool_context(self) -> str:
        """Build a formatted string of available Python tools for the LLM's context.

        Returns:
            Formatted string listing all available tools and their actions.
        """
        tools = {
            "system_control": [
                "open_app:<app_name>",
                "close_app:<app_name>",
                "list_processes",
                "kill_process:<process_name>",
                "shutdown",
                "restart",
            ],
            "browser_control": [
                "open_url:<url>",
                "search_youtube:<query>",
                "play_youtube:<video_id_or_url>",
                "search_google:<query>",
                "take_screenshot",
            ],
            "desktop_automation": [
                "click_at:<x>,<y>",
                "type_text:<text>",
                "press_key:<key>",
                "scroll:<direction>",
                "screenshot",
            ],
            "file_manager": [
                "list_files:<path>",
                "copy_file:<source>:<dest>",
                "move_file:<source>:<dest>",
                "delete_file:<path>",
                "create_folder:<path>",
                "open_file:<path>",
            ],
            "media_control": [
                "play_youtube:<query>",
                "pause",
                "volume_up",
                "volume_down",
                "mute",
                "unmute",
            ],
            "network_tools": [
                "ping:<host>",
                "check_internet",
                "search_web:<query>",
                "download_file:<url>:<save_path>",
            ],
            "app_controller": [
                "focus_app:<app_name>",
                "type_in_app:<text>",
                "press_key_in_app:<key>",
                "maximize",
                "minimize",
            ],
        }

        lines = []
        for tool_name, actions in tools.items():
            lines.append(f"  {tool_name}:")
            for action in actions:
                lines.append(f"    - {action}")
        return "\n".join(lines)
