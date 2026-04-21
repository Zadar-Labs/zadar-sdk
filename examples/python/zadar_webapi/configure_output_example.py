#!/usr/bin/env python3

import argparse

from _example_support import print_response
from zadar_webapi import ZadarWebApiClient


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Configure output destination and UDP ports over the Zadar sensor Web API."
    )
    parser.add_argument("--sensor-host", required=True, help="Sensor hostname or IPv4 address.")
    parser.add_argument(
        "--destination-ip",
        required=True,
        help="Destination IPv4 address for sensor UDP output.",
    )
    parser.add_argument("--pcl-port", type=int, default=7777, help="Radar / PCL UDP port.")
    parser.add_argument("--imu-port", type=int, default=36636, help="IMU UDP port.")
    args = parser.parse_args()

    client = ZadarWebApiClient(args.sensor_host)

    print_response(
        "Set Output Destination IP",
        client.set_output_destination_ip_address(args.destination_ip),
    )
    print_response("Set PCL Port", client.set_pcl_port(args.pcl_port))
    print_response("Set IMU Port", client.set_imu_port(args.imu_port))
    print_response("Output Destination IP", client.get_output_destination_ip_address())
    print_response("PCL Port", client.get_pcl_port())
    print_response("IMU Port", client.get_imu_port())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
