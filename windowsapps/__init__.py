"""
WindowsApps: Python module for managing Windows applications.

Provides functions to list installed applications, find apps by name or ID,
and open apps. Uses a caching mechanism to improve performance when listing apps.

Originally by @StealtherThreat - https://github.com/StealtherThreat/windowsapps
Updated by @Aquarion - https://github.com/aquarion/windowsapps

"""

from json import loads
from subprocess import run
from os import startfile
from typing import Dict, Tuple, Optional
import time


class WindowsAppsCache:
    """Thread-safe cache for Windows applications with TTL support."""

    def __init__(self, ttl_seconds: int = 300):  # 5 minute default TTL
        self._cache: Optional[Dict[str, str]] = None
        self._cache_time: float = 0
        self._ttl = ttl_seconds

    def _is_cache_valid(self) -> bool:
        """Check if the current cache is still valid based on TTL."""
        return self._cache is not None and time.time() - self._cache_time < self._ttl

    def _fetch_apps(self) -> Dict[str, str]:
        """Fetch fresh app data from PowerShell."""
        cmd = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-Command",
            "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Get-StartApps | ConvertTo-Json",
        ]
        result = run(cmd, capture_output=True, encoding="utf-8", errors="replace")
        apps_data = loads(result.stdout)
        return {app["Name"]: app["AppID"] for app in apps_data}

    def get_apps(self, force_refresh: bool = False) -> Dict[str, str]:
        """Get all installed apps, using cache if valid."""
        if force_refresh or not self._is_cache_valid():
            self._cache = self._fetch_apps()
            self._cache_time = time.time()
        return self._cache.copy()  # Return copy to prevent external modification

    def clear_cache(self) -> None:
        """Manually clear the cache."""
        self._cache = None
        self._cache_time = 0


# Global cache instance
_apps_cache = WindowsAppsCache()


def get_apps(force_refresh: bool = False) -> Dict[str, str]:
    """
    Get all installed Windows applications.

    Args:
        force_refresh: If True, bypass cache and fetch fresh data

    Returns:
        Dictionary mapping application names to their App IDs
    """
    return _apps_cache.get_apps(force_refresh=force_refresh)


def find_app(app_name: str) -> Tuple[str, str]:
    """
    Find an application by name (case-insensitive partial match).

    Args:
        app_name: Name or partial name of the application to find

    Returns:
        Tuple of (full_app_name, app_id)

    Raises:
        ValueError: If no matching application is found
    """
    apps = get_apps()
    app_name_upper = app_name.upper()

    # Sort by length to prefer shorter (more specific) matches
    for name in sorted(apps.keys(), key=len):
        if app_name_upper in name.upper():
            return name, apps[name]

    raise ValueError(f"Application '{app_name}' not found!")


def find_app_by_id(app_id: str) -> Tuple[str, str]:
    """
    Find an application by App ID (case-insensitive partial match).

    Args:
        app_id: App ID or partial App ID to search for

    Returns:
        Tuple of (app_name, full_app_id)

    Raises:
        ValueError: If no matching application is found
    """
    apps = get_apps()
    app_id_upper = app_id.upper()

    # Sort by App ID length to prefer shorter (more specific) matches
    for name, aid in sorted(apps.items(), key=lambda x: len(x[1])):
        if app_id_upper in aid.upper():
            return name, aid

    raise ValueError(f"Application with ID '{app_id}' not found!")


def open_app(app_name: str) -> None:
    """
    Open an application by name.

    Args:
        app_name: Name or partial name of the application to open

    Raises:
        ValueError: If application is not found
    """
    _, app_id = find_app(app_name)
    startfile(f"shell:AppsFolder\\{app_id}")


def refresh_cache() -> None:
    """Manually refresh the application cache."""
    _apps_cache.clear_cache()


# Backwards compatibility aliases
def clear_cache() -> None:
    """Clear the application cache (alias for refresh_cache)."""
    refresh_cache()


if __name__ == "__main__":
    try:
        result = find_app("stealth pc monitor")
        print(f"Found: {result}")
    except ValueError as e:
        print(f"Error: {e}")
