"""High-level customer radar listener APIs built on the shared UDP SDK."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import socket
from typing import Iterator, Optional, Tuple
import time

from .proto import load_zadar_proto_module
from .source import UdpFrameSource


@dataclass
class RadarDataPayload:
    timestamp: Tuple[int, int]
    frame_id: int
    data_object: object

    @property
    def dataObject(self) -> object:
        return self.data_object


@dataclass
class RadarDataOutput:
    status_code: int
    data: Optional[RadarDataPayload]


@dataclass
class RadarListenerStats:
    packets_received: int = 0
    bytes_received: int = 0
    malformed_packets: int = 0
    duplicate_fragments: int = 0
    completed_frames: int = 0
    proto_parse_errors: int = 0
    evicted_frames: int = 0


class RadarStatusCodes(IntEnum):
    IMPROPER_PACKET = -1
    IMPROPER_CRC = -2
    FINE = 0
    PROTO_PARSING_ERROR = 1


class RadarDataListener:
    """Receive and parse reassembled radar frames from a UDP stream."""

    DEFAULT_RCVBUF_BYTES = 64 * 1024 * 1024
    DEFAULT_MAX_BUFFERED_FRAMES = 128
    DEFAULT_FRAME_TIMEOUT_SEC = 1.0

    def __init__(
        self,
        ip: str = "0.0.0.0",
        port: int = 7777,
        *,
        rx_buffer_bytes: int = DEFAULT_RCVBUF_BYTES,
        max_buffered_frames: int = DEFAULT_MAX_BUFFERED_FRAMES,
        frame_timeout_sec: float = DEFAULT_FRAME_TIMEOUT_SEC,
        socket_timeout_sec: Optional[float] = None,
        generated_python_dir: Optional[str] = None,
    ) -> None:
        if max_buffered_frames <= 0:
            raise ValueError("max_buffered_frames must be positive")
        if frame_timeout_sec <= 0:
            raise ValueError("frame_timeout_sec must be positive")

        self.ip = ip
        self.port = port
        self.rx_buffer_bytes = rx_buffer_bytes
        self.max_buffered_frames = max_buffered_frames
        self.frame_timeout_sec = frame_timeout_sec
        self.socket_timeout_sec = socket_timeout_sec

        self._proto_module = load_zadar_proto_module(generated_python_dir)
        if self._proto_module is None:
            raise RuntimeError(
                "ZadarFrame protobuf bindings are unavailable. Run "
                "`scripts/build_proto.sh` first."
            )

        self._source = UdpFrameSource(
            bind_address=ip,
            data_port=port,
            receive_buffer_bytes=rx_buffer_bytes,
            socket_timeout_sec=socket_timeout_sec,
            max_inflight_frames=max_buffered_frames,
        )
        self._stats = RadarListenerStats()

    def open(self) -> "RadarDataListener":
        self._source.open()
        return self

    def close(self) -> None:
        self._source.close()

    def get_stats(self) -> RadarListenerStats:
        return RadarListenerStats(**self._stats.__dict__)

    def _make_output(
        self,
        status_code: RadarStatusCodes,
        data: Optional[RadarDataPayload] = None,
    ) -> RadarDataOutput:
        return RadarDataOutput(status_code=int(status_code), data=data)

    def _sync_reassembly_stats(self) -> None:
        reassembler = self._source.reassembler
        self._stats.duplicate_fragments = reassembler.duplicate_fragments
        self._stats.evicted_frames = reassembler.evicted_frames

    def read_frame(self) -> Optional[RadarDataOutput]:
        self.open()
        reassembler = self._source.reassembler

        while True:
            try:
                datagram = self._source.recv_datagram()
            except socket.timeout:
                return None
            now = time.monotonic()
            self._stats.packets_received += 1
            self._stats.bytes_received += len(datagram)

            reassembler.evict_stale_frames(now=now, timeout_sec=self.frame_timeout_sec)
            self._sync_reassembly_stats()

            try:
                completed = reassembler.add_datagram(datagram, now=now)
            except ValueError:
                self._stats.malformed_packets += 1
                self._sync_reassembly_stats()
                return self._make_output(RadarStatusCodes.IMPROPER_PACKET)

            self._sync_reassembly_stats()
            if completed is None:
                continue

            radar_frame = self._proto_module.ZadarFrame()
            try:
                radar_frame.ParseFromString(completed.payload)
            except Exception:
                self._stats.proto_parse_errors += 1
                return self._make_output(RadarStatusCodes.PROTO_PARSING_ERROR)

            self._stats.completed_frames += 1
            return self._make_output(
                RadarStatusCodes.FINE,
                RadarDataPayload(
                    timestamp=(
                        completed.header.timestamp_sec,
                        completed.header.timestamp_nsec,
                    ),
                    frame_id=completed.frame_id,
                    data_object=radar_frame,
                ),
            )

    def read_frames(self) -> Iterator[RadarDataOutput]:
        while True:
            output = self.read_frame()
            if output is None:
                continue
            yield output
