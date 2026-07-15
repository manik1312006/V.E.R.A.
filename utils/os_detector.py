"""OS detection utilities for V.E.R.A."""

import platform
import enum


class OSType(enum.Enum):
    """Supported operating systems."""
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    UNKNOWN = "unknown"


def detect_os() -> OSType:
    """Detect the current operating system.

    Returns:
        OSType enum value for the current platform.
    """
    system = platform.system().lower()
    if system == "windows":
        return OSType.WINDOWS
    elif system == "linux":
        return OSType.LINUX
    elif system == "darwin":
        return OSType.MACOS
    return OSType.UNKNOWN


def get_current_os() -> str:
    """Get the current OS as a lowercase string.

    Returns:
        String identifier: 'windows', 'linux', 'macos', or 'unknown'.
    """
    return detect_os().value


def get_script_extension() -> str:
    """Get the appropriate script extension for the current OS.

    Returns:
        '.bat' for Windows, '.sh' for Linux/macOS.
    """
    os_type = detect_os()
    if os_type == OSType.WINDOWS:
        return ".bat"
    return ".sh"


def get_scripts_dir_name() -> str:
    """Get the scripts subdirectory name for the current OS.

    Returns:
        Directory name: 'windows', 'linux', or 'macos'.
    """
    return get_current_os()
