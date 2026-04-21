"""Shared helpers for UDP Python examples."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import sys
from typing import Tuple


UDP_ROOT = Path(__file__).resolve().parents[3]
SDK_PYTHON_DIR = UDP_ROOT / "sdk" / "python"
GENERATED_PYTHON_DIR = UDP_ROOT / "generated" / "python"

if str(SDK_PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(SDK_PYTHON_DIR))


def make_radar_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--bind-address",
        default="0.0.0.0",
        help="Local interface to bind for incoming radar UDP traffic.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7777,
        help="Radar UDP port.",
    )
    parser.add_argument(
        "--socket-buffer-bytes",
        type=int,
        default=64 * 1024 * 1024,
        help="Receive socket buffer size in bytes.",
    )
    parser.add_argument(
        "--frame-timeout-sec",
        type=float,
        default=1.0,
        help="Reassembly timeout for incomplete radar frames.",
    )
    parser.add_argument(
        "--socket-timeout-sec",
        type=float,
        default=None,
        help="Optional socket read timeout in seconds.",
    )
    parser.add_argument(
        "--max-buffered-frames",
        type=int,
        default=128,
        help="Maximum number of incomplete radar frames to retain.",
    )
    parser.add_argument(
        "--frame-limit",
        type=int,
        default=0,
        help="Stop after this many completed radar frames. Use 0 to run continuously.",
    )
    parser.add_argument(
        "--generated-python-dir",
        default=str(GENERATED_PYTHON_DIR),
        help="Directory containing generated ZadarFrame_pb2.py.",
    )
    return parser


def make_imu_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--bind-address",
        default="0.0.0.0",
        help="Local interface to bind for incoming IMU UDP traffic.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=36636,
        help="IMU UDP port.",
    )
    parser.add_argument(
        "--socket-buffer-bytes",
        type=int,
        default=4 * 1024 * 1024,
        help="Receive socket buffer size in bytes.",
    )
    parser.add_argument(
        "--socket-timeout-sec",
        type=float,
        default=None,
        help="Optional socket read timeout in seconds.",
    )
    parser.add_argument(
        "--packet-limit",
        type=int,
        default=0,
        help="Stop after this many decoded IMU packets. Use 0 to run continuously.",
    )
    return parser


def format_timestamp(timestamp: Tuple[int, int]) -> str:
    timestamp_sec, timestamp_nsec = timestamp
    timestamp_sec += timestamp_nsec // 1_000_000_000
    timestamp_nsec %= 1_000_000_000
    wall_time = datetime.fromtimestamp(timestamp_sec)
    milliseconds = timestamp_nsec // 1_000_000
    return f"{wall_time.strftime('%Y-%d-%m %H:%M:%S')}.{milliseconds:03d}"


def format_timestamp_ns(timestamp_ns: int) -> str:
    if timestamp_ns <= 0:
        return "0"
    return format_timestamp(divmod(timestamp_ns, 1_000_000_000))


def print_frame_banner(frame_id: int, timestamp: Tuple[int, int]) -> None:
    print(f"\n=== Frame #{frame_id} ===")
    print(f"Timestamp: {format_timestamp(timestamp)}")


def should_stop(processed_count: int, limit: int) -> bool:
    return limit > 0 and processed_count >= limit


def should_report_status(occurrences: int) -> bool:
    return occurrences <= 5 or occurrences % 100 == 0
