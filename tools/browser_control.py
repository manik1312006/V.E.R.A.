"""Browser control tool for V.E.R.A. — Playwright-based web automation."""

from utils.logger import get_logger

logger = get_logger("vera.tools.browser")


class BrowserController:
    """Controls web browsers using Playwright for complex web tasks."""

    def __init__(self):
        self._browser = None
        self._playwright = None

    def execute(self, action: str, parameters: str) -> str:
        """Execute a browser control action.

        Args:
            action: The action to perform.
            parameters: Action parameters.

        Returns:
            Result message string.
        """
        handler = {
            "open_url": self.open_url,
            "search_youtube": self.search_youtube,
            "play_youtube": self.play_youtube,
            "search_google": self.search_google,
            "take_screenshot": self.take_screenshot,
            "get_page_title": self.get_page_title,
            "fill_form": self.fill_form,
            "click_element": self.click_element,
        }.get(action)

        if not handler:
            return f"Unknown action: {action}. Available: {list(self._actions().keys())}"

        return handler(parameters)

    def _actions(self) -> dict:
        return {
            "open_url": "Open a URL in browser (params: url)",
            "search_youtube": "Search YouTube (params: query)",
            "play_youtube": "Play YouTube video (params: url or query)",
            "search_google": "Search Google (params: query)",
            "take_screenshot": "Screenshot current page (params: save_path)",
            "get_page_title": "Get current page title (params: none)",
            "fill_form": "Fill a form field (params: selector:value)",
            "click_element": "Click an element (params: CSS selector)",
        }

    def _launch_browser(self):
        """Launch a Playwright browser (lazy init)."""
        if self._browser is None:
            try:
                from playwright.sync_api import sync_playwright
                pw = sync_playwright().start()
                self._playwright = pw
                self._browser = pw.chromium.launch(headless=False)
            except ImportError:
                raise ImportError(
                    "Playwright not installed. Run: pip install playwright && playwright install"
                )
        return self._browser

    def open_url(self, url: str) -> str:
        try:
            browser = self._launch_browser()
            page = browser.new_page()
            page.goto(url)
            title = page.title()
            return f"Opened: {title} ({url})"
        except Exception as e:
            return f"Failed to open URL: {e}"

    def search_youtube(self, query: str) -> str:
        url = f"https://www.youtube.com/results?search_query={query}"
        return self.open_url(url)

    def play_youtube(self, url_or_query: str) -> str:
        if "youtube.com" in url_or_query or "youtu.be" in url_or_query:
            return self.open_url(url_or_query)
        else:
            return self.search_youtube(url_or_query)

    def search_google(self, query: str) -> str:
        url = f"https://www.google.com/search?q={query}"
        return self.open_url(url)

    def take_screenshot(self, save_path: str = "browser_screenshot.png") -> str:
        try:
            browser = self._launch_browser()
            pages = browser.contexts[0].pages if browser.contexts else []
            if pages:
                pages[-1].screenshot(path=save_path)
                return f"Screenshot saved: {save_path}"
            return "No browser page open to screenshot."
        except Exception as e:
            return f"Failed to take screenshot: {e}"

    def get_page_title(self, _: str = "") -> str:
        try:
            browser = self._launch_browser()
            pages = browser.contexts[0].pages if browser.contexts else []
            if pages:
                title = pages[-1].title()
                return f"Page title: {title}"
            return "No browser page open."
        except Exception as e:
            return f"Failed to get page title: {e}"

    def fill_form(self, params: str) -> str:
        try:
            selector, value = params.split(":", 1)
            browser = self._launch_browser()
            pages = browser.contexts[0].pages if browser.contexts else []
            if pages:
                pages[-1].fill(selector, value)
                return f"Filled '{selector}' with value."
            return "No browser page open."
        except Exception as e:
            return f"Failed to fill form: {e}"

    def click_element(self, selector: str) -> str:
        try:
            browser = self._launch_browser()
            pages = browser.contexts[0].pages if browser.contexts else []
            if pages:
                pages[-1].click(selector)
                return f"Clicked element: {selector}"
            return "No browser page open."
        except Exception as e:
            return f"Failed to click element: {e}"

    def cleanup(self):
        """Close the browser and Playwright connection."""
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
        self._browser = None
        self._playwright = None
