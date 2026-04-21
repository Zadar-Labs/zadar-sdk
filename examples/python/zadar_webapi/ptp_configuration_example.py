#!/usr/bin/env python3

import argparse

from _example_support import print_response
from zadar_webapi import ZadarWebApiClient


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect or update PTP synchronization settings over the Zadar sensor Web API."
    )
    parser.add_argument("--sensor-host", required=True, help="Sensor hostname or IPv4 address.")
    parser.add_argument("--ptp-mode", help="PTP mode, for example 1588-E2E or automotive-slave.")
    parser.add_argument("--sync-accuracy", type=int, help="PTP sync accuracy in nanoseconds.")
    parser.add_argument("--trigger-offset", type=int, help="PTP trigger offset.")
    args = parser.parse_args()

    client = ZadarWebApiClient(args.sensor_host)

    if args.ptp_mode is not None:
        print_response("Set PTP Mode", client.set_ptp_mode(args.ptp_mode))
    if args.sync_accuracy is not None:
        print_response(
            "Set PTP Sync Accuracy",
            client.set_ptp_sync_accuracy(args.sync_accuracy),
        )
    if args.trigger_offset is not None:
        print_response(
            "Set PTP Trigger Offset",
            client.set_ptp_trigger_offset(args.trigger_offset),
        )

    print_response("PTP Sync Status", client.get_ptp_sync_status())
    print_response("PTP Mode", client.get_ptp_mode())
    print_response("PTP Sync Accuracy", client.get_ptp_sync_accuracy())
    print_response("PTP Trigger Offset", client.get_ptp_trigger_offset())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
