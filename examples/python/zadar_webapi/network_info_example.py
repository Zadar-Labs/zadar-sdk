#!/usr/bin/env python3

import argparse

from _example_support import print_response
from zadar_webapi import ZadarWebApiClient


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect configured and active network output settings over the Zadar sensor Web API."
    )
    parser.add_argument("--sensor-host", required=True, help="Sensor hostname or IPv4 address.")
    args = parser.parse_args()

    client = ZadarWebApiClient(args.sensor_host)

    print_response("Configured Device IP", client.get_configured_device_ip_address())
    print_response("Current Device IP", client.get_current_device_ip_address())
    print_response("Output Destination IP", client.get_output_destination_ip_address())
    print_response("PCL Port", client.get_pcl_port())
    print_response("IMU Port", client.get_imu_port())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
