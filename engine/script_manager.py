"""Script manager for V.E.R.A. — discovers, loads, and organizes scripts."""

import os
from pathlib import Path
from typing import Optional
from utils.os_detector import get_current_os, get_script_extension
from utils.logger import get_logger

logger = get_logger("vera.engine")


class ScriptManager:
    """Manages automation scripts across operating systems."""

    def __init__(self, scripts_base_dir: str | Path):
        self.scripts_base_dir = Path(scripts_base_dir)
        self.current_os = get_current_os()
        self.script_extension = get_script_extension()
        self._registry: dict[str, dict] = {}
        self._scan_scripts()

    def _scan_scripts(self) -> None:
        self._registry.clear()
        os_scripts_dir = self.scripts_base_dir / self.current_os
        if os_scripts_dir.exists():
            self._scan_directory(os_scripts_dir, source="os")
        custom_dir = self.scripts_base_dir / "custom"
        if custom_dir.exists():
            self._scan_directory(custom_dir, source="custom")
        logger.info(f"Loaded {len(self._registry)} scripts from registry")

    def _scan_directory(self, directory: Path, source: str = "os") -> None:
        # Only register real script files (.bat, .sh, .cmd, .ps1) — skip .gitkeep etc.
        valid_extensions = {".bat", ".sh", ".cmd", ".ps1"}
        for file in directory.iterdir():
            if file.is_file() and file.suffix.lower() in valid_extensions:
                name = file.stem
                description = self._extract_description(file)
                self._registry[name.lower()] = {
                    "name": name,
                    "path": str(file),
                    "description": description,
                    "source": source,
                    "extension": file.suffix,
                }

    def _extract_description(self, file: Path) -> str:
        try:
            with open(file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    for prefix in ["REM ", "rem ", "# ", "// "]:
                        if line.startswith(prefix):
                            return line[len(prefix):].strip()
                    break
        except Exception:
            pass
        return "No description"

    def get_script(self, name: str) -> Optional[dict]:
        return self._registry.get(name.lower())

    def get_all_scripts(self) -> list[dict]:
        return list(self._registry.values())

    def get_script_list_for_llm(self) -> str:
        if not self._registry:
            return "No scripts available."
        lines = []
        for script in self._registry.values():
            lines.append(f"  - {script['name']}: {script['description']}")
        return "\n".join(lines)

    def script_exists(self, name: str) -> bool:
        return name.lower() in self._registry

    def reload(self) -> None:
        self._scan_scripts()
