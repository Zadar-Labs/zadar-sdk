"""ROS 1 Python driver for Zadar UDP radar sensors."""

from __future__ import annotations

from collections import Counter
import errno
import threading
from typing import Optional

import rospy
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


class ZadarUdpDriverNode:
    """Live UDP driver node for Zadar ROS 1 integrations."""

    def __init__(self) -> None:
        self._stop_event = threading.Event()
        self._threads = []
        self._radar_status_counts = Counter()
        self._imu_status_counts = Counter()

        default_generated_dir = str(default_generated_python_dir())

        configured_udp_bind_address = str(
            rospy.get_param("~udp_bind_address", "")
        ).strip()
        configured_legacy_bind_address = str(
            rospy.get_param("~bind_address", "0.0.0.0")
        ).strip()
        self._sensor_hostname = str(rospy.get_param("~sensor_hostname", "")).strip()
        self._host_ip = str(rospy.get_param("~host_ip", "")).strip()
        self._managed_mode = bool(self._sensor_hostname)

        self._bind_address = configured_udp_bind_address or configured_legacy_bind_address
        if not self._bind_address:
            self._bind_address = "0.0.0.0"
        if (
            configured_legacy_bind_address
            and not configured_udp_bind_address
            and configured_legacy_bind_address != "0.0.0.0"
        ):
            rospy.logwarn(
                "Parameter 'bind_address' is deprecated; prefer 'udp_bind_address'."
            )

        self._requested_data_port = int(rospy.get_param("~data_port", 0))
        self._requested_imu_port = int(rospy.get_param("~imu_port", 0))
        self._webapi_port = int(rospy.get_param("~webapi_port", DEFAULT_WEBAPI_PORT))
        self._webapi_timeout_sec = float(rospy.get_param("~webapi_timeout_sec", 5.0))
        self._running_mode = int(rospy.get_param("~running_mode", -1))
        self._frame_id = str(rospy.get_param("~frame_id", "zadar"))
        self._publish_scan = bool(rospy.get_param("~publish_scan", True))
        self._publish_clusters = bool(rospy.get_param("~publish_clusters", True))
        self._publish_tracks = bool(rospy.get_param("~publish_tracks", True))
        self._publish_odometry = bool(rospy.get_param("~publish_odometry", True))
        self._publish_imu = bool(rospy.get_param("~publish_imu", True))
        self._radar_socket_buffer_bytes = int(
            rospy.get_param("~radar_socket_buffer_bytes", 64 * 1024 * 1024)
        )
        self._imu_socket_buffer_bytes = int(
            rospy.get_param("~imu_socket_buffer_bytes", 4 * 1024 * 1024)
        )
        self._max_buffered_frames = int(rospy.get_param("~max_buffered_frames", 128))
        self._frame_timeout_sec = float(rospy.get_param("~frame_timeout_sec", 1.0))
        self._socket_timeout_sec = float(rospy.get_param("~socket_timeout_sec", 0.25))
        self._generated_python_dir = str(
            rospy.get_param("~generated_python_dir", default_generated_dir)
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
            rospy.logwarn(
                "Parameter 'host_ip' is ignored unless sensor_hostname is provided."
            )

        self._points_publisher = (
            rospy.Publisher("points", PointCloud2, queue_size=10)
            if self._publish_scan
            else None
        )
        self._clusters_publisher = (
            rospy.Publisher("clusters", ZadarClusters, queue_size=10)
            if self._publish_clusters
            else None
        )
        self._tracks_publisher = (
            rospy.Publisher("tracks", ZadarTracks, queue_size=10)
            if self._publish_tracks
            else None
        )
        self._odometry_publisher = (
            rospy.Publisher("odometry", ZadarOdometry, queue_size=10)
            if self._publish_odometry
            else None
        )
        self._imu_publisher = (
            rospy.Publisher("imu", Imu, queue_size=10) if self._publish_imu else None
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
            udp_bind_address=rospy.get_param("~udp_bind_address", ""),
            legacy_bind_address=rospy.get_param("~bind_address", ""),
            webapi_port=self._webapi_port,
        )
        self._destination_ip = settings.destination_ip
        self._bind_address = settings.bind_address

        if not self._radar_stream_enabled and self._requested_data_port > 0:
            rospy.logwarn(
                "data_port was provided but radar publishers are disabled; the radar port is ignored."
            )
        if not self._imu_stream_enabled and self._requested_imu_port > 0:
            rospy.logwarn(
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
                        "Unable to bind radar UDP listener on %s:%d: %s"
                        % (self._bind_address, candidate_port, error)
                    )
                last_error = error

        raise DriverControlError(
            "Unable to allocate an available radar UDP port starting from %d: %s"
            % (start_port, last_error)
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
                        "Unable to bind IMU UDP listener on %s:%d: %s"
                        % (self._bind_address, candidate_port, error)
                    )
                last_error = error

        raise DriverControlError(
            "Unable to allocate an available IMU UDP port starting from %d: %s"
            % (start_port, last_error)
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
                "Unable to allocate an IMU UDP port starting from %d while using "
                "explicit radar port %d."
                % (DEFAULT_IMU_PORT, self._requested_data_port)
            )

        if imu_explicit:
            for data_port in range(DEFAULT_DATA_PORT, DEFAULT_DATA_PORT + 256):
                pair = self._try_reserve_pair(data_port, self._requested_imu_port)
                if pair is not None:
                    return pair
            raise DriverControlError(
                "Unable to allocate a radar UDP port starting from %d while using "
                "explicit IMU port %d."
                % (DEFAULT_DATA_PORT, self._requested_imu_port)
            )

        for offset in range(256):
            pair = self._try_reserve_pair(
                DEFAULT_DATA_PORT + offset,
                DEFAULT_IMU_PORT + offset,
            )
            if pair is not None:
                return pair

        raise DriverControlError("Unable to allocate a managed radar/IMU UDP port pair.")

    def _reserve_explicit_pair(
        self,
        data_port: int,
        imu_port: int,
    ) -> tuple[int, int, RadarDataListener, ImuDataListener]:
        pair = self._try_reserve_pair(data_port, imu_port, allow_port_in_use_scan=False)
        if pair is None:
            raise DriverControlError(
                "Unable to bind the requested UDP ports %d and %d on %s."
                % (data_port, imu_port, self._bind_address)
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
                "Unable to bind managed UDP listeners on %s:%d and %s:%d: %s"
                % (
                    self._bind_address,
                    data_port,
                    self._bind_address,
                    imu_port,
                    error,
                )
            )

    def _log_launch_configuration(self) -> None:
        if self._managed_mode:
            mode_text = (
                str(self._running_mode) if self._running_mode >= 0 else "not started"
            )
            rospy.loginfo(
                "Managed sensor %s configured for udp://%s:%d (radar) and "
                "udp://%s:%d (imu); listening on udp://%s:%d and udp://%s:%d; "
                "running mode: %s",
                self._sensor_hostname,
                self._destination_ip,
                self._data_port,
                self._destination_ip,
                self._imu_port,
                self._bind_address,
                self._data_port,
                self._bind_address,
                self._imu_port,
                mode_text,
            )
            return

        rospy.loginfo(
            "Listening on udp://%s:%d (radar) and udp://%s:%d (imu)",
            self._bind_address,
            self._data_port,
            self._bind_address,
            self._imu_port,
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
            rospy.logwarn("No publishers are enabled; the driver is idle.")

    def _log_status(self, counter: Counter, status_code: int, label: str) -> None:
        counter[status_code] += 1
        occurrences = counter[status_code]
        if occurrences <= 5 or occurrences % 100 == 0:
            rospy.logwarn(
                "%s status %d received %d time(s).",
                label,
                status_code,
                occurrences,
            )

    def _radar_loop(self) -> None:
        assert self._radar_listener is not None

        while not rospy.is_shutdown() and not self._stop_event.is_set():
            try:
                output = self._radar_listener.read_frame()
            except Exception as error:
                if not self._stop_event.is_set():
                    rospy.logerr("Radar listener stopped: %s", error)
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

        while not rospy.is_shutdown() and not self._stop_event.is_set():
            try:
                output = self._imu_listener.read_packet()
            except Exception as error:
                if not self._stop_event.is_set():
                    rospy.logerr("IMU listener stopped: %s", error)
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

    def shutdown(self) -> None:
        if self._stop_event.is_set():
            return

        self._stop_event.set()

        if self._radar_listener is not None:
            self._radar_listener.close()
        if self._imu_listener is not None:
            self._imu_listener.close()

        for thread in self._threads:
            thread.join(timeout=1.0)


def main() -> None:
    rospy.init_node("zadar_udp_driver")
    node = ZadarUdpDriverNode()
    rospy.on_shutdown(node.shutdown)
    rospy.spin()


if __name__ == "__main__":
    main()
