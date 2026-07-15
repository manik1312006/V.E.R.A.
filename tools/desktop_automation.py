"""Desktop automation tool for V.E.R.A. — mouse/keyboard control."""

import time
import platform
from utils.logger import get_logger

logger = get_logger("vera.tools.desktop")


class DesktopAutomation:
    """Controls mouse and keyboard input for desktop automation."""

    def execute(self, action: str, parameters: str) -> str:
        """Execute a desktop automation action.

        Args:
            action: The action to perform.
            parameters: Action parameters.

        Returns:
            Result message string.
        """
        handler = {
            "click_at": self.click_at,
            "type_text": self.type_text,
            "press_key": self.press_key,
            "scroll": self.scroll,
            "screenshot": self.screenshot,
            "double_click": self.double_click,
            "right_click": self.right_click,
            "move_mouse": self.move_mouse,
            "hotkey": self.hotkey,
        }.get(action)

        if not handler:
            return f"Unknown action: {action}. Available: {list(self._actions().keys())}"

        return handler(parameters)

    def _actions(self) -> dict:
        return {
            "click_at": "Click at x,y coordinates (params: x,y)",
            "type_text": "Type text (params: text string)",
            "press_key": "Press a key (params: key name, e.g., enter, tab, escape)",
            "scroll": "Scroll up or down (params: up|down [clicks])",
            "screenshot": "Take a desktop screenshot (params: save_path)",
            "double_click": "Double click at x,y (params: x,y)",
            "right_click": "Right click at x,y (params: x,y)",
            "move_mouse": "Move mouse to x,y (params: x,y)",
            "hotkey": "Press a hotkey combo (params: ctrl+c, alt+tab, etc.)",
        }

    def _get_pyautogui(self):
        try:
            import pyautogui
            pyautogui.FAILSAFE = False
            return pyautogui
        except ImportError:
            raise ImportError(
                "PyAutoGUI not installed. Run: pip install pyautogui"
            )

    def click_at(self, coords: str) -> str:
        try:
            pyautogui = self._get_pyautogui()
            x, y = coords.split(",")
            x, y = int(x.strip()), int(y.strip())
            pyautogui.click(x, y)
            return f"Clicked at ({x}, {y})"
        except Exception as e:
            return f"Failed to click: {e}"

    def type_text(self, text: str) -> str:
        try:
            pyautogui = self._get_pyautogui()
            # Small delay to ensure focus
            time.sleep(0.1)
            pyautogui.write(text, interval=0.02)
            return f"Typed: {text[:100]}{'...' if len(text) > 100 else ''}"
        except Exception as e:
            return f"Failed to type: {e}"

    def press_key(self, key: str) -> str:
        try:
            pyautogui = self._get_pyautogui()
            pyautogui.press(key.strip().lower())
            return f"Pressed key: {key}"
        except Exception as e:
            return f"Failed to press key: {e}"

    def scroll(self, params: str) -> str:
        try:
            pyautogui = self._get_pyautogui()
            parts = params.strip().split()
            direction = parts[0].lower()
            clicks = int(parts[1]) if len(parts) > 1 else 3
            amount = clicks if direction == "up" else -clicks
            pyautogui.scroll(amount)
            return f"Scrolled {direction} by {clicks} clicks"
        except Exception as e:
            return f"Failed to scroll: {e}"

    def screenshot(self, save_path: str = "desktop_screenshot.png") -> str:
        try:
            pyautogui = self._get_pyautogui()
            pyautogui.screenshot(save_path)
            return f"Screenshot saved: {save_path}"
        except Exception as e:
            return f"Failed to take screenshot: {e}"

    def double_click(self, coords: str) -> str:
        try:
            pyautogui = self._get_pyautogui()
            x, y = coords.split(",")
            x, y = int(x.strip()), int(y.strip())
            pyautogui.doubleClick(x, y)
            return f"Double-clicked at ({x}, {y})"
        except Exception as e:
            return f"Failed to double-click: {e}"

    def right_click(self, coords: str) -> str:
        try:
            pyautogui = self._get_pyautogui()
            x, y = coords.split(",")
            x, y = int(x.strip()), int(y.strip())
            pyautogui.rightClick(x, y)
            return f"Right-clicked at ({x}, {y})"
        except Exception as e:
            return f"Failed to right-click: {e}"

    def move_mouse(self, coords: str) -> str:
        try:
            pyautogui = self._get_pyautogui()
            x, y = coords.split(",")
            x, y = int(x.strip()), int(y.strip())
            pyautogui.moveTo(x, y, duration=0.3)
            return f"Moved mouse to ({x}, {y})"
        except Exception as e:
            return f"Failed to move mouse: {e}"

    def hotkey(self, combo: str) -> str:
        try:
            pyautogui = self._get_pyautogui()
            keys = [k.strip().lower() for k in combo.split("+")]
            pyautogui.hotkey(*keys)
            return f"Pressed hotkey: {'+'.join(keys)}"
        except Exception as e:
            return f"Failed to press hotkey: {e}"
