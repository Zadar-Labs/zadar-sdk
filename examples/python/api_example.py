#!/usr/bin/env python3

"""End-to-end SDK example using both the Web API and UDP listener packages."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import sys


UDP_ROOT = Path(__file__).resolve().parents[2]
SDK_PYTHON_DIR = UDP_ROOT / "sdk" / "python"

if str(SDK_PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(SDK_PYTHON_DIR))


from zadar_udp import ImuDataListener, ImuStatusCodes, RadarDataListener, RadarStatusCodes
from zadar_webapi import ApiResponse, ZadarWebApiClient
from zadar_webapi.driver_control import require_success, resolve_managed_network_settings


def format_timestamp(timestamp: tuple[int, int]) -> str:
    timestamp_sec, timestamp_nsec = timestamp
    timestamp_sec += timestamp_nsec // 1_000_000_000
    timestamp_nsec %= 1_000_000_000
    wall_time = datetime.fromtimestamp(timestamp_sec)
    milliseconds = timestamp_nsec // 1_000_000
    return f"{wall_time.strftime('%Y-%d-%m %H:%M:%S')}.{milliseconds:03d}"


def print_response(title: str, response: ApiResponse) -> None:
    print(f"\n=== {title} ===")
    print(f"status_code={response.status_code} success={response.success}")
    if response.error:
        print(f"error={response.error}")
    elif response.json_body is not None:
        print(json.dumps(response.json_body, indent=2, sort_keys=True))
    elif response.text_body:
        print(response.text_body)


def read_next_radar_frame(listener: RadarDataListener):
    while True:
        output = listener.read_frame()
        if output is None:
            raise TimeoutError("Timed out waiting for a radar frame.")
        if output.status_code == RadarStatusCodes.FINE and output.data is not None:
            return output.data
        print(f"Skipping radar frame with status_code={output.status_code}")


def read_next_imu_packet(listener: ImuDataListener):
    while True:
        output = listener.read_packet()
        if output is None:
            raise TimeoutError("Timed out waiting for an IMU packet.")
        if output.status_code == ImuStatusCodes.FINE and output.data is not None:
            return output.data
        print(f"Skipping IMU packet with status_code={output.status_code}")


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "End-to-end SDK example that configures sensor output over the Web API "
            "and then receives radar and IMU data over UDP."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--sensor-host", required=True, help="Sensor hostname or IPv4 address.")
    parser.add_argument(
        "--host-ip",
        default="",
        help="Host IP address to program as the UDP destination. Leave empty to auto-detect.",
    )
    parser.add_argument(
        "--bind-address",
        default="0.0.0.0",
        help="Local interface for the UDP listeners. Use 0.0.0.0 to auto-resolve.",
    )
    parser.add_argument("--pcl-port", type=int, default=7777, help="Radar UDP port.")
    parser.add_argument("--imu-port", type=int, default=36636, help="IMU UDP port.")
    parser.add_argument(
        "--running-mode",
        type=int,
        default=None,
        help="Running mode to start before receiving UDP data. Omit to leave the current mode unchanged.",
    )
    parser.add_argument(
        "--radar-frames",
        type=int,
        default=3,
        help="Number of completed radar frames to print.",
    )
    parser.add_argument(
        "--imu-packets",
        type=int,
        default=3,
        help="Number of decoded IMU packets to print.",
    )
    parser.add_argument(
        "--socket-timeout-sec",
        type=float,
        default=5.0,
        help="Timeout for each UDP read.",
    )
    parser.add_argument(
        "--set-device-ip",
        default="",
        help="Optional static device IP override to apply before the UDP flow.",
    )
    parser.add_argument(
        "--ptp-mode",
        choices=("1588-E2E", "automotive-slave"),
        default="",
        help="Optional PTP mode update to apply before the UDP flow.",
    )
    parser.add_argument(
        "--ptp-sync-accuracy",
        type=int,
        default=None,
        help="Optional PTP sync accuracy update in nanoseconds.",
    )
    parser.add_argument(
        "--ptp-trigger-offset",
        type=int,
        default=None,
        help="Optional PTP trigger offset update in nanoseconds.",
    )
    parser.add_argument(
        "--stop-at-end",
        action="store_true",
        help="Stop the running mode before exiting.",
    )
    return parser


def main() -> int:
    args = make_parser().parse_args()

    settings = resolve_managed_network_settings(
        sensor_hostname=args.sensor_host,
        host_ip=args.host_ip,
        udp_bind_address=args.bind_address,
        legacy_bind_address="",
    )
    print("Resolved network settings:")
    print(f"  destination_ip={settings.destination_ip}")
    print(f"  bind_address={settings.bind_address}")
    print(f"  pcl_port={args.pcl_port}")
    print(f"  imu_port={args.imu_port}")

    client = ZadarWebApiClient(args.sensor_host)
    radar_listener = RadarDataListener(
        ip=settings.bind_address,
        port=args.pcl_port,
        socket_timeout_sec=args.socket_timeout_sec,
    )
    imu_listener = ImuDataListener(
        ip=settings.bind_address,
        port=args.imu_port,
        socket_timeout_sec=args.socket_timeout_sec,
    )

    try:
        print("\nOpening UDP listeners...")
        radar_listener.open()
        imu_listener.open()

        print_response("Sensor Info", client.get_sensor_info())
        print_response("Device Modes", client.get_device_modes())
        print_response("Running Mode", client.get_running_mode())
        print_response("Configured Device IP", client.get_configured_device_ip_address())
        print_response("Current Device IP", client.get_current_device_ip_address())
        print_response("Output Destination IP", client.get_output_destination_ip_address())
        print_response("Configured PCL Port", client.get_pcl_port())
        print_response("Configured IMU Port", client.get_imu_port())
        print_response("Startup Mode", client.get_startup_mode())
        print_response("PTP Sync Status", client.get_ptp_sync_status())
        print_response("PTP Mode", client.get_ptp_mode())
        print_response("PTP Sync Accuracy", client.get_ptp_sync_accuracy())
        print_response("PTP Trigger Offset", client.get_ptp_trigger_offset())

        if args.set_device_ip:
            response = client.set_configured_device_ip_address_static(args.set_device_ip)
            print_response("Set Configured Device IP", response)
            require_success("Setting configured device IP", response)

        if args.ptp_mode:
            response = client.set_ptp_mode(args.ptp_mode)
            print_response("Set PTP Mode", response)
            require_success("Setting PTP mode", response)

        if args.ptp_sync_accuracy is not None:
            response = client.set_ptp_sync_accuracy(args.ptp_sync_accuracy)
            print_response("Set PTP Sync Accuracy", response)
            require_success("Setting PTP sync accuracy", response)

        if args.ptp_trigger_offset is not None:
            response = client.set_ptp_trigger_offset(args.ptp_trigger_offset)
            print_response("Set PTP Trigger Offset", response)
            require_success("Setting PTP trigger offset", response)

        print("\nConfiguring output destination and UDP ports...")
        response = client.set_output_destination_ip_address(settings.destination_ip)
        print_response("Set Output Destination IP", response)
        require_success("Configuring output destination IP", response)

        response = client.set_pcl_port(args.pcl_port)
        print_response("Set PCL Port", response)
        require_success("Configuring radar data port", response)

        response = client.set_imu_port(args.imu_port)
        print_response("Set IMU Port", response)
        require_success("Configuring IMU port", response)

        if args.running_mode is not None:
            response = client.set_running_mode(args.running_mode)
            print_response(f"Start Running Mode {args.running_mode}", response)
            require_success(f"Starting running mode {args.running_mode}", response)
        else:
            print(
                "\nNo --running-mode was provided. The example will expect the sensor "
                "to already be streaming."
            )

        print_response("Verified Output Destination IP", client.get_output_destination_ip_address())
        print_response("Verified PCL Port", client.get_pcl_port())
        print_response("Verified IMU Port", client.get_imu_port())
        print_response("Verified Running Mode", client.get_running_mode())

        print("\nReading radar frames...")
        for _ in range(args.radar_frames):
            payload = read_next_radar_frame(radar_listener)
            frame = payload.data_object
            print(f"\n=== Radar Frame #{payload.frame_id} ===")
            print(f"Timestamp: {format_timestamp(payload.timestamp)}")
            print(f"Points: {len(frame.radar_scan.points)}")
            print(f"Clusters: {len(frame.clusters)}")
            print(f"Tracks: {len(frame.tracks)}")
            print(f"Odometry Present: {frame.HasField('odometry')}")

        print("\nReading IMU packets...")
        for _ in range(args.imu_packets):
            payload = read_next_imu_packet(imu_listener)
            packet = payload.data_object
            print(f"\n=== IMU Packet #{payload.frame_id} ===")
            print(f"Timestamp: {format_timestamp(payload.timestamp)}")
            print(
                "Accel: "
                f"{packet.acceleration_x:.2f}, "
                f"{packet.acceleration_y:.2f}, "
                f"{packet.acceleration_z:.2f}"
            )
            print(
                "Gyro:  "
                f"{packet.angular_rate_x:.2f}, "
                f"{packet.angular_rate_y:.2f}, "
                f"{packet.angular_rate_z:.2f}"
            )

        if args.stop_at_end:
            response = client.stop_running_mode()
            print_response("Stop Running Mode", response)
            require_success("Stopping running mode", response)

    finally:
        radar_listener.close()
        imu_listener.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
