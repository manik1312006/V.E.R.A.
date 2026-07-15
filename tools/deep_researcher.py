"""Deep Researcher tool for V.E.R.A. — automated bulk knowledge extraction.

Strategy:
1. Wikipedia API  — reliable, rich, always works (no scraping needed)
2. ArXiv API     — real academic papers, JSON feed
3. Targeted scraping of known reliable domains (britannica, etc.)
"""

import time
import requests
from bs4 import BeautifulSoup
from utils.logger import get_logger
from pathlib import Path
import re
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
import xml.etree.ElementTree as ET

logger = get_logger("vera.tools.deep_researcher")


class DeepResearcher:
    """Automates multi-source bulk knowledge extraction and saving."""

    def __init__(self, base_dir: str = None):
        if base_dir is None:
            # Default to the 'Knowledge' folder in the V.E.R.A root directory
            base_dir = str(Path(__file__).resolve().parents[2] / "Knowledge")
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def execute(self, action: str, parameters: str) -> str:
        handler = {
            "run_deep_research": self.run_deep_research,
        }.get(action)
        if not handler:
            return f"Unknown action: {action}. Available: {list(self._actions().keys())}"
        return handler(parameters)

    def _actions(self) -> dict:
        return {
            "run_deep_research": "Autonomously build a huge knowledge base on a topic (params: topic)",
        }

    def _slugify(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r'[^a-z0-9]+', '_', text)
        return text.strip('_')[:50]

    def _topic_dir(self, topic: str) -> Path:
        """Return (and create) the topic-specific subfolder inside Knowledge."""
        folder = self.base_dir / topic.strip().title()
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def _save(self, topic_dir: Path, source_slug: str, content: str) -> bool:
        """Save content to a file inside the topic folder, return True on success."""
        if not content or len(content) < 200:
            return False
        filename = f"{source_slug}.md"
        file_path = topic_dir / filename
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"Failed to save {filename}: {e}")
            return False

    # ────────────────────────────────────────────────
    # SOURCE 1: Wikipedia (most reliable)
    # ────────────────────────────────────────────────

    def _get_wikipedia_related(self, topic: str, limit: int = 20) -> list:
        """Return a list of related Wikipedia page titles for the topic."""
        try:
            resp = requests.get(
                "https://en.wikipedia.org/w/api.php",
                params={"action": "query", "format": "json", "list": "search",
                        "srsearch": topic, "srlimit": limit},
                headers=self.headers, timeout=8
            )
            results = resp.json().get("query", {}).get("search", [])
            return [r["title"] for r in results]
        except Exception as e:
            logger.error(f"Wikipedia search failed: {e}")
            return []

    def _fetch_wikipedia_article(self, title: str) -> str:
        """Fetch the full plain text of a Wikipedia article via API."""
        try:
            resp = requests.get(
                "https://en.wikipedia.org/w/api.php",
                params={"action": "query", "format": "json", "prop": "extracts",
                        "explaintext": True, "titles": title, "exlimit": 1},
                headers=self.headers, timeout=10
            )
            pages = resp.json().get("query", {}).get("pages", {})
            for page_id, page in pages.items():
                extract = page.get("extract", "")
                if extract:
                    return f"# {title}\n\nSource: https://en.wikipedia.org/wiki/{urllib.parse.quote(title)}\n\n{extract}"
        except Exception as e:
            logger.error(f"Wikipedia fetch failed for '{title}': {e}")
        return ""

    def _mine_wikipedia(self, topic: str, topic_dir: Path, count: int = 25) -> int:
        """Fetch multiple Wikipedia articles. Returns save count."""
        titles = self._get_wikipedia_related(topic, limit=count)
        logger.info(f"Wikipedia: found {len(titles)} related articles")
        saved = 0
        with ThreadPoolExecutor(max_workers=8) as ex:
            futures = {ex.submit(self._fetch_wikipedia_article, t): t for t in titles}
            for future in as_completed(futures):
                content = future.result()
                title = futures[future]
                title_slug = self._slugify(title)
                if self._save(topic_dir, f"wikipedia_{title_slug}", content):
                    saved += 1
        return saved

    # ────────────────────────────────────────────────
    # SOURCE 2: ArXiv (academic papers)
    # ────────────────────────────────────────────────

    def _mine_arxiv(self, topic: str, topic_dir: Path, count: int = 30) -> int:
        """Fetch paper abstracts + metadata from ArXiv. Returns save count."""
        saved = 0
        try:
            # ArXiv Atom API — free, no key needed
            resp = requests.get(
                "http://export.arxiv.org/api/query",
                params={"search_query": f"all:{topic}", "start": 0, "max_results": count},
                headers=self.headers, timeout=15
            )
            root = ET.fromstring(resp.content)
            ns = {"a": "http://www.w3.org/2005/Atom"}
            entries = root.findall("a:entry", ns)
            logger.info(f"ArXiv: found {len(entries)} papers")

            for entry in entries:
                title_el = entry.find("a:title", ns)
                summary_el = entry.find("a:summary", ns)
                id_el = entry.find("a:id", ns)
                authors = [a.find("a:name", ns).text for a in entry.findall("a:author", ns) if a.find("a:name", ns) is not None]

                if title_el is None or summary_el is None:
                    continue

                title = title_el.text.strip().replace("\n", " ")
                summary = summary_el.text.strip()
                arxiv_url = id_el.text.strip() if id_el is not None else ""
                author_str = ", ".join(authors[:5])

                content = (
                    f"# {title}\n\n"
                    f"**Authors:** {author_str}\n"
                    f"**Source:** {arxiv_url}\n\n"
                    f"## Abstract\n\n{summary}"
                )
                title_slug = self._slugify(title[:40])
                if self._save(topic_dir, f"arxiv_{title_slug}", content):
                    saved += 1

        except Exception as e:
            logger.error(f"ArXiv mining failed: {e}")
        return saved

    # ────────────────────────────────────────────────
    # SOURCE 3: Direct scraping of known reliable domains
    # ────────────────────────────────────────────────

    def _scrape_url(self, url: str) -> str:
        """Fetch and extract clean text from a single URL."""
        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, "html.parser")
            for el in soup(["script", "style", "nav", "header", "footer", "aside", "noscript"]):
                el.decompose()
            lines = [ln.strip() for ln in soup.get_text(separator="\n").splitlines() if ln.strip()]
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"Scrape failed for '{url}': {e}")
            return ""

    def _mine_web(self, topic: str, topic_dir: Path) -> int:
        """Scrape known, reliably accessible web pages. Returns save count."""
        encoded = urllib.parse.quote_plus(topic)
        # Predefined reliable sources that don't block scrapers
        urls = [
            f"https://en.wikipedia.org/wiki/{urllib.parse.quote(topic.replace(' ', '_'))}",
            f"https://www.britannica.com/search?query={encoded}",
            f"https://www.sciencedaily.com/search/?keyword={encoded}",
            f"https://www.nature.com/search?q={encoded}",
            f"https://www.ibm.com/search?lang=en&cc=us&q={encoded}",
        ]
        saved = 0
        for url in urls:
            try:
                text = self._scrape_url(url)
                if text and len(text) > 300:
                    domain = urllib.parse.urlparse(url).netloc.replace("www.", "")
                    domain_slug = self._slugify(domain)
                    content = f"# Source: {url}\n\n{text}"
                    if self._save(topic_dir, f"web_{domain_slug}", content):
                        saved += 1
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"Web mine error for {url}: {e}")
        return saved

    # ────────────────────────────────────────────────
    # MAIN ENTRY POINT
    # ────────────────────────────────────────────────

    def _notify_completion(self, topic: str, total: int) -> None:
        """Fire a desktop notification + beep when research finishes (Cross-Platform)."""
        import platform
        import subprocess
        system = platform.system().lower()

        # 1. Beep
        try:
            if system == "windows":
                import winsound
                winsound.Beep(1000, 300)
                winsound.Beep(1200, 300)
            else:
                print("\a") # ASCII bell for Mac/Linux
        except Exception:
            pass

        # 2. Notification Popup
        title = "V.E.R.A. — Research Complete ✓"
        msg = f'Research on "{topic}" is complete! {total} files saved to {self.base_dir.absolute()}/{topic.strip().title()}'
        
        try:
            if system == "windows":
                ps_script = (
                    f"Add-Type -AssemblyName System.Windows.Forms; "
                    f"[System.Windows.Forms.MessageBox]::Show('{msg}', '{title}', 'OK', 'Information')"
                )
                subprocess.Popen(
                    ["powershell", "-WindowStyle", "Hidden", "-Command", ps_script],
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
            elif system == "darwin": # macOS
                subprocess.Popen(["osascript", "-e", f'display notification "{msg}" with title "{title}"'])
            else: # Linux
                subprocess.Popen(["notify-send", title, msg])
        except Exception as e:
            logger.warning(f"Could not show notification: {e}")

    def run_deep_research(self, topic: str) -> str:
        topic = topic.strip()
        if not topic:
            return "Error: Topic cannot be empty."

        # Create a dedicated folder for this topic
        topic_dir = self._topic_dir(topic)
        logger.info(f"Saving all research to: {topic_dir}")
        logger.info(f"Starting deep research on: '{topic}'")

        wiki_saved = self._mine_wikipedia(topic, topic_dir, count=30)
        logger.info(f"Wikipedia: saved {wiki_saved} articles")

        arxiv_saved = self._mine_arxiv(topic, topic_dir, count=50)
        logger.info(f"ArXiv: saved {arxiv_saved} papers")

        web_saved = self._mine_web(topic, topic_dir)
        logger.info(f"Web: saved {web_saved} pages")

        total = wiki_saved + arxiv_saved + web_saved

        # Notify via desktop popup + beep
        self._notify_completion(topic, total)

        return (
            f"✅ Deep Research Completed!\n"
            f"  Topic: {topic}\n"
            f"  Folder: {topic_dir}\n"
            f"  Wikipedia Articles Saved: {wiki_saved}\n"
            f"  ArXiv Academic Papers Saved: {arxiv_saved}\n"
            f"  Web Pages Saved: {web_saved}\n"
            f"  Total Knowledge Files Created: {total}\n"
            f"All knowledge is searchable via 'search_knowledge'."
        )

