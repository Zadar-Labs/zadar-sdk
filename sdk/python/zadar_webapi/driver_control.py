"""Shared driver-control helpers for managed Zadar sensor launch flows."""

from __future__ import annotations

from dataclasses import dataclass
import socket
from typing import Optional

from .client import ApiResponse, ZadarWebApiClient


DEFAULT_DATA_PORT = 7777
DEFAULT_IMU_PORT = 36636
DEFAULT_WEBAPI_PORT = 8080


class DriverControlError(RuntimeError):
    """Raised when the managed control-plane flow fails."""


@dataclass(frozen=True)
class ManagedNetworkSettings:
    destination_ip: str
    bind_address: str


def _normalize_ip(value: str) -> str:
    return str(value).strip()


def _is_wildcard_bind_address(value: str) -> bool:
    normalized = _normalize_ip(value)
    return normalized in ("", "0.0.0.0", "::")


def detect_host_ip_for_sensor(sensor_hostname: str, *, webapi_port: int) -> str:
    sensor_host = _normalize_ip(sensor_hostname)
    if not sensor_host:
        raise DriverControlError("sensor_hostname must not be empty")

    probe_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe_socket.connect((sensor_host, int(webapi_port)))
        local_ip = probe_socket.getsockname()[0]
    except OSError as error:
        raise DriverControlError(
            f"Unable to determine a local host IP for sensor '{sensor_host}': {error}"
        ) from error
    finally:
        probe_socket.close()

    local_ip = _normalize_ip(local_ip)
    if not local_ip:
        raise DriverControlError(
            f"Unable to determine a local host IP for sensor '{sensor_host}'."
        )
    return local_ip


def resolve_managed_network_settings(
    *,
    sensor_hostname: str,
    host_ip: str,
    udp_bind_address: str,
    legacy_bind_address: str,
    webapi_port: int = DEFAULT_WEBAPI_PORT,
) -> ManagedNetworkSettings:
    sensor_host = _normalize_ip(sensor_hostname)
    if not sensor_host:
        raise DriverControlError(
            "sensor_hostname is required for managed single-sensor launch."
        )

    normalized_host_ip = _normalize_ip(host_ip)
    normalized_udp_bind = _normalize_ip(udp_bind_address)
    normalized_legacy_bind = _normalize_ip(legacy_bind_address)

    destination_ip = normalized_host_ip
    if not destination_ip and not _is_wildcard_bind_address(normalized_udp_bind):
        destination_ip = normalized_udp_bind
    if not destination_ip and not _is_wildcard_bind_address(normalized_legacy_bind):
        destination_ip = normalized_legacy_bind
    if not destination_ip:
        destination_ip = detect_host_ip_for_sensor(
            sensor_host,
            webapi_port=webapi_port,
        )

    bind_address = normalized_udp_bind or normalized_legacy_bind
    if _is_wildcard_bind_address(bind_address):
        bind_address = destination_ip

    return ManagedNetworkSettings(
        destination_ip=destination_ip,
        bind_address=bind_address,
    )


def extract_error_message(response: ApiResponse) -> str:
    if response.error:
        return response.error
    if response.json_body:
        description = response.json_body.get("description")
        if isinstance(description, str) and description:
            return description
    if response.text_body:
        return response.text_body.strip()
    return f"HTTP {response.status_code}"


def require_success(action: str, response: ApiResponse) -> None:
    if response.success:
        return
    raise DriverControlError(f"{action} failed: {extract_error_message(response)}")


def configure_sensor_for_udp(
    client: ZadarWebApiClient,
    *,
    destination_ip: str,
    data_port: Optional[int],
    imu_port: Optional[int],
    running_mode: Optional[int],
) -> None:
    require_success(
        "Web API heartbeat",
        client.get_device_clock(),
    )
    require_success(
        "Configuring output destination IP",
        client.set_output_destination_ip_address(destination_ip),
    )

    if data_port is not None:
        require_success(
            "Configuring radar data port",
            client.set_pcl_port(int(data_port)),
        )
    if imu_port is not None:
        require_success(
            "Configuring IMU port",
            client.set_imu_port(int(imu_port)),
        )

    if running_mode is not None and int(running_mode) >= 0:
        require_success(
            f"Starting running mode {int(running_mode)}",
            client.set_running_mode(int(running_mode)),
        )
