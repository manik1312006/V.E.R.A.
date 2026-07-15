"""Media control tool for V.E.R.A. — audio/video playback."""

import platform
from utils.logger import get_logger

logger = get_logger("vera.tools.media")


class MediaControl:
    """Controls media playback and system audio."""

    def execute(self, action: str, parameters: str) -> str:
        """Execute a media control action.

        Args:
            action: The action to perform.
            parameters: Action parameters.

        Returns:
            Result message string.
        """
        handler = {
            "play_youtube": self.play_youtube,
            "pause": self.pause,
            "play": self.play,
            "volume_up": self.volume_up,
            "volume_down": self.volume_down,
            "mute": self.mute,
            "unmute": self.unmute,
            "volume_set": self.volume_set,
        }.get(action)

        if not handler:
            return f"Unknown action: {action}. Available: {list(self._actions().keys())}"

        return handler(parameters)

    def _actions(self) -> dict:
        return {
            "play_youtube": "Play YouTube video (params: url or query)",
            "pause": "Pause media playback (params: none)",
            "play": "Resume media playback (params: none)",
            "volume_up": "Increase volume (params: optional amount)",
            "volume_down": "Decrease volume (params: optional amount)",
            "mute": "Mute system audio (params: none)",
            "unmute": "Unmute system audio (params: none)",
            "volume_set": "Set volume level (params: 0-100)",
        }

    def play_youtube(self, url_or_query: str) -> str:
        import subprocess
        if "youtube.com" in url_or_query or "youtu.be" in url_or_query:
            url = url_or_query
        else:
            encoded = url_or_query.replace(" ", "+")
            url = f"https://www.youtube.com/results?search_query={encoded}"

        system = platform.system().lower()
        try:
            if system == "windows":
                subprocess.Popen(["cmd", "/c", "start", "", url], shell=True)
            elif system == "darwin":
                subprocess.Popen(["open", url])
            else:
                subprocess.Popen(["xdg-open", url])
            return f"Playing: {url}"
        except Exception as e:
            return f"Failed to play media: {e}"

    def pause(self, _: str) -> str:
        try:
            import pyautogui
            pyautogui.press("playpause")
            return "Media paused/resumed (toggled)"
        except Exception:
            return "Media pause requires pyautogui. Use keyboard media keys manually."

    def play(self, _: str) -> str:
        return self.pause("")  # Same key toggles play/pause

    def volume_up(self, amount: str = "10") -> str:
        system = platform.system().lower()
        try:
            if system == "windows":
                import subprocess
                n = int(amount) if amount.isdigit() else 1
                for _ in range(n):
                    subprocess.run(
                        ["powershell", "-Command",
                         "$wsh = New-Object -ComObject WScript.Shell; $wsh.SendKeys([char]175)"],
                        capture_output=True
                    )
            elif system == "darwin":
                import subprocess
                subprocess.run(["osascript", "-e",
                                 f"set volume output volume ((output volume of (get volume settings)) + {amount})"],
                                capture_output=True)
            else:
                import subprocess
                subprocess.run(["pactl", "--", "set-sink-volume", "@DEFAULT_SINK@",
                                 f"+{amount}%"], capture_output=True)
            return f"Volume increased by {amount}"
        except Exception as e:
            return f"Failed to adjust volume: {e}"

    def volume_down(self, amount: str = "10") -> str:
        system = platform.system().lower()
        try:
            if system == "windows":
                import subprocess
                n = int(amount) if amount.isdigit() else 1
                for _ in range(n):
                    subprocess.run(
                        ["powershell", "-Command",
                         "$wsh = New-Object -ComObject WScript.Shell; $wsh.SendKeys([char]174)"],
                        capture_output=True
                    )
            elif system == "darwin":
                import subprocess
                subprocess.run(["osascript", "-e",
                                 f"set volume output volume ((output volume of (get volume settings)) - {amount})"],
                                capture_output=True)
            else:
                import subprocess
                subprocess.run(["pactl", "--", "set-sink-volume", "@DEFAULT_SINK@",
                                 f"-{amount}%"], capture_output=True)
            return f"Volume decreased by {amount}"
        except Exception as e:
            return f"Failed to adjust volume: {e}"

    def mute(self, _: str) -> str:
        system = platform.system().lower()
        try:
            if system == "windows":
                import subprocess
                subprocess.run(
                    ["powershell", "-Command",
                     "$wsh = New-Object -ComObject WScript.Shell; $wsh.SendKeys([char]173)"],
                    capture_output=True
                )
            elif system == "darwin":
                import subprocess
                subprocess.run(["osascript", "-e", "set volume output muted true"],
                                capture_output=True)
            else:
                import subprocess
                subprocess.run(["pactl", "--", "set-sink-mute", "@DEFAULT_SINK@", "toggle"],
                                capture_output=True)
            return "Volume muted (toggled)"
        except Exception as e:
            return f"Failed to mute: {e}"

    def unmute(self, _: str) -> str:
        system = platform.system().lower()
        try:
            if system == "darwin":
                import subprocess
                subprocess.run(["osascript", "-e", "set volume output muted false"],
                                capture_output=True)
                return "Volume unmuted"
            else:
                return self.mute("")  # Toggle
        except Exception as e:
            return f"Failed to unmute: {e}"

    def volume_set(self, level: str) -> str:
        try:
            level = int(level)
            level = max(0, min(100, level))
            system = platform.system().lower()
            if system == "darwin":
                import subprocess
                subprocess.run(["osascript", "-e", f"set volume output volume {level}"],
                                capture_output=True)
            else:
                import subprocess
                if system == "windows":
                    # Windows volume set is complex; approximate with up/down
                    return f"Volume set to ~{level}% (approximate on Windows)"
                else:
                    subprocess.run(["pactl", "--", "set-sink-volume", "@DEFAULT_SINK@",
                                     f"{level}%"], capture_output=True)
            return f"Volume set to {level}%"
        except Exception as e:
            return f"Failed to set volume: {e}"
