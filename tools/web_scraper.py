"""Web Scraper tool for V.E.R.A. — reading and extracting text from webpages."""

import requests
from bs4 import BeautifulSoup
from pathlib import Path
from utils.logger import get_logger
from utils.helpers import truncate_text

logger = get_logger("vera.tools.scraper")


class WebScraper:
    """Fetches and extracts clean text from web pages."""

    def execute(self, action: str, parameters: str) -> str:
        """Execute a web scraping action.

        Args:
            action: The action to perform (e.g. 'scrape_url').
            parameters: The URL to scrape.

        Returns:
            Extracted text from the webpage.
        """
        handler = {
            "scrape_url": self.scrape_url,
        }.get(action)

        if not handler:
            return f"Unknown action: {action}. Available: {list(self._actions().keys())}"

        return handler(parameters)

    def _actions(self) -> dict:
        return {
            "scrape_url": "Read and extract text from a webpage (params: url)",
        }

    def scrape_url(self, url: str) -> str:
        """Fetch a webpage or local HTML file and extract clean readable text."""
        url = url.strip()
        
        # Check if it's a local file first
        local_path = Path(url.replace("file://", ""))
        if local_path.exists() and local_path.is_file():
            try:
                html = local_path.read_text(encoding="utf-8", errors="ignore")
                return self._extract_text(html, str(local_path))
            except Exception as e:
                return f"Failed to read local file: {e}"

        if not url.startswith("http"):
            url = "https://" + url

        try:
            # Setup headers to look like a standard browser
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/115.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "en-US,en;q=0.9",
            }
            
            logger.info(f"Scraping URL: {url}")
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                return self._extract_text(response.text, url)
            else:
                return f"Failed to fetch {url}: HTTP {response.status_code}"

        except Exception as e:
            return f"Failed to fetch {url}: {e}"

    def _extract_text(self, html_content: str, source: str) -> str:
        """Helper to extract text from HTML using BeautifulSoup."""
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Remove scripts, styles, header, footer, nav
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.extract()

            # Get text
            text = soup.get_text(separator="\n", strip=True)

            # Clean up empty lines
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            clean_text = "\n".join(lines)

            # Use truncate_text helper (returns ~8000 words max by default)
            return f"Source: {source}\n\n{truncate_text(clean_text)}"

        except Exception as e:
            return f"Failed to extract text: {e}"
