#!/usr/bin/env python3
"""Listen for UDP radar frames and print a concise raw frame summary."""

from __future__ import annotations

import argparse
import socket

from _example_support import (
    GENERATED_PYTHON_DIR,
    format_timestamp_ns,
    should_report_status,
    should_stop,
)
from zadar_udp.proto import load_zadar_proto_module
from zadar_udp.source import UdpFrameSource


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Receive Zadar UDP frames and print a concise frame summary.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--bind-address",
        default="0.0.0.0",
        help="Local interface to bind for incoming radar UDP traffic.",
    )
    parser.add_argument(
        "--port",
        "--data-port",
        dest="port",
        type=int,
        default=7777,
        help="Radar UDP port.",
    )
    parser.add_argument(
        "--socket-buffer-bytes",
        type=int,
        default=4 * 1024 * 1024,
        help="Receive socket buffer size in bytes.",
    )
    parser.add_argument(
        "--socket-timeout-sec",
        type=float,
        default=None,
        help="Optional socket read timeout in seconds.",
    )
    parser.add_argument(
        "--frame-limit",
        type=int,
        default=0,
        help="Stop after this many completed radar frames. Use 0 to run continuously.",
    )
    parser.add_argument(
        "--generated-python-dir",
        default=str(GENERATED_PYTHON_DIR),
        help=(
            "Directory containing generated ZadarFrame_pb2.py."
        ),
    )
    return parser.parse_args()


def summarize_with_proto(proto_module, payload: bytes) -> str:
    zadar_frame = proto_module.ZadarFrame()
    zadar_frame.ParseFromString(payload)
    scan_points = len(zadar_frame.radar_scan.points)
    clusters = len(zadar_frame.clusters)
    tracks = len(zadar_frame.tracks)
    has_odometry = zadar_frame.HasField("odometry")
    return (
        f"scan_points={scan_points} "
        f"clusters={clusters} "
        f"tracks={tracks} "
        f"odometry={has_odometry}"
    )


def _malformed_packet_message() -> str:
    return "received datagrams that do not match the radar frame format for this tool"


def main() -> int:
    args = parse_args()
    proto_module = load_zadar_proto_module(args.generated_python_dir)

    print(f"Listening on udp://{args.bind_address}:{args.port}")
    if proto_module is None:
        print(
            "Protobuf decoding is unavailable. Ensure "
            "`generated/python/ZadarFrame_pb2.py` "
            "is present, or regenerate it with "
            "`scripts/build_proto.sh`."
        )

    with UdpFrameSource(
        bind_address=args.bind_address,
        data_port=args.port,
        receive_buffer_bytes=args.socket_buffer_bytes,
        socket_timeout_sec=args.socket_timeout_sec,
    ) as source:
        try:
            processed_frames = 0
            malformed_packets = 0
            while not should_stop(processed_frames, args.frame_limit):
                try:
                    frame = source.recv_frame()
                except socket.timeout:
                    continue
                except ValueError:
                    malformed_packets += 1
                    if should_report_status(malformed_packets):
                        print(
                            "Warning: "
                            f"{_malformed_packet_message()} "
                            f"(seen {malformed_packets} time(s))"
                        )
                    continue
                summary = (
                    summarize_with_proto(proto_module, frame.payload)
                    if proto_module is not None
                    else f"payload_bytes={len(frame.payload)}"
                )
                print(
                    f"frame_id={frame.frame_id} "
                    f"timestamp='{format_timestamp_ns(frame.timestamp_ns)}' "
                    f"format={frame.header.data_format} "
                    f"packets={frame.header.packets_in_frame} "
                    f"{summary}"
                )
                processed_frames += 1
        except KeyboardInterrupt:
            print("Exiting...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
