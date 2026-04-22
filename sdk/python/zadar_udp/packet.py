"""Packet parsing utilities for the customer-facing UDP SDK."""

from __future__ import annotations

from dataclasses import dataclass
import struct

HEADER_FORMAT = "<HHIQQHHHH"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)


@dataclass(frozen=True)
class FramePacketHeader:
    """Parsed header for a fragmented UDP radar frame packet."""

    radar_id: int
    data_format: int
    points_in_frame: int
    timestamp_sec: int
    timestamp_nsec: int
    frame_id: int
    packets_in_frame: int
    packet_index: int
    data_size: int

    @classmethod
    def from_bytes(cls, datagram: bytes) -> "FramePacketHeader":
        if len(datagram) < HEADER_SIZE:
            raise ValueError(
                f"Datagram is too small for a Zadar UDP header: "
                f"expected at least {HEADER_SIZE} bytes, got {len(datagram)}"
            )

        return cls(*struct.unpack_from(HEADER_FORMAT, datagram, 0))

    @property
    def timestamp_ns(self) -> int:
        return (self.timestamp_sec * 1_000_000_000) + self.timestamp_nsec

    def extract_fragment(self, datagram: bytes) -> bytes:
        start = HEADER_SIZE
        end = HEADER_SIZE + self.data_size
        if len(datagram) < end:
            raise ValueError(
                f"Datagram payload is truncated: expected {end} bytes, "
                f"got {len(datagram)}"
            )
        return datagram[start:end]


@dataclass(frozen=True)
class FramePacket:
    """One received UDP packet containing a fragment of a protobuf frame."""

    header: FramePacketHeader
    fragment: bytes

    @classmethod
    def from_datagram(cls, datagram: bytes) -> "FramePacket":
        header = FramePacketHeader.from_bytes(datagram)
        return cls(header=header, fragment=header.extract_fragment(datagram))
