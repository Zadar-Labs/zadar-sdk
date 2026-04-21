#!/usr/bin/env python3

import argparse

from _example_support import print_response
from zadar_webapi import ZadarWebApiClient


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Query basic Web API information from a Zadar sensor."
    )
    parser.add_argument("--sensor-host", required=True, help="Sensor hostname or IPv4 address.")
    args = parser.parse_args()

    client = ZadarWebApiClient(args.sensor_host)

    print_response("Heartbeat", client.heartbeat())
    print_response("Sensor Info", client.get_sensor_info())
    print_response("Device Modes", client.get_device_modes())
    print_response("Running Mode", client.get_running_mode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
