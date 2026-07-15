"""Network tools for V.E.R.A. — web search and diagnostics."""

import subprocess
import platform
import urllib.request
import json
from utils.logger import get_logger

logger = get_logger("vera.tools.network")


class NetworkTools:
    """Network diagnostics and web search capabilities."""

    def execute(self, action: str, parameters: str) -> str:
        """Execute a network action.

        Args:
            action: The action to perform.
            parameters: Action parameters.

        Returns:
            Result message string.
        """
        handler = {
            "ping": self.ping,
            "check_internet": self.check_internet,
            "search_web": self.search_web,
            "download_file": self.download_file,
            "get_ip": self.get_ip,
            "dns_lookup": self.dns_lookup,
            "check_port": self.check_port,
        }.get(action)

        if not handler:
            return f"Unknown action: {action}. Available: {list(self._actions().keys())}"

        return handler(parameters)

    def _actions(self) -> dict:
        return {
            "ping": "Ping a host (params: hostname)",
            "check_internet": "Check internet connectivity (params: none)",
            "search_web": "Search the web using DuckDuckGo (params: query)",
            "download_file": "Download a file (params: url:save_path)",
            "get_ip": "Get public IP address (params: none)",
            "dns_lookup": "DNS lookup (params: hostname)",
            "check_port": "Check if a port is open (params: host:port)",
        }

    def ping(self, host: str) -> str:
        host = host.strip()
        try:
            system = platform.system().lower()
            param = "-n" if system == "windows" else "-c"
            count = "4"
            result = subprocess.run(
                ["ping", param, count, host],
                capture_output=True, text=True, timeout=15
            )
            return result.stdout.strip() or f"Ping to {host} completed."
        except subprocess.TimeoutExpired:
            return f"Ping to {host} timed out."
        except Exception as e:
            return f"Ping failed: {e}"

    def check_internet(self, _: str) -> str:
        try:
            urllib.request.urlopen("https://duckduckgo.com", timeout=5)
            return "Internet connection: OK"
        except Exception:
            try:
                urllib.request.urlopen("https://google.com", timeout=5)
                return "Internet connection: OK"
            except Exception:
                return "Internet connection: FAILED"

    def search_web(self, query: str) -> str:
        try:
            import requests
            from bs4 import BeautifulSoup
            
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"}
            url = "https://html.duckduckgo.com/html/"
            data = {"q": query}
            
            response = requests.post(url, headers=headers, data=data, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "html.parser")
            results = []
            
            for result in soup.find_all("div", class_="result"):
                title_elem = result.find("h2", class_="result__title")
                snippet_elem = result.find("a", class_="result__snippet")
                url_elem = result.find("a", class_="result__url")
                
                if title_elem and url_elem:
                    title = title_elem.get_text(strip=True)
                    link = url_elem.get("href", "")
                    # DDG often redirects, the URL text itself is usually correct, or the href starts with //duckduckgo.com/l/?uddg=
                    if link.startswith("//duckduckgo.com/l/?uddg="):
                        import urllib.parse
                        parsed = urllib.parse.parse_qs(urllib.parse.urlparse(link).query)
                        if 'uddg' in parsed:
                            link = parsed['uddg'][0]
                    
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    results.append(f"Title: {title}\nURL: {link}\nSnippet: {snippet}\n")
                    
                if len(results) >= 8:
                    break

            if results:
                return "Search results:\n\n" + "\n".join(results)
            return f"Search completed but no results extracted. Try another query."
        except Exception as e:
            return f"Web search failed: {e}"

    def download_file(self, params: str) -> str:
        try:
            parts = params.split(":", 1)
            url = parts[0].strip()
            save_path = parts[1].strip() if len(parts) > 1 else url.split("/")[-1]

            urllib.request.urlretrieve(url, save_path)
            size = __import__("os").path.getsize(save_path)
            return f"Downloaded: {save_path} ({size:,} bytes)"
        except Exception as e:
            return f"Download failed: {e}"

    def get_ip(self, _: str) -> str:
        try:
            req = urllib.request.Request(
                "https://api.ipify.org?format=json",
                headers={"User-Agent": "V.E.R.A./1.0"},
            )
            response = urllib.request.urlopen(req, timeout=10)
            data = json.loads(response.read().decode())
            return f"Public IP: {data.get('ip', 'unknown')}"
        except Exception as e:
            return f"Failed to get IP: {e}"

    def dns_lookup(self, hostname: str) -> str:
        try:
            import socket
            ips = socket.gethostbyname_ex(hostname)
            return f"DNS lookup for {hostname}:\n  Aliases: {ips[1]}\n  Addresses: {ips[2]}"
        except Exception as e:
            return f"DNS lookup failed: {e}"

    def check_port(self, params: str) -> str:
        try:
            parts = params.split(":")
            host = parts[0].strip()
            port = int(parts[1].strip()) if len(parts) > 1 else 80
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                return f"Port {port} on {host} is OPEN"
            return f"Port {port} on {host} is CLOSED"
        except Exception as e:
            return f"Port check failed: {e}"
