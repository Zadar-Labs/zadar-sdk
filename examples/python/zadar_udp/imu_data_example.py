#!/usr/bin/env python3
"""Print IMU packet summaries from the Zadar UDP IMU stream."""

from __future__ import annotations

from _example_support import (
    format_timestamp,
    make_imu_parser,
    should_report_status,
    should_stop,
)
from zadar_udp import ImuDataListener, ImuStatusCodes


def _status_message(status_code: int) -> str:
    if status_code == int(ImuStatusCodes.IMPROPER_PACKET):
        return "packet size or packet layout did not match the expected IMU format"
    if status_code == int(ImuStatusCodes.IMPROPER_CRC):
        return "packet CRC validation failed"
    return "unknown IMU status"


def main() -> int:
    args = make_imu_parser(
        "Receive Zadar UDP IMU packets and print acceleration and gyro data."
    ).parse_args()
    listener = ImuDataListener(
        ip=args.bind_address,
        port=args.port,
        rx_buffer_bytes=args.socket_buffer_bytes,
        socket_timeout_sec=args.socket_timeout_sec,
    )

    print(f"Listening for IMU UDP packets on udp://{args.bind_address}:{args.port}")
    try:
        processed_packets = 0
        status_counts = {}
        while not should_stop(processed_packets, args.packet_limit):
            out = listener.read_packet()
            if out is None:
                continue
            if out.status_code != ImuStatusCodes.FINE:
                count = status_counts.get(int(out.status_code), 0) + 1
                status_counts[int(out.status_code)] = count
                if should_report_status(count):
                    print(
                        f"Warning: IMU status {out.status_code}: "
                        f"{_status_message(out.status_code)} "
                        f"(seen {count} time(s))"
                    )
                continue

            assert out.data is not None
            packet = out.data.data_object
            print(f"\nIMU Packet #{processed_packets}")
            print(f"Sensor Frame ID: {out.data.frame_id}")
            print(f"Timestamp: {format_timestamp(out.data.timestamp)}")
            print(
                f"Accel: {packet.acceleration_x:.2f}, "
                f"{packet.acceleration_y:.2f}, "
                f"{packet.acceleration_z:.2f}"
            )
            print(
                f"Gyro:  {packet.angular_rate_x:.2f}, "
                f"{packet.angular_rate_y:.2f}, "
                f"{packet.angular_rate_z:.2f}"
            )
            processed_packets += 1
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        listener.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
