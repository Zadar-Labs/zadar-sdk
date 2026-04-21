"""Frame reassembly primitives for fragmented UDP protobuf payloads."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
import time
from typing import List, Optional

from .packet import FramePacket, FramePacketHeader


@dataclass(frozen=True)
class CompletedFrame:
    """A fully reassembled protobuf payload for one sensor frame."""

    header: FramePacketHeader
    payload: bytes

    @property
    def frame_id(self) -> int:
        return self.header.frame_id

    @property
    def timestamp_ns(self) -> int:
        return self.header.timestamp_ns


@dataclass
class _InFlightFrame:
    header: FramePacketHeader
    fragments: List[Optional[bytes]]
    received_count: int = 0
    created_at: float = 0.0
    last_updated: float = 0.0


class FrameReassembler:
    """Reassemble fragmented UDP packets into complete protobuf frames."""

    def __init__(self, max_inflight_frames: int = 32) -> None:
        if max_inflight_frames < 1:
            raise ValueError("max_inflight_frames must be at least 1")

        self._max_inflight_frames = max_inflight_frames
        self._frames: "OrderedDict[int, _InFlightFrame]" = OrderedDict()
        self.duplicate_fragments = 0
        self.evicted_frames = 0

    @property
    def inflight_count(self) -> int:
        return len(self._frames)

    def clear(self) -> None:
        self._frames.clear()

    def add_datagram(
        self,
        datagram: bytes,
        now: Optional[float] = None,
    ) -> Optional[CompletedFrame]:
        return self.add_packet(FramePacket.from_datagram(datagram), now=now)

    def add_packet(
        self,
        packet: FramePacket,
        now: Optional[float] = None,
    ) -> Optional[CompletedFrame]:
        now = time.monotonic() if now is None else now
        header = packet.header
        if header.packets_in_frame < 1:
            raise ValueError("packets_in_frame must be at least 1")
        if header.packet_index >= header.packets_in_frame:
            raise ValueError(
                f"packet_index {header.packet_index} is out of range for "
                f"{header.packets_in_frame} packets"
            )

        in_flight = self._frames.get(header.frame_id)
        if in_flight is None:
            in_flight = _InFlightFrame(
                header=header,
                fragments=[None] * header.packets_in_frame,
                created_at=now,
                last_updated=now,
            )
            self._frames[header.frame_id] = in_flight
            self._trim_oldest_frames()
        else:
            self._validate_compatible_header(in_flight.header, header)
            self._frames.move_to_end(header.frame_id)
            in_flight.last_updated = now

        existing_fragment = in_flight.fragments[header.packet_index]
        if existing_fragment is None:
            in_flight.fragments[header.packet_index] = packet.fragment
            in_flight.received_count += 1
        elif existing_fragment != packet.fragment:
            raise ValueError(
                f"Conflicting duplicate packet for frame {header.frame_id} "
                f"index {header.packet_index}"
            )
        else:
            self.duplicate_fragments += 1
            return None

        if in_flight.received_count != header.packets_in_frame:
            return None

        payload = b"".join(fragment or b"" for fragment in in_flight.fragments)
        del self._frames[header.frame_id]
        return CompletedFrame(header=in_flight.header, payload=payload)

    def _trim_oldest_frames(self) -> None:
        while len(self._frames) > self._max_inflight_frames:
            self._frames.popitem(last=False)
            self.evicted_frames += 1

    def evict_stale_frames(
        self,
        now: Optional[float] = None,
        timeout_sec: float = 1.0,
    ) -> int:
        if timeout_sec <= 0:
            raise ValueError("timeout_sec must be positive")

        now = time.monotonic() if now is None else now
        stale_frame_ids = [
            frame_id
            for frame_id, in_flight in self._frames.items()
            if now - in_flight.last_updated > timeout_sec
        ]
        for frame_id in stale_frame_ids:
            del self._frames[frame_id]
        self.evicted_frames += len(stale_frame_ids)
        return len(stale_frame_ids)

    @staticmethod
    def _validate_compatible_header(
        expected: FramePacketHeader,
        observed: FramePacketHeader,
    ) -> None:
        if expected.packets_in_frame != observed.packets_in_frame:
            raise ValueError(
                f"Frame {observed.frame_id} changed packets_in_frame from "
                f"{expected.packets_in_frame} to {observed.packets_in_frame}"
            )
        if expected.radar_id != observed.radar_id:
            raise ValueError(
                f"Frame {observed.frame_id} changed radar_id from "
                f"{expected.radar_id} to {observed.radar_id}"
            )
        if expected.data_format != observed.data_format:
            raise ValueError(
                f"Frame {observed.frame_id} changed data_format from "
                f"{expected.data_format} to {observed.data_format}"
            )
