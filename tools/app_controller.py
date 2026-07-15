"""App controller tool for V.E.R.A. — smart window focus, typing, and interaction.

Uses pywinauto on Windows for reliable window detection, focus, and text input.
Falls back to pyautogui on other platforms.
"""

import time
import platform
from utils.logger import get_logger

logger = get_logger("vera.tools.app")

SYSTEM = platform.system().lower()


class AppController:
    """Controls application windows — focus, type, and interact with apps like a human."""

    def execute(self, action: str, parameters: str) -> str:
        handler = {
            "focus_app":        self.focus_app,
            "type_in_app":      self.type_in_app,
            "press_key_in_app": self.press_key_in_app,
            "maximize":         self.maximize,
            "minimize":         self.minimize,
            "list_windows":     self.list_windows,
            "close_window":     self.close_window,
            "get_focused_app":  self.get_focused_app,
            "click_in_app":     self.click_in_app,
        }.get(action)

        if not handler:
            return f"Unknown action: {action}. Available: focus_app, type_in_app, press_key_in_app, maximize, minimize, list_windows, close_window, get_focused_app, click_in_app"

        return handler(parameters)

    # ── Windows helpers ──────────────────────────────────────────────────────

    def _find_window_win(self, app_name: str):
        """Return the first pywinauto Application object whose title matches app_name."""
        try:
            from pywinauto import Desktop
            app_lower = app_name.lower()
            for win in Desktop(backend="uia").windows():
                title = (win.window_text() or "").lower()
                proc  = ""
                try:
                    import psutil
                    proc = psutil.Process(win.process_id()).name().lower()
                except Exception:
                    pass
                if app_lower in title or app_lower in proc:
                    return win
            return None
        except Exception as e:
            logger.error(f"_find_window_win error: {e}")
            return None

    def _focus_window_win(self, app_name: str) -> str:
        """Bring a window to the foreground on Windows."""
        win = self._find_window_win(app_name)
        if win is None:
            return f"No window found matching '{app_name}'."
        try:
            win.set_focus()
            time.sleep(0.4)
            return f"Focused: '{win.window_text()}'"
        except Exception as e:
            # Fallback: click the taskbar button via Win32 API
            try:
                import ctypes
                hwnd = int(win.handle)
                SW_RESTORE = 9
                ctypes.windll.user32.ShowWindow(hwnd, SW_RESTORE)
                ctypes.windll.user32.SetForegroundWindow(hwnd)
                time.sleep(0.4)
                return f"Focused (via Win32): '{win.window_text()}'"
            except Exception as e2:
                return f"Failed to focus '{app_name}': {e2}"

    # ── Public actions ───────────────────────────────────────────────────────

    def get_focused_app(self, _: str = "") -> str:
        """Return the title of the currently focused window."""
        try:
            if SYSTEM == "windows":
                import ctypes
                hwnd = ctypes.windll.user32.GetForegroundWindow()
                length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                buf = ctypes.create_unicode_buffer(length + 1)
                ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
                return f"Currently focused window: '{buf.value}'"
            elif SYSTEM == "darwin":
                import subprocess
                r = subprocess.run(
                    ["osascript", "-e",
                     'tell application "System Events" to get name of first application process whose frontmost is true'],
                    capture_output=True, text=True
                )
                return f"Currently focused app: '{r.stdout.strip()}'"
            else:
                return "get_focused_app not supported on Linux."
        except Exception as e:
            return f"Failed to get focused app: {e}"

    def focus_app(self, app_name: str) -> str:
        """Bring a named app/window to the foreground."""
        app_name = app_name.strip().strip('"')
        try:
            if SYSTEM == "windows":
                return self._focus_window_win(app_name)
            elif SYSTEM == "darwin":
                import subprocess
                subprocess.run(
                    ["osascript", "-e", f'tell application "{app_name}" to activate'],
                    capture_output=True, timeout=5
                )
                time.sleep(0.4)
                return f"Activated: {app_name}"
            else:
                import subprocess
                subprocess.run(["wmctrl", "-a", app_name], capture_output=True, timeout=5)
                time.sleep(0.4)
                return f"Focused: {app_name}"
        except Exception as e:
            return f"Failed to focus '{app_name}': {e}"

    def type_in_app(self, params: str) -> str:
        """Type text in a specific app window.

        Params format: 'app_name:text to type'   OR just 'text to type'.
        If app_name is provided, the window is focused first.
        """
        params = params.strip()

        # Parse optional "app_name:text" format
        target_app = None
        text = params
        if ":" in params:
            potential_app, rest = params.split(":", 1)
            potential_app = potential_app.strip()
            # Only treat as app name if it's a short single word/phrase
            if len(potential_app) < 30 and " " not in potential_app.strip():
                target_app = potential_app
                text = rest.strip().strip('"')
            else:
                text = params  # The colon is part of the text itself

        # Focus the target app if specified
        if target_app:
            focus_result = self.focus_app(target_app)
            logger.info(f"Focus result: {focus_result}")
            time.sleep(0.5)

        if not text:
            return "No text provided to type."

        try:
            if SYSTEM == "windows":
                # Use pywinauto's send_keys for reliable Unicode support
                from pywinauto import keyboard
                # send_keys doesn't handle plain text well directly — use clipboard paste
                self._paste_text(text)
                return f"Typed in '{target_app or 'focused app'}': {text[:80]}{'...' if len(text) > 80 else ''}"
            else:
                import pyautogui
                pyautogui.FAILSAFE = False
                pyautogui.write(text, interval=0.01)
                return f"Typed in focused app: {text[:80]}{'...' if len(text) > 80 else ''}"
        except Exception as e:
            return f"Failed to type: {e}"

    def _paste_text(self, text: str) -> None:
        """Copy text to clipboard and paste it — handles Unicode and long strings."""
        import subprocess
        import ctypes

        # Write to clipboard via PowerShell (supports all Unicode)
        ps_cmd = f'Set-Clipboard -Value {repr(text)}'
        subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, timeout=5)
        time.sleep(0.15)

        # Paste using Ctrl+V
        import pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.1)

    def press_key_in_app(self, params: str) -> str:
        """Press a key in a specific app.

        Params: 'app_name:key'  OR just 'key'.
        """
        params = params.strip()
        target_app = None
        key = params

        if ":" in params:
            parts = params.split(":", 1)
            if len(parts[0].strip()) < 30:
                target_app = parts[0].strip()
                key = parts[1].strip()

        if target_app:
            self.focus_app(target_app)
            time.sleep(0.3)

        try:
            import pyautogui
            pyautogui.FAILSAFE = False
            pyautogui.press(key.strip().lower())
            return f"Pressed '{key}' in '{target_app or 'focused app'}'"
        except Exception as e:
            return f"Failed to press key '{key}': {e}"

    def click_in_app(self, params: str) -> str:
        """Click at coordinates within a specific app.

        Params: 'app_name:x,y'  OR 'x,y'.
        """
        try:
            parts = params.strip().split(":")
            if len(parts) == 2:
                self.focus_app(parts[0].strip())
                time.sleep(0.3)
                coords = parts[1]
            else:
                coords = parts[0]

            x, y = [int(v.strip()) for v in coords.split(",")]
            import pyautogui
            pyautogui.FAILSAFE = False
            pyautogui.click(x, y)
            return f"Clicked at ({x}, {y})"
        except Exception as e:
            return f"Failed to click: {e}"

    def maximize(self, app_name: str = "") -> str:
        app_name = (app_name or "").strip()
        try:
            if SYSTEM == "windows":
                if app_name:
                    self.focus_app(app_name)
                    time.sleep(0.2)
                import ctypes
                hwnd = ctypes.windll.user32.GetForegroundWindow()
                ctypes.windll.user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
                return f"Maximized '{app_name or 'focused window'}'"
            elif SYSTEM == "darwin":
                import subprocess
                subprocess.run(["osascript", "-e",
                                'tell application "System Events" to keystroke "f" using {command down, control down}'],
                               capture_output=True)
                return "Maximized"
            else:
                import pyautogui
                pyautogui.hotkey("winleft", "up")
                return "Maximized"
        except Exception as e:
            return f"Failed to maximize: {e}"

    def minimize(self, app_name: str = "") -> str:
        app_name = (app_name or "").strip()
        try:
            if SYSTEM == "windows":
                if app_name:
                    self.focus_app(app_name)
                    time.sleep(0.2)
                import ctypes
                hwnd = ctypes.windll.user32.GetForegroundWindow()
                ctypes.windll.user32.ShowWindow(hwnd, 6)  # SW_MINIMIZE
                return f"Minimized '{app_name or 'focused window'}'"
            elif SYSTEM == "darwin":
                import subprocess
                subprocess.run(["osascript", "-e",
                                'tell application "System Events" to keystroke "m" using {command down}'],
                               capture_output=True)
                return "Minimized"
            else:
                import pyautogui
                pyautogui.hotkey("winleft", "down")
                return "Minimized"
        except Exception as e:
            return f"Failed to minimize: {e}"

    def list_windows(self, _: str = "") -> str:
        """List all visible windows with their titles."""
        try:
            if SYSTEM == "windows":
                import ctypes

                EnumWindows = ctypes.windll.user32.EnumWindows
                GetWindowText = ctypes.windll.user32.GetWindowTextW
                GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
                IsWindowVisible = ctypes.windll.user32.IsWindowVisible

                windows = []
                WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))

                def foreach_window(hwnd, lParam):
                    if IsWindowVisible(hwnd):
                        length = GetWindowTextLength(hwnd)
                        if length > 0:
                            buf = ctypes.create_unicode_buffer(length + 1)
                            GetWindowText(hwnd, buf, length + 1)
                            windows.append(buf.value)
                    return True

                EnumWindows(WNDENUMPROC(foreach_window), 0)
                return "Open windows:\n" + "\n".join(f"  - {w}" for w in windows[:40])
            else:
                import psutil
                procs = [p.name() for p in psutil.process_iter(["name"]) if p.info["name"]]
                return "Running processes:\n" + "\n".join(f"  - {p}" for p in sorted(set(procs))[:40])
        except Exception as e:
            return f"Failed to list windows: {e}"

    def close_window(self, app_name: str) -> str:
        """Close a window by app name."""
        app_name = app_name.strip()
        try:
            if SYSTEM == "windows":
                win = self._find_window_win(app_name)
                if win:
                    win.close()
                    return f"Closed window: '{win.window_text()}'"
                return f"No window found matching '{app_name}'"
            else:
                import psutil
                killed = []
                for proc in psutil.process_iter(["pid", "name"]):
                    if app_name.lower() in proc.info["name"].lower():
                        proc.terminate()
                        killed.append(str(proc.info["pid"]))
                return f"Closed: {app_name} (PIDs: {', '.join(killed)})" if killed else f"No process found: '{app_name}'"
        except Exception as e:
            return f"Failed to close '{app_name}': {e}"
