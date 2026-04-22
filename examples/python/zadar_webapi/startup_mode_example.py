#!/usr/bin/env python3

import argparse

from _example_support import print_response
from zadar_webapi import ZadarWebApiClient


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect or update the startup mode over the Zadar sensor Web API."
    )
    parser.add_argument("--sensor-host", required=True, help="Sensor hostname or IPv4 address.")
    parser.add_argument("--mode", type=int, help="Startup mode to configure.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Remove the startup-mode override and return to the default startup behavior.",
    )
    args = parser.parse_args()

    if args.reset and args.mode is not None:
        parser.error("--mode and --reset cannot be used together")

    client = ZadarWebApiClient(args.sensor_host)

    if args.reset:
        print_response("Reset Startup Mode", client.reset_startup_mode())
    elif args.mode is not None:
        print_response("Set Startup Mode", client.set_startup_mode(args.mode))

    print_response("Startup Mode", client.get_startup_mode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
