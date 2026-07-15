"""Browser control tool for V.E.R.A. — opens the user's REAL system browser.

Uses the system's default or Chrome browser via webbrowser/subprocess.
Playwright is NOT used here — it is reserved for web_scraper (headless scraping).
"""

import webbrowser
import subprocess
import platform
import time
from urllib.parse import quote_plus
from utils.logger import get_logger

logger = get_logger("vera.tools.browser")

SYSTEM = platform.system().lower()


def _open_in_chrome(url: str) -> bool:
    """Try to open a URL in the real installed Chrome/Edge browser. Returns True on success."""
    chrome_paths = []
    if SYSTEM == "windows":
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ]
        for path in chrome_paths:
            try:
                subprocess.Popen([path, url])
                return True
            except FileNotFoundError:
                continue
    elif SYSTEM == "darwin":
        try:
            subprocess.Popen(["open", "-a", "Google Chrome", url])
            return True
        except Exception:
            try:
                subprocess.Popen(["open", "-a", "Safari", url])
                return True
            except Exception:
                pass
    else:
        for browser in ["google-chrome", "chromium-browser", "chromium", "firefox", "xdg-open"]:
            try:
                subprocess.Popen([browser, url])
                return True
            except FileNotFoundError:
                continue
    return False


class BrowserController:
    """Opens URLs and searches in the user's real system browser."""

    def execute(self, action: str, parameters: str) -> str:
        handler = {
            "open_url":       self.open_url,
            "search_youtube": self.search_youtube,
            "play_youtube":   self.play_youtube,
            "search_google":  self.search_google,
            "take_screenshot":self.take_screenshot,
        }.get(action)

        if not handler:
            return (
                f"Unknown action: {action}. "
                f"Available: open_url, search_youtube, play_youtube, search_google, take_screenshot"
            )
        return handler(parameters)

    def open_url(self, url: str) -> str:
        url = url.strip().strip('"\'')
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        try:
            opened = _open_in_chrome(url)
            if not opened:
                webbrowser.open(url)
            time.sleep(0.5)
            return f"Opened in browser: {url}"
        except Exception as e:
            return f"Failed to open URL '{url}': {e}"

    def search_youtube(self, query: str) -> str:
        query = query.strip().strip('"\'')
        url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
        result = self.open_url(url)
        return f"Searched YouTube for '{query}'. {result}"

    def play_youtube(self, url_or_query: str) -> str:
        url_or_query = url_or_query.strip().strip('"\'')
        if "youtube.com" in url_or_query or "youtu.be" in url_or_query:
            return self.open_url(url_or_query)
        # Search and let user click first result
        return self.search_youtube(url_or_query)

    def search_google(self, query: str) -> str:
        query = query.strip().strip('"\'')
        url = f"https://www.google.com/search?q={quote_plus(query)}"
        result = self.open_url(url)
        return f"Searched Google for '{query}'. {result}"

    def take_screenshot(self, save_path: str = "") -> str:
        """Take a screenshot of the current screen."""
        try:
            import pyautogui
            save_path = save_path.strip() or "screenshot.png"
            pyautogui.screenshot(save_path)
            return f"Screenshot saved to: {save_path}"
        except Exception as e:
            return f"Failed to take screenshot: {e}"
