#!/usr/bin/env python3

import argparse

from _example_support import print_response
from zadar_webapi import ZadarWebApiClient


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Start or stop a running mode over the Zadar sensor Web API."
    )
    parser.add_argument("--sensor-host", required=True, help="Sensor hostname or IPv4 address.")
    parser.add_argument("--mode", type=int, help="Running mode to start.")
    parser.add_argument(
        "--stop",
        action="store_true",
        help="Stop the current running mode instead of starting one.",
    )
    args = parser.parse_args()

    if not args.stop and args.mode is None:
        parser.error("--mode is required unless --stop is used")

    client = ZadarWebApiClient(args.sensor_host)

    if args.stop:
        print_response("Stop Running Mode", client.stop_running_mode())
    else:
        print_response("Start Running Mode", client.set_running_mode(args.mode))
    print_response("Running Mode", client.get_running_mode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
