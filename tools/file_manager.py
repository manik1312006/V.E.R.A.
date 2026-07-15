"""File manager tool for V.E.R.A. — file operations."""

import os
import shutil
from pathlib import Path
from utils.logger import get_logger

logger = get_logger("vera.tools.files")


class FileManager:
    """Manages files and directories on the system."""

    @staticmethod
    def _get_windows_folder(folder_name: str) -> Path:
        """Helper to intelligently resolve standard folders that might be in OneDrive."""
        onedrive = Path.home() / "OneDrive" / folder_name
        if onedrive.exists():
            return onedrive
        return Path.home() / folder_name

    # Friendly alias → actual folder resolver (lazy, uses real username at runtime)
    _ALIASES: dict = {
        "desktop":   lambda: FileManager._get_windows_folder("Desktop"),
        "home":      lambda: Path.home(),
        "documents": lambda: FileManager._get_windows_folder("Documents"),
        "docs":      lambda: FileManager._get_windows_folder("Documents"),
        "downloads": lambda: Path.home() / "Downloads",
        "pictures":  lambda: FileManager._get_windows_folder("Pictures"),
        "photos":    lambda: FileManager._get_windows_folder("Pictures"),
        "music":     lambda: Path.home() / "Music",
        "videos":    lambda: Path.home() / "Videos",
        "movies":    lambda: Path.home() / "Videos",
    }

    def _resolve_path(self, raw: str) -> Path:
        """Resolve a raw path string into an absolute Path.

        Handles:
        - Friendly aliases: 'desktop', 'documents', 'downloads', etc.
        - Windows %ENVVAR% expansion  (e.g. %USERNAME%, %USERPROFILE%)
        - Unix $VAR / ${VAR} expansion
        - ~ home-dir expansion
        - Relative paths (resolved against cwd)
        """
        raw = raw.strip().strip('"').strip("'")  # strip surrounding quotes too

        # 1. Friendly aliases (case-insensitive exact match)
        if raw.lower() in self._ALIASES:
            return self._ALIASES[raw.lower()]()

        # 2. Expand %VARIABLE% (Windows) and $VAR (Unix)
        expanded = os.path.expandvars(raw)

        # 3. Expand ~
        expanded = os.path.expanduser(expanded)

        return Path(expanded).resolve()

    # ──────────────────────────────────────────────────────────────────────────
    # Dispatch
    # ──────────────────────────────────────────────────────────────────────────

    def execute(self, action: str, parameters: str) -> str:
        """Execute a file management action.

        Args:
            action: The action to perform.
            parameters: Action parameters.

        Returns:
            Result message string.
        """
        handler = {
            "list_files":    self.list_files,
            "copy_file":     self.copy_file,
            "move_file":     self.move_file,
            "delete_file":   self.delete_file,
            "create_folder": self.create_folder,
            "open_file":     self.open_file,
            "read_file":     self.read_file,
            "get_file_info": self.get_file_info,
            "search_files":  self.search_files,
        }.get(action)

        if not handler:
            return f"Unknown action: {action}. Available: {list(self._actions().keys())}"

        return handler(parameters)

    def _actions(self) -> dict:
        return {
            "list_files":    "List files in a directory (params: path or alias like 'desktop')",
            "copy_file":     "Copy a file (params: source:destination)",
            "move_file":     "Move/rename a file (params: source:destination)",
            "delete_file":   "Delete a file or folder (params: path)",
            "create_folder": "Create a folder (params: path)",
            "open_file":     "Open a file with its default app (params: path)",
            "read_file":     "Read file contents (params: path)",
            "get_file_info": "Get file metadata (params: path)",
            "search_files":  "Search files by name (params: name:directory)",
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Actions
    # ──────────────────────────────────────────────────────────────────────────

    def list_files(self, directory: str = "") -> str:
        path = self._resolve_path(directory) if directory.strip() else Path.home()
        try:
            if not path.exists():
                return f"Directory not found: {path}"

            items = []
            for item in sorted(path.iterdir()):
                prefix = "📁" if item.is_dir() else "📄"
                size = ""
                if item.is_file():
                    try:
                        size = f" ({item.stat().st_size:,} bytes)"
                    except OSError:
                        size = ""
                items.append(f"  {prefix} {item.name}{size}")

            if not items:
                return f"Directory is empty: {path}"
            return f"Contents of {path}:\n" + "\n".join(items[:100])
        except Exception as e:
            return f"Failed to list files: {e}"

    def copy_file(self, params: str) -> str:
        try:
            source, dest = params.split(":", 1)
            src_path = self._resolve_path(source)
            dst_path = self._resolve_path(dest)
            shutil.copy2(src_path, dst_path)
            return f"Copied: {src_path} -> {dst_path}"
        except Exception as e:
            return f"Failed to copy file: {e}"

    def move_file(self, params: str) -> str:
        try:
            source, dest = params.split(":", 1)
            src_path = self._resolve_path(source)
            dst_path = self._resolve_path(dest)
            shutil.move(str(src_path), str(dst_path))
            return f"Moved: {src_path} -> {dst_path}"
        except Exception as e:
            return f"Failed to move file: {e}"

    def delete_file(self, file_path: str) -> str:
        path = self._resolve_path(file_path)
        try:
            if path.is_dir():
                shutil.rmtree(path)
                return f"Deleted directory: {path}"
            else:
                path.unlink()
                return f"Deleted file: {path}"
        except Exception as e:
            return f"Failed to delete '{path}': {e}"

    def create_folder(self, folder_path: str) -> str:
        path = self._resolve_path(folder_path)
        try:
            path.mkdir(parents=True, exist_ok=True)
            return f"Created folder: {path}"
        except Exception as e:
            return f"Failed to create folder: {e}"

    def open_file(self, file_path: str) -> str:
        path = self._resolve_path(file_path)
        try:
            import platform
            system = platform.system().lower()
            if system == "windows":
                os.startfile(str(path))
            elif system == "darwin":
                os.system(f"open '{path}'")
            else:
                os.system(f"xdg-open '{path}'")
            return f"Opened: {path}"
        except Exception as e:
            return f"Failed to open file: {e}"

    def read_file(self, file_path: str) -> str:
        path = self._resolve_path(file_path)
        try:
            if not path.exists():
                return f"File not found: {path}"
            content = path.read_text(encoding="utf-8", errors="ignore")
            if len(content) > 20000:
                return content[:20000] + f"\n... (truncated, {len(content)} total chars)"
            return content
        except Exception as e:
            return f"Failed to read file: {e}"

    def get_file_info(self, file_path: str) -> str:
        path = self._resolve_path(file_path)
        try:
            import datetime
            stat = path.stat()
            info = (
                f"File: {path.name}\n"
                f"Path: {path.absolute()}\n"
                f"Size: {stat.st_size:,} bytes\n"
                f"Modified: {datetime.datetime.fromtimestamp(stat.st_mtime)}\n"
                f"Type: {'Directory' if path.is_dir() else 'File'}"
            )
            return info
        except Exception as e:
            return f"Failed to get file info: {e}"

    def search_files(self, params: str) -> str:
        try:
            parts = params.split(":", 1)
            name_pattern = parts[0].strip()
            search_dir = (
                self._resolve_path(parts[1].strip()) if len(parts) > 1 else Path.home()
            )

            matches = []
            for root, dirs, files in os.walk(search_dir):
                # Limit depth to avoid hanging
                depth = str(root)[len(str(search_dir)):].count(os.sep)
                if depth > 3:
                    continue
                for f in files:
                    if name_pattern.lower() in f.lower():
                        matches.append(os.path.join(root, f))
                if len(matches) >= 50:
                    break

            if not matches:
                return f"No files matching '{name_pattern}' found in {search_dir}"
            return f"Found {len(matches)} matches:\n" + "\n".join(matches[:50])
        except Exception as e:
            return f"Failed to search files: {e}"
