"""High-level customer IMU listener APIs for the UDP package."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import socket
import struct
from typing import Iterator, Optional, Tuple

from .crc import CRC64Ecma182


@dataclass(frozen=True)
class ImuPacketData:
    diagnostic_timestamp: int
    accelerometer_timestamp: int
    gyroscope_timestamp: int
    acceleration_x: float
    acceleration_y: float
    acceleration_z: float
    angular_rate_x: float
    angular_rate_y: float
    angular_rate_z: float


@dataclass
class ImuDataPayload:
    timestamp: Tuple[int, int]
    frame_id: int
    data_object: ImuPacketData

    @property
    def dataObject(self) -> ImuPacketData:
        return self.data_object


@dataclass
class ImuDataOutput:
    status_code: int
    data: Optional[ImuDataPayload]


@dataclass
class ImuListenerStats:
    packets_received: int = 0
    bytes_received: int = 0
    malformed_packets: int = 0
    crc_errors: int = 0
    completed_packets: int = 0


class ImuStatusCodes(IntEnum):
    IMPROPER_PACKET = -1
    IMPROPER_CRC = -2
    FINE = 0


class ImuDataListener:
    """Receive and parse IMU UDP packets from a single sensor stream."""

    HEADER_STRUCT = struct.Struct("<QIIIIIIQQ")
    DATA_STRUCT = struct.Struct("<QQQffffffQ")
    HEADER_SIZE = HEADER_STRUCT.size
    DATA_SIZE = DATA_STRUCT.size
    PACKET_SIZE = HEADER_SIZE + DATA_SIZE
    MAX_DATAGRAM_SIZE = 65535
    DEFAULT_RCVBUF_BYTES = 4 * 1024 * 1024

    def __init__(
        self,
        ip: str = "0.0.0.0",
        port: int = 36636,
        *,
        rx_buffer_bytes: int = DEFAULT_RCVBUF_BYTES,
        socket_timeout_sec: Optional[float] = None,
    ) -> None:
        self.ip = ip
        self.port = port
        self.rx_buffer_bytes = rx_buffer_bytes
        self.socket_timeout_sec = socket_timeout_sec

        self._socket: Optional[socket.socket] = None
        self._stats = ImuListenerStats()
        self._recv_buffer = bytearray(self.MAX_DATAGRAM_SIZE)

    def open(self) -> "ImuDataListener":
        if self._socket is not None:
            return self

        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.rx_buffer_bytes)
        if self.socket_timeout_sec is not None:
            udp_socket.settimeout(self.socket_timeout_sec)
        udp_socket.bind((self.ip, self.port))
        self._socket = udp_socket
        return self

    def close(self) -> None:
        if self._socket is None:
            return
        self._socket.close()
        self._socket = None

    def get_stats(self) -> ImuListenerStats:
        return ImuListenerStats(**self._stats.__dict__)

    def _make_output(
        self,
        status_code: ImuStatusCodes,
        data: Optional[ImuDataPayload] = None,
    ) -> ImuDataOutput:
        return ImuDataOutput(status_code=int(status_code), data=data)

    def _process_datagram(self, packet: memoryview, packet_size: int) -> ImuDataOutput:
        if packet_size < self.PACKET_SIZE:
            self._stats.malformed_packets += 1
            return self._make_output(ImuStatusCodes.IMPROPER_PACKET)

        packet_crc = struct.unpack_from("<Q", packet, packet_size - 8)[0]
        crc_engine = CRC64Ecma182()
        crc_engine.update(packet[: packet_size - 8])
        if packet_crc != crc_engine.digest():
            self._stats.crc_errors += 1
            return self._make_output(ImuStatusCodes.IMPROPER_CRC)

        (
            _stream_id,
            _version,
            _radar_id,
            frame_id,
            data_size,
            _dopplers,
            _ranges,
            timestamp_sec,
            timestamp_nsec,
        ) = self.HEADER_STRUCT.unpack_from(packet)

        (
            diagnostic_timestamp,
            accelerometer_timestamp,
            gyroscope_timestamp,
            acceleration_x,
            acceleration_y,
            acceleration_z,
            angular_rate_x,
            angular_rate_y,
            angular_rate_z,
            embedded_crc,
        ) = self.DATA_STRUCT.unpack_from(packet, self.HEADER_SIZE)

        if embedded_crc != packet_crc:
            self._stats.crc_errors += 1
            return self._make_output(ImuStatusCodes.IMPROPER_CRC)

        self._stats.completed_packets += 1
        return self._make_output(
            ImuStatusCodes.FINE,
            ImuDataPayload(
                timestamp=(timestamp_sec, timestamp_nsec),
                frame_id=frame_id,
                data_object=ImuPacketData(
                    diagnostic_timestamp=diagnostic_timestamp,
                    accelerometer_timestamp=accelerometer_timestamp,
                    gyroscope_timestamp=gyroscope_timestamp,
                    acceleration_x=acceleration_x,
                    acceleration_y=acceleration_y,
                    acceleration_z=acceleration_z,
                    angular_rate_x=angular_rate_x,
                    angular_rate_y=angular_rate_y,
                    angular_rate_z=angular_rate_z,
                ),
            ),
        )

    def read_packet(self) -> Optional[ImuDataOutput]:
        self.open()
        assert self._socket is not None
        recv_buffer_view = memoryview(self._recv_buffer)

        try:
            packet_size, _addr = self._socket.recvfrom_into(self._recv_buffer)
        except socket.timeout:
            return None

        self._stats.packets_received += 1
        self._stats.bytes_received += packet_size
        return self._process_datagram(recv_buffer_view, packet_size)

    def read_imu_data(self) -> Iterator[ImuDataOutput]:
        while True:
            output = self.read_packet()
            if output is None:
                continue
            yield output
