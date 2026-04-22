"""UDP socket utilities for receiving reassembled Zadar frames."""

from __future__ import annotations

import socket
from typing import Iterator, Optional

from .reassembly import CompletedFrame, FrameReassembler


class UdpFrameSource:
    """Receive UDP datagrams and yield reassembled frame payloads."""

    def __init__(
        self,
        bind_address: str = "0.0.0.0",
        data_port: int = 7777,
        *,
        receive_buffer_bytes: Optional[int] = None,
        max_datagram_size: int = 65535,
        socket_timeout_sec: Optional[float] = None,
        max_inflight_frames: int = 32,
    ) -> None:
        self._bind_address = bind_address
        self._data_port = data_port
        self._receive_buffer_bytes = receive_buffer_bytes
        self._max_datagram_size = max_datagram_size
        self._socket_timeout_sec = socket_timeout_sec
        self._socket: Optional[socket.socket] = None
        self._reassembler = FrameReassembler(max_inflight_frames=max_inflight_frames)

    @property
    def reassembler(self) -> FrameReassembler:
        return self._reassembler

    def open(self) -> "UdpFrameSource":
        if self._socket is not None:
            return self

        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if self._receive_buffer_bytes is not None:
            udp_socket.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_RCVBUF,
                self._receive_buffer_bytes,
            )
        if self._socket_timeout_sec is not None:
            udp_socket.settimeout(self._socket_timeout_sec)
        udp_socket.bind((self._bind_address, self._data_port))
        self._socket = udp_socket
        return self

    def close(self) -> None:
        if self._socket is None:
            return
        self._socket.close()
        self._socket = None

    def __enter__(self) -> "UdpFrameSource":
        return self.open()

    def __exit__(self, exc_type, exc, exc_tb) -> None:
        self.close()

    def recv_datagram(self) -> bytes:
        if self._socket is None:
            self.open()
        assert self._socket is not None
        datagram, _ = self._socket.recvfrom(self._max_datagram_size)
        return datagram

    def recv_frame(self) -> CompletedFrame:
        while True:
            completed = self._reassembler.add_datagram(self.recv_datagram())
            if completed is not None:
                return completed

    def frames(self) -> Iterator[CompletedFrame]:
        while True:
            yield self.recv_frame()
