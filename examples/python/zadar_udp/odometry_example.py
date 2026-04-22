#!/usr/bin/env python3
"""Print odometry data from received UDP radar frames when available."""

from __future__ import annotations

from _example_support import (
    format_timestamp_ns,
    make_radar_parser,
    print_frame_banner,
    should_report_status,
    should_stop,
)
from zadar_udp import RadarDataListener, RadarStatusCodes


def _print_odometry(radar_frame) -> None:
    if not radar_frame.HasField("odometry"):
        print("Odometry: not present in this frame")
        return

    odometry = radar_frame.odometry
    print(
        "Odometry: "
        f"frame={odometry.frame_num}, stamp='{format_timestamp_ns(odometry.stamp)}', "
        f"euler=({odometry.phi:.3f}, {odometry.psi:.3f}, {odometry.theta:.3f}), "
        f"vel=({odometry.vx:.3f}, {odometry.vy:.3f}, {odometry.vz:.3f}), "
        f"raw_vel=({odometry.raw_vx:.3f}, {odometry.raw_vy:.3f}, {odometry.raw_vz:.3f}), "
        f"omega=({odometry.omega_x:.3f}, {odometry.omega_y:.3f}, {odometry.omega_z:.3f})"
    )


def _status_message(status_code: int) -> str:
    if status_code == int(RadarStatusCodes.IMPROPER_PACKET):
        return "packet parsing or frame reassembly failed"
    if status_code == int(RadarStatusCodes.PROTO_PARSING_ERROR):
        return "protobuf decoding failed"
    return "unknown radar status"


def main() -> int:
    args = make_radar_parser(
        "Receive Zadar UDP radar frames and print odometry data when present."
    ).parse_args()
    listener = RadarDataListener(
        ip=args.bind_address,
        port=args.port,
        rx_buffer_bytes=args.socket_buffer_bytes,
        max_buffered_frames=args.max_buffered_frames,
        frame_timeout_sec=args.frame_timeout_sec,
        socket_timeout_sec=args.socket_timeout_sec,
        generated_python_dir=args.generated_python_dir,
    )

    print(f"Listening for radar UDP frames on udp://{args.bind_address}:{args.port}")
    try:
        processed_frames = 0
        status_counts = {}
        while not should_stop(processed_frames, args.frame_limit):
            out = listener.read_frame()
            if out is None:
                continue
            if out.status_code != RadarStatusCodes.FINE:
                count = status_counts.get(int(out.status_code), 0) + 1
                status_counts[int(out.status_code)] = count
                if should_report_status(count):
                    print(
                        f"Warning: radar status {out.status_code}: "
                        f"{_status_message(out.status_code)} "
                        f"(seen {count} time(s))"
                    )
                continue

            assert out.data is not None
            print_frame_banner(out.data.frame_id, out.data.timestamp)
            _print_odometry(out.data.data_object)
            processed_frames += 1
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        listener.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
