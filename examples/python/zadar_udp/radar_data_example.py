#!/usr/bin/env python3
"""Print radar scan metadata and sample radar points from UDP frames."""

from __future__ import annotations

import random

from _example_support import (
    format_timestamp_ns,
    make_radar_parser,
    print_frame_banner,
    should_report_status,
    should_stop,
)
from zadar_udp import RadarDataListener, RadarStatusCodes


def _print_sample_points(points, sample_count: int) -> None:
    print(f"Total Points: {len(points)}")
    if not points:
        return

    sample_points = random.sample(points, sample_count)
    for index, point in enumerate(sample_points, 1):
        print(
            f"  Pt{index}: x={point.x:.3f}, y={point.y:.3f}, z={point.z:.3f}, "
            f"doppler={point.doppler:.3f}, snr={point.snr:.3f}"
        )


def _status_message(status_code: int) -> str:
    if status_code == int(RadarStatusCodes.IMPROPER_PACKET):
        return "packet parsing or frame reassembly failed"
    if status_code == int(RadarStatusCodes.PROTO_PARSING_ERROR):
        return "protobuf decoding failed"
    return "unknown radar status"


def main() -> int:
    parser = make_radar_parser(
        "Receive Zadar UDP radar frames and print scan metadata plus sample points."
    )
    parser.add_argument(
        "--sample-count",
        type=int,
        default=5,
        help="Number of radar points to print from each frame.",
    )
    args = parser.parse_args()
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
            radar_frame = out.data.data_object
            points = list(radar_frame.radar_scan.points)

            print_frame_banner(out.data.frame_id, out.data.timestamp)
            print(
                "Radar Scan: "
                f"seq={radar_frame.radar_scan.header.seq}, "
                f"stamp='{format_timestamp_ns(radar_frame.radar_scan.header.stamp)}', "
                f"frame_id='{radar_frame.radar_scan.header.frame_id}', "
                f"width={radar_frame.radar_scan.width}, "
                f"height={radar_frame.radar_scan.height}, "
                f"is_dense={radar_frame.radar_scan.is_dense}"
            )
            _print_sample_points(points, min(len(points), args.sample_count))
            processed_frames += 1
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        listener.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
