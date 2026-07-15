"""App controller tool for V.E.R.A. — in-app typing and control."""

import time
import platform
from utils.logger import get_logger

logger = get_logger("vera.tools.app")


class AppController:
    """Controls application windows — focus, type, and interact with apps."""

    def execute(self, action: str, parameters: str) -> str:
        """Execute an app controller action.

        Args:
            action: The action to perform.
            parameters: Action parameters.

        Returns:
            Result message string.
        """
        handler = {
            "focus_app": self.focus_app,
            "type_in_app": self.type_in_app,
            "press_key_in_app": self.press_key_in_app,
            "maximize": self.maximize,
            "minimize": self.minimize,
            "list_windows": self.list_windows,
            "close_window": self.close_window,
        }.get(action)

        if not handler:
            return f"Unknown action: {action}. Available: {list(self._actions().keys())}"

        return handler(parameters)

    def _actions(self) -> dict:
        return {
            "focus_app": "Bring an app to foreground (params: app_name)",
            "type_in_app": "Type text in focused app (params: text)",
            "press_key_in_app": "Press key in focused app (params: key_name)",
            "maximize": "Maximize focused window (params: none)",
            "minimize": "Minimize focused window (params: none)",
            "list_windows": "List all open windows (params: none)",
            "close_window": "Close a window (params: app_name)",
        }

    def _get_pyautogui(self):
        try:
            import pyautogui
            pyautogui.FAILSAFE = False
            return pyautogui
        except ImportError:
            raise ImportError("PyAutoGUI not installed. Run: pip install pyautogui")

    def focus_app(self, app_name: str) -> str:
        system = platform.system().lower()
        try:
            if system == "windows":
                import subprocess
                # Use PowerShell to find and focus window
                cmd = (
                    f'$w = Get-Process "{app_name}" -ErrorAction SilentlyContinue | '
                    f'Select-Object -First 1 -ExpandProperty MainWindowHandle; '
                    f'if ($w) {{ [void][System.Reflection.Assembly]::LoadWithPartialName("Microsoft.VisualBasic"); '
                    f'[Microsoft.VisualBasic.Interaction]::AppActivate($w) }}'
                )
                result = subprocess.run(
                    ["powershell", "-Command", cmd],
                    capture_output=True, text=True, timeout=5
                )
                time.sleep(0.3)
                return f"Focused app: {app_name}"
            elif system == "darwin":
                import subprocess
                subprocess.run(["osascript", "-e",
                                f'tell application "{app_name}" to activate'],
                               capture_output=True, timeout=5)
                time.sleep(0.3)
                return f"Activated app: {app_name}"
            else:
                # Linux: try wmctrl
                import subprocess
                subprocess.run(["wmctrl", "-a", app_name],
                               capture_output=True, timeout=5)
                time.sleep(0.3)
                return f"Focused app: {app_name}"
        except Exception as e:
            return f"Failed to focus '{app_name}': {e}"

    def type_in_app(self, text: str) -> str:
        try:
            pyautogui = self._get_pyautogui()
            time.sleep(0.1)
            pyautogui.write(text, interval=0.02)
            return f"Typed in focused app: {text[:100]}{'...' if len(text) > 100 else ''}"
        except Exception as e:
            return f"Failed to type: {e}"

    def press_key_in_app(self, key: str) -> str:
        try:
            pyautogui = self._get_pyautogui()
            pyautogui.press(key.strip().lower())
            return f"Pressed key in focused app: {key}"
        except Exception as e:
            return f"Failed to press key: {e}"

    def maximize(self, _: str) -> str:
        system = platform.system().lower()
        try:
            if system == "windows":
                import pyautogui
                pyautogui.hotkey("win", "up")
            elif system == "darwin":
                import subprocess
                subprocess.run(["osascript", "-e",
                                'tell application "System Events" to keystroke "f" using {command down}'],
                               capture_output=True)
            else:
                import pyautogui
                pyautogui.hotkey("winleft", "up")
            return "Window maximized"
        except Exception as e:
            return f"Failed to maximize: {e}"

    def minimize(self, _: str) -> str:
        system = platform.system().lower()
        try:
            if system == "windows":
                import subprocess
                subprocess.run(
                    ["powershell", "-Command",
                     "[void][System.Reflection.Assembly]::LoadWithPartialName(\"Microsoft.VisualBasic\");"
                     "[Microsoft.VisualBasic.Interaction]::AppActivate((Get-Process | "
                     "Where-Object {$_.MainWindowTitle}).MainWindowHandle[0]); "
                     "[Microsoft.VisualBasic.Interaction]::SendKeys(\"% m\")"],
                    capture_output=True, timeout=5
                )
            elif system == "darwin":
                import subprocess
                subprocess.run(["osascript", "-e",
                                'tell application "System Events" to keystroke "m" using {command down}'],
                               capture_output=True)
            else:
                import pyautogui
                pyautogui.hotkey("winleft", "down")
            return "Window minimized"
        except Exception as e:
            return f"Failed to minimize: {e}"

    def list_windows(self, _: str) -> str:
        try:
            import psutil
            windows = []
            for proc in psutil.process_iter(["pid", "name"]):
                try:
                    if proc.info["name"] and proc.pid != proc.ppid():
                        windows.append(f"  PID: {proc.info['pid']:>6} | {proc.info['name']}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            if not windows:
                return "No windows found."
            return f"Open windows ({len(windows)}):\n" + "\n".join(windows[:30])
        except Exception as e:
            return f"Failed to list windows: {e}"

    def close_window(self, app_name: str) -> str:
        try:
            import psutil
            killed = []
            for proc in psutil.process_iter(["pid", "name"]):
                if app_name.lower() in proc.info["name"].lower():
                    proc.terminate()
                    killed.append(str(proc.info["pid"]))
            if killed:
                return f"Closed window: {app_name} (PIDs: {', '.join(killed)})"
            return f"No window found matching '{app_name}'"
        except Exception as e:
            return f"Failed to close window: {e}"
