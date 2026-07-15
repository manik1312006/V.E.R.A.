"""V.E.R.A. Utils - Shared utilities."""

from .os_detector import detect_os, get_script_extension, get_current_os
from .logger import setup_logger, get_logger
from .helpers import load_config, get_project_root

__all__ = [
    "detect_os",
    "get_script_extension",
    "get_current_os",
    "setup_logger",
    "get_logger",
    "load_config",
    "get_project_root",
]
