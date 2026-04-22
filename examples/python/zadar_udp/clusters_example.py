#!/usr/bin/env python3
"""Print sample cluster data from received UDP radar frames."""

from __future__ import annotations

import random

from _example_support import (
    make_radar_parser,
    print_frame_banner,
    should_report_status,
    should_stop,
)
from zadar_udp import RadarDataListener, RadarStatusCodes


def _print_sample_clusters(clusters, sample_count: int) -> None:
    print(f"Total Clusters: {len(clusters)}")
    if not clusters:
        return

    sample_clusters = random.sample(clusters, sample_count)
    for index, cluster in enumerate(sample_clusters, 1):
        print(
            f"  Cluster{index}: id={cluster.cluster_id}, "
            f"pos=({cluster.x:.3f}, {cluster.y:.3f}, {cluster.z:.3f}), "
            f"doppler={cluster.doppler:.3f}, points={cluster.num_points}, "
            f"static={cluster.is_static}, vertices={len(cluster.vertices)}"
        )


def _status_message(status_code: int) -> str:
    if status_code == int(RadarStatusCodes.IMPROPER_PACKET):
        return "packet parsing or frame reassembly failed"
    if status_code == int(RadarStatusCodes.PROTO_PARSING_ERROR):
        return "protobuf decoding failed"
    return "unknown radar status"


def main() -> int:
    parser = make_radar_parser(
        "Receive Zadar UDP radar frames and print sample cluster data."
    )
    parser.add_argument(
        "--sample-count",
        type=int,
        default=3,
        help="Number of clusters to print from each frame.",
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
            clusters = list(out.data.data_object.clusters)
            print_frame_banner(out.data.frame_id, out.data.timestamp)
            _print_sample_clusters(clusters, min(len(clusters), args.sample_count))
            processed_frames += 1
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        listener.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
