"""Shared helper utilities for V.E.R.A."""

import os
import yaml
from pathlib import Path


def get_project_root() -> Path:
    """Get the project root directory.

    Returns:
        Path to the V.E.R.A project root.
    """
    # Walk up from this file to find the project root (where vera.py lives)
    current = Path(__file__).resolve().parent
    while current.parent != current:
        if (current / "vera.py").exists():
            return current
        current = current.parent
    # Fallback: assume utils/ is directly under project root
    return Path(__file__).resolve().parent.parent


def load_config(config_path: str = None) -> dict:
    """Load configuration from YAML file.

    Args:
        config_path: Path to config.yaml. If None, looks in project root.

    Returns:
        Configuration dictionary.
    """
    if config_path is None:
        config_path = get_project_root() / "config.yaml"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}\n"
            f"Copy config.example.yaml to config.yaml and fill in your settings."
        )

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config


def ensure_dir(path: str | Path) -> Path:
    """Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path to create.

    Returns:
        Path object for the directory.
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def truncate_text(text: str, max_length: int = 2000) -> str:
    """Truncate text to a maximum length with an ellipsis indicator.

    Args:
        text: Text to truncate.
        max_length: Maximum character length.

    Returns:
        Truncated text string.
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."
