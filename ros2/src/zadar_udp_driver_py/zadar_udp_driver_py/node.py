"""ROS 2 Python driver for Zadar UDP radar sensors."""

from __future__ import annotations

from collections import Counter
import errno
import threading
from typing import List, Optional

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import Imu, PointCloud2

from .conversions import (
    clusters_to_msg,
    frame_timestamp_ns,
    imu_payload_to_msg,
    odometry_to_msg,
    radar_scan_to_pointcloud2,
    scan_timestamp_ns,
    tracks_to_msg,
)
from .sdk_bootstrap import default_generated_python_dir, ensure_sdk_on_path


UDP_ROOT = ensure_sdk_on_path()

from zadar_udp import ImuDataListener, ImuStatusCodes, RadarDataListener, RadarStatusCodes
from zadar_webapi import ZadarWebApiClient
from zadar_webapi.driver_control import (
    DEFAULT_DATA_PORT,
    DEFAULT_IMU_PORT,
    DEFAULT_WEBAPI_PORT,
    DriverControlError,
    configure_sensor_for_udp,
    resolve_managed_network_settings,
)
from zadar_msgs.msg import ZadarClusters, ZadarOdometry, ZadarTracks


class ZadarUdpDriverNode(Node):
    """Live UDP driver node for Zadar ROS 2 integrations."""

    def __init__(self) -> None:
        super().__init__("zadar_udp_driver")

        self._stop_event = threading.Event()
        self._threads: List[threading.Thread] = []
        self._radar_status_counts = Counter()
        self._imu_status_counts = Counter()

        default_generated_dir = str(default_generated_python_dir())

        self.declare_parameter("udp_bind_address", "")
        self.declare_parameter("bind_address", "0.0.0.0")
        self.declare_parameter("sensor_hostname", "")
        self.declare_parameter("host_ip", "")
        self.declare_parameter("data_port", 0)
        self.declare_parameter("imu_port", 0)
        self.declare_parameter("webapi_port", DEFAULT_WEBAPI_PORT)
        self.declare_parameter("webapi_timeout_sec", 5.0)
        self.declare_parameter("running_mode", -1)
        self.declare_parameter("frame_id", "zadar")
        self.declare_parameter("publish_scan", True)
        self.declare_parameter("publish_clusters", True)
        self.declare_parameter("publish_tracks", True)
        self.declare_parameter("publish_odometry", True)
        self.declare_parameter("publish_imu", True)
        self.declare_parameter("radar_socket_buffer_bytes", 64 * 1024 * 1024)
        self.declare_parameter("imu_socket_buffer_bytes", 4 * 1024 * 1024)
        self.declare_parameter("max_buffered_frames", 128)
        self.declare_parameter("frame_timeout_sec", 1.0)
        self.declare_parameter("socket_timeout_sec", 0.25)
        self.declare_parameter("generated_python_dir", default_generated_dir)

        configured_udp_bind_address = str(
            self.get_parameter("udp_bind_address").value
        ).strip()
        configured_legacy_bind_address = str(
            self.get_parameter("bind_address").value
        ).strip()
        self._sensor_hostname = str(self.get_parameter("sensor_hostname").value).strip()
        self._host_ip = str(self.get_parameter("host_ip").value).strip()
        self._managed_mode = bool(self._sensor_hostname)
        self._bind_address = configured_udp_bind_address or configured_legacy_bind_address
        if not self._bind_address:
            self._bind_address = "0.0.0.0"
        if (
            configured_legacy_bind_address
            and not configured_udp_bind_address
            and configured_legacy_bind_address != "0.0.0.0"
        ):
            self.get_logger().warning(
                "Parameter 'bind_address' is deprecated; prefer 'udp_bind_address'."
            )
        self._requested_data_port = int(self.get_parameter("data_port").value)
        self._requested_imu_port = int(self.get_parameter("imu_port").value)
        self._webapi_port = int(self.get_parameter("webapi_port").value)
        self._webapi_timeout_sec = float(self.get_parameter("webapi_timeout_sec").value)
        self._running_mode = int(self.get_parameter("running_mode").value)
        self._frame_id = str(self.get_parameter("frame_id").value)
        self._publish_scan = bool(self.get_parameter("publish_scan").value)
        self._publish_clusters = bool(self.get_parameter("publish_clusters").value)
        self._publish_tracks = bool(self.get_parameter("publish_tracks").value)
        self._publish_odometry = bool(self.get_parameter("publish_odometry").value)
        self._publish_imu = bool(self.get_parameter("publish_imu").value)
        self._radar_socket_buffer_bytes = int(
            self.get_parameter("radar_socket_buffer_bytes").value
        )
        self._imu_socket_buffer_bytes = int(
            self.get_parameter("imu_socket_buffer_bytes").value
        )
        self._max_buffered_frames = int(self.get_parameter("max_buffered_frames").value)
        self._frame_timeout_sec = float(self.get_parameter("frame_timeout_sec").value)
        self._socket_timeout_sec = float(self.get_parameter("socket_timeout_sec").value)
        self._generated_python_dir = str(
            self.get_parameter("generated_python_dir").value
        )
        self._radar_stream_enabled = any(
            (
                self._publish_scan,
                self._publish_clusters,
                self._publish_tracks,
                self._publish_odometry,
            )
        )
        self._imu_stream_enabled = self._publish_imu
        self._destination_ip: Optional[str] = None
        self._data_port = 0
        self._imu_port = 0

        if self._running_mode >= 0 and not self._managed_mode:
            raise RuntimeError(
                "running_mode requires sensor_hostname so the driver can control the sensor."
            )
        if self._host_ip and not self._managed_mode:
            self.get_logger().warning(
                "Parameter 'host_ip' is ignored unless sensor_hostname is provided."
            )

        self._points_publisher = (
            self.create_publisher(PointCloud2, "points", 10)
            if self._publish_scan
            else None
        )
        self._clusters_publisher = (
            self.create_publisher(ZadarClusters, "clusters", 10)
            if self._publish_clusters
            else None
        )
        self._tracks_publisher = (
            self.create_publisher(ZadarTracks, "tracks", 10)
            if self._publish_tracks
            else None
        )
        self._odometry_publisher = (
            self.create_publisher(ZadarOdometry, "odometry", 10)
            if self._publish_odometry
            else None
        )
        self._imu_publisher = (
            self.create_publisher(Imu, "imu", 10) if self._publish_imu else None
        )

        self._radar_listener: Optional[RadarDataListener] = None
        self._imu_listener: Optional[ImuDataListener] = None

        if self._managed_mode:
            self._prepare_managed_single_sensor()
        else:
            self._prepare_receive_only()

        self._start_workers()
        self._log_launch_configuration()

    def _make_radar_listener(self, port: int) -> RadarDataListener:
        return RadarDataListener(
            ip=self._bind_address,
            port=port,
            rx_buffer_bytes=self._radar_socket_buffer_bytes,
            max_buffered_frames=self._max_buffered_frames,
            frame_timeout_sec=self._frame_timeout_sec,
            socket_timeout_sec=self._socket_timeout_sec,
            generated_python_dir=self._generated_python_dir or None,
        )

    def _make_imu_listener(self, port: int) -> ImuDataListener:
        return ImuDataListener(
            ip=self._bind_address,
            port=port,
            rx_buffer_bytes=self._imu_socket_buffer_bytes,
            socket_timeout_sec=self._socket_timeout_sec,
        )

    def _prepare_receive_only(self) -> None:
        self._data_port = (
            self._requested_data_port
            if self._requested_data_port > 0
            else DEFAULT_DATA_PORT
        )
        self._imu_port = (
            self._requested_imu_port if self._requested_imu_port > 0 else DEFAULT_IMU_PORT
        )

        if self._radar_stream_enabled:
            self._radar_listener = self._make_radar_listener(self._data_port)
        if self._imu_stream_enabled:
            self._imu_listener = self._make_imu_listener(self._imu_port)

    def _prepare_managed_single_sensor(self) -> None:
        settings = resolve_managed_network_settings(
            sensor_hostname=self._sensor_hostname,
            host_ip=self._host_ip,
            udp_bind_address=self.get_parameter("udp_bind_address").value,
            legacy_bind_address=self.get_parameter("bind_address").value,
            webapi_port=self._webapi_port,
        )
        self._destination_ip = settings.destination_ip
        self._bind_address = settings.bind_address

        if not self._radar_stream_enabled and self._requested_data_port > 0:
            self.get_logger().warning(
                "data_port was provided but radar publishers are disabled; the radar port is ignored."
            )
        if not self._imu_stream_enabled and self._requested_imu_port > 0:
            self.get_logger().warning(
                "imu_port was provided but IMU publishing is disabled; the IMU port is ignored."
            )

        if self._radar_stream_enabled and self._imu_stream_enabled:
            (
                self._data_port,
                self._imu_port,
                self._radar_listener,
                self._imu_listener,
            ) = self._reserve_listener_pair()
        elif self._radar_stream_enabled:
            self._data_port, self._radar_listener = self._reserve_radar_listener()
        elif self._imu_stream_enabled:
            self._imu_port, self._imu_listener = self._reserve_imu_listener()

        client = ZadarWebApiClient(
            self._sensor_hostname,
            port=self._webapi_port,
            timeout_sec=self._webapi_timeout_sec,
        )
        configure_sensor_for_udp(
            client,
            destination_ip=self._destination_ip,
            data_port=self._data_port if self._radar_stream_enabled else None,
            imu_port=self._imu_port if self._imu_stream_enabled else None,
            running_mode=self._running_mode if self._running_mode >= 0 else None,
        )

    def _reserve_radar_listener(self) -> tuple[int, RadarDataListener]:
        explicit = self._requested_data_port > 0
        start_port = self._requested_data_port if explicit else DEFAULT_DATA_PORT
        last_error: Optional[BaseException] = None

        for candidate_port in range(start_port, start_port + 256):
            listener = self._make_radar_listener(candidate_port)
            try:
                listener.open()
                return candidate_port, listener
            except OSError as error:
                listener.close()
                if explicit or getattr(error, "errno", None) != errno.EADDRINUSE:
                    raise DriverControlError(
                        f"Unable to bind radar UDP listener on {self._bind_address}:{candidate_port}: {error}"
                    ) from error
                last_error = error

        raise DriverControlError(
            f"Unable to allocate an available radar UDP port starting from {start_port}: {last_error}"
        )

    def _reserve_imu_listener(self) -> tuple[int, ImuDataListener]:
        explicit = self._requested_imu_port > 0
        start_port = self._requested_imu_port if explicit else DEFAULT_IMU_PORT
        last_error: Optional[BaseException] = None

        for candidate_port in range(start_port, start_port + 256):
            listener = self._make_imu_listener(candidate_port)
            try:
                listener.open()
                return candidate_port, listener
            except OSError as error:
                listener.close()
                if explicit or getattr(error, "errno", None) != errno.EADDRINUSE:
                    raise DriverControlError(
                        f"Unable to bind IMU UDP listener on {self._bind_address}:{candidate_port}: {error}"
                    ) from error
                last_error = error

        raise DriverControlError(
            f"Unable to allocate an available IMU UDP port starting from {start_port}: {last_error}"
        )

    def _reserve_listener_pair(
        self,
    ) -> tuple[int, int, RadarDataListener, ImuDataListener]:
        data_explicit = self._requested_data_port > 0
        imu_explicit = self._requested_imu_port > 0

        if data_explicit and imu_explicit:
            return self._reserve_explicit_pair(
                self._requested_data_port,
                self._requested_imu_port,
            )

        if data_explicit:
            for imu_port in range(DEFAULT_IMU_PORT, DEFAULT_IMU_PORT + 256):
                pair = self._try_reserve_pair(self._requested_data_port, imu_port)
                if pair is not None:
                    return pair
            raise DriverControlError(
                f"Unable to allocate an IMU UDP port starting from {DEFAULT_IMU_PORT} "
                f"while using explicit radar port {self._requested_data_port}."
            )

        if imu_explicit:
            for data_port in range(DEFAULT_DATA_PORT, DEFAULT_DATA_PORT + 256):
                pair = self._try_reserve_pair(data_port, self._requested_imu_port)
                if pair is not None:
                    return pair
            raise DriverControlError(
                f"Unable to allocate a radar UDP port starting from {DEFAULT_DATA_PORT} "
                f"while using explicit IMU port {self._requested_imu_port}."
            )

        for offset in range(256):
            pair = self._try_reserve_pair(
                DEFAULT_DATA_PORT + offset,
                DEFAULT_IMU_PORT + offset,
            )
            if pair is not None:
                return pair

        raise DriverControlError(
            "Unable to allocate a managed radar/IMU UDP port pair."
        )

    def _reserve_explicit_pair(
        self,
        data_port: int,
        imu_port: int,
    ) -> tuple[int, int, RadarDataListener, ImuDataListener]:
        pair = self._try_reserve_pair(data_port, imu_port, allow_port_in_use_scan=False)
        if pair is None:
            raise DriverControlError(
                f"Unable to bind the requested UDP ports {data_port} and {imu_port} "
                f"on {self._bind_address}."
            )
        return pair

    def _try_reserve_pair(
        self,
        data_port: int,
        imu_port: int,
        *,
        allow_port_in_use_scan: bool = True,
    ) -> Optional[tuple[int, int, RadarDataListener, ImuDataListener]]:
        radar_listener = self._make_radar_listener(data_port)
        imu_listener = self._make_imu_listener(imu_port)

        try:
            radar_listener.open()
            imu_listener.open()
            return data_port, imu_port, radar_listener, imu_listener
        except OSError as error:
            radar_listener.close()
            imu_listener.close()
            if allow_port_in_use_scan and getattr(error, "errno", None) == errno.EADDRINUSE:
                return None
            raise DriverControlError(
                f"Unable to bind managed UDP listeners on {self._bind_address}:{data_port} "
                f"and {self._bind_address}:{imu_port}: {error}"
            ) from error

    def _log_launch_configuration(self) -> None:
        if self._managed_mode:
            mode_text = (
                str(self._running_mode) if self._running_mode >= 0 else "not started"
            )
            self.get_logger().info(
                f"Managed sensor {self._sensor_hostname} configured for "
                f"udp://{self._destination_ip}:{self._data_port} (radar) and "
                f"udp://{self._destination_ip}:{self._imu_port} (imu); "
                f"listening on udp://{self._bind_address}:{self._data_port} and "
                f"udp://{self._bind_address}:{self._imu_port}; running mode: {mode_text}"
            )
            return

        self.get_logger().info(
            f"Listening on udp://{self._bind_address}:{self._data_port} "
            f"(radar) and udp://{self._bind_address}:{self._imu_port} (imu)"
        )

    def _start_workers(self) -> None:
        if self._radar_listener is not None:
            self._threads.append(
                threading.Thread(target=self._radar_loop, name="zadar-radar", daemon=True)
            )
        if self._imu_listener is not None:
            self._threads.append(
                threading.Thread(target=self._imu_loop, name="zadar-imu", daemon=True)
            )

        for thread in self._threads:
            thread.start()

        if not self._threads:
            self.get_logger().warning("No publishers are enabled; the driver is idle.")

    def _log_status(self, counter: Counter, status_code: int, label: str) -> None:
        counter[status_code] += 1
        occurrences = counter[status_code]
        if occurrences <= 5 or occurrences % 100 == 0:
            self.get_logger().warning(
                f"{label} status {status_code} received {occurrences} time(s)."
            )

    def _radar_loop(self) -> None:
        assert self._radar_listener is not None

        while rclpy.ok() and not self._stop_event.is_set():
            try:
                output = self._radar_listener.read_frame()
            except Exception as error:
                if not self._stop_event.is_set():
                    self.get_logger().error(f"Radar listener stopped: {error}")
                break

            if output is None:
                continue
            if output.status_code != RadarStatusCodes.FINE or output.data is None:
                self._log_status(
                    self._radar_status_counts,
                    int(output.status_code),
                    "Radar",
                )
                continue

            payload = output.data
            radar_frame = payload.data_object
            fallback_timestamp_ns = frame_timestamp_ns(payload.timestamp)
            message_timestamp_ns = scan_timestamp_ns(
                radar_frame.radar_scan,
                fallback_timestamp_ns,
            )

            if self._points_publisher is not None:
                self._points_publisher.publish(
                    radar_scan_to_pointcloud2(
                        radar_frame.radar_scan,
                        self._frame_id,
                        message_timestamp_ns,
                    )
                )

            if self._clusters_publisher is not None:
                self._clusters_publisher.publish(
                    clusters_to_msg(
                        radar_frame.clusters,
                        self._frame_id,
                        message_timestamp_ns,
                    )
                )

            if self._tracks_publisher is not None:
                self._tracks_publisher.publish(
                    tracks_to_msg(
                        radar_frame.tracks,
                        self._frame_id,
                        message_timestamp_ns,
                        payload.frame_id,
                    )
                )

            if self._odometry_publisher is not None and radar_frame.HasField("odometry"):
                self._odometry_publisher.publish(
                    odometry_to_msg(
                        radar_frame.odometry,
                        self._frame_id,
                        message_timestamp_ns,
                    )
                )

    def _imu_loop(self) -> None:
        assert self._imu_listener is not None

        while rclpy.ok() and not self._stop_event.is_set():
            try:
                output = self._imu_listener.read_packet()
            except Exception as error:
                if not self._stop_event.is_set():
                    self.get_logger().error(f"IMU listener stopped: {error}")
                break

            if output is None:
                continue
            if output.status_code != ImuStatusCodes.FINE or output.data is None:
                self._log_status(
                    self._imu_status_counts,
                    int(output.status_code),
                    "IMU",
                )
                continue

            if self._imu_publisher is not None:
                self._imu_publisher.publish(
                    imu_payload_to_msg(output.data, self._frame_id)
                )

    def destroy_node(self) -> bool:
        self._stop_event.set()

        if self._radar_listener is not None:
            self._radar_listener.close()
        if self._imu_listener is not None:
            self._imu_listener.close()

        for thread in self._threads:
            thread.join(timeout=1.0)

        return super().destroy_node()


def main(args: Optional[List[str]] = None) -> None:
    rclpy.init(args=args)
    node = ZadarUdpDriverNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
