"""Helpers for locating the shared UDP Python SDK from the ROS 2 package."""

from __future__ import annotations

import os
from pathlib import Path
import sys
from typing import Optional


def _existing_udp_root(candidate: Path) -> Optional[Path]:
    sdk_dir = candidate / "sdk" / "python" / "zadar_udp"
    generated_dir = candidate / "generated" / "python"
    webapi_dir = candidate / "sdk" / "python" / "zadar_webapi"
    if sdk_dir.is_dir() and generated_dir.is_dir() and webapi_dir.is_dir():
        return candidate
    return None


def find_udp_package_root() -> Optional[Path]:
    env_override = os.environ.get("ZADAR_UDP_PACKAGE_ROOT")
    if env_override:
        found = _existing_udp_root(Path(env_override).expanduser().resolve())
        if found is not None:
            return found

    module_path = Path(__file__).resolve()
    for candidate in module_path.parents:
        found = _existing_udp_root(candidate)
        if found is not None:
            return found

    try:
        from ament_index_python.packages import get_package_share_directory

        share_dir = Path(get_package_share_directory("zadar_udp_driver_py")).resolve()
        for candidate in share_dir.parents:
            found = _existing_udp_root(candidate)
            if found is not None:
                return found
    except Exception:
        pass

    return None


def ensure_sdk_on_path() -> Path:
    udp_root = find_udp_package_root()
    if udp_root is None:
        raise RuntimeError(
            "Unable to locate the Zadar UDP SDK. Set ZADAR_UDP_PACKAGE_ROOT to "
            "the UDP package root if it is not in the expected layout."
        )

    sdk_python_dir = udp_root / "sdk" / "python"
    if str(sdk_python_dir) not in sys.path:
        sys.path.insert(0, str(sdk_python_dir))
    return udp_root


def default_generated_python_dir() -> Path:
    udp_root = ensure_sdk_on_path()
    return udp_root / "generated" / "python"
