#!/usr/bin/env python3

import argparse
from pathlib import Path

from _example_support import print_response
from zadar_webapi import ZadarWebApiClient


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download or print diagnostic information over the Zadar sensor Web API."
    )
    parser.add_argument("--sensor-host", required=True, help="Sensor hostname or IPv4 address.")
    parser.add_argument(
        "--timeout-sec",
        type=float,
        default=10.0,
        help="Timeout for diagnostic generation and download.",
    )
    parser.add_argument(
        "--save-path",
        help="Optional file path where the diagnostic text should be written.",
    )
    args = parser.parse_args()

    client = ZadarWebApiClient(args.sensor_host)
    response = client.get_diagnostics(timeout_sec=args.timeout_sec)
    print_response("Diagnostics", response)

    if response.success and args.save_path and response.text_body:
        save_path = Path(args.save_path)
        save_path.write_text(response.text_body, encoding="utf-8")
        print(f"\nSaved diagnostics to {save_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
