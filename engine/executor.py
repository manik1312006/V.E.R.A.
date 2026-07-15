"""Main executor for V.E.R.A. — routes tasks to scripts or Python tools."""

import subprocess
import sys
import platform
from typing import Optional
from .script_manager import ScriptManager
from .script_creator import ScriptCreator
from .safety import SafetyChecker
from utils.logger import get_logger

logger = get_logger("vera.engine")


class Executor:
    """Executes tasks by running scripts or calling Python tools.

    The executor is the central hub that receives parsed commands from the
    reasoning engine and dispatches them to the appropriate handler:
    - SCRIPT commands → run an existing .bat/.sh script
    - NEW_SCRIPT commands → create a new script, then run it
    - TOOL commands → call a Python automation tool
    """

    def __init__(self, script_manager: ScriptManager, script_creator: ScriptCreator,
                 safety_checker: SafetyChecker, tools_registry: dict = None):
        self.script_manager = script_manager
        self.script_creator = script_creator
        self.safety = safety_checker
        self.tools_registry = tools_registry or {}

    def execute(self, parsed_command: dict) -> dict:
        """Execute a parsed command from the reasoning engine.

        Args:
            parsed_command: Dict with 'type', 'action', 'message' keys.

        Returns:
            Dict with 'success', 'output', 'error' keys.
        """
        action_type = parsed_command.get("type")
        action = parsed_command.get("action")
        message = parsed_command.get("message")

        if action_type == "conversation":
            return {"success": True, "output": message, "error": None}

        if not action:
            return {"success": False, "output": None, "error": "No action specified"}

        # Safety check
        safety_result = self.safety.check(action_type, action)
        if not safety_result.get("allowed", True):
            return {"success": False, "output": None, "error": safety_result.get("reason", "Action blocked")}

        # Route to the appropriate handler
        try:
            if action_type == "script":
                return self._run_script(action)
            elif action_type == "new_script":
                return self._create_and_run_script(action)
            elif action_type == "tool":
                return self._run_tool(action)
            else:
                return {"success": False, "output": None, "error": f"Unknown action type: {action_type}"}
        except Exception as e:
            logger.error(f"Execution error: {e}")
            return {"success": False, "output": None, "error": str(e)}

    def _run_script(self, action: dict) -> dict:
        """Execute an existing script.

        Args:
            action: Dict with 'script_name' and 'arguments'.

        Returns:
            Execution result dict.
        """
        script_name = action.get("script_name", "")
        arguments = action.get("arguments", "")

        script_info = self.script_manager.get_script(script_name)
        if not script_info:
            return {
                "success": False,
                "output": None,
                "error": f"Script '{script_name}' not found. Available: "
                         f"{[s['name'] for s in self.script_manager.get_all_scripts()]}",
            }

        script_path = script_info["path"]
        logger.info(f"Running script: {script_path} with args: {arguments}")

        return self._execute_file(script_path, arguments)

    def _create_and_run_script(self, action: dict) -> dict:
        """Create a new script from LLM output, then execute it.

        Args:
            action: Dict with 'script_name', 'description', 'code'.

        Returns:
            Execution result dict.
        """
        script_name = action.get("script_name", "")
        description = action.get("description", "")
        code = action.get("code", "")

        # Create the script
        result = self.script_creator.create_script(script_name, code, description)
        if not result["success"]:
            return {
                "success": False,
                "output": None,
                "error": f"Failed to create script: {result.get('error', 'Unknown error')}",
            }

        # Reload script registry so the new script is available
        self.script_manager.reload()

        logger.info(f"New script created: {result['path']}")

        # Execute the newly created script
        return self._execute_file(result["path"], "")

    def _run_tool(self, action: dict) -> dict:
        """Call a Python automation tool.

        Args:
            action: Dict with 'tool_name', 'tool_action', 'parameters'.

        Returns:
            Execution result dict.
        """
        tool_name = action.get("tool_name", "")
        tool_action = action.get("tool_action", "")
        parameters = action.get("parameters", "")

        if tool_name not in self.tools_registry:
            return {
                "success": False,
                "output": None,
                "error": f"Tool '{tool_name}' not found. Available: {list(self.tools_registry.keys())}",
            }

        tool = self.tools_registry[tool_name]
        logger.info(f"Calling tool: {tool_name}.{tool_action}({parameters})")

        try:
            result = tool.execute(tool_action, parameters)
            return {"success": True, "output": str(result), "error": None}
        except Exception as e:
            return {"success": False, "output": None, "error": str(e)}

    def _execute_file(self, file_path: str, arguments: str) -> dict:
        """Execute a script file on the current OS.

        Args:
            file_path: Path to the script file.
            arguments: Command-line arguments to pass.

        Returns:
            Execution result dict with stdout/stderr.
        """
        current_os = platform.system().lower()

        try:
            if current_os == "windows":
                # On Windows, run .bat files via cmd.exe
                cmd = f'cmd.exe /c "{file_path}" {arguments}'
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
            else:
                # On Linux/macOS, run .sh files via bash
                cmd = f'bash "{file_path}" {arguments}'
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

            output = result.stdout.strip() if result.stdout else ""
            error = result.stderr.strip() if result.stderr else ""

            if result.returncode != 0 and not output:
                return {"success": False, "output": output, "error": error or f"Exit code: {result.returncode}"}

            return {"success": True, "output": output, "error": error if error else None}

        except subprocess.TimeoutExpired:
            return {"success": False, "output": None, "error": "Script execution timed out (60s)"}
        except Exception as e:
            return {"success": False, "output": None, "error": str(e)}
