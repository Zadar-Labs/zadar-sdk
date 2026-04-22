"""HTTP Web API client for supported Zadar UDP-based sensors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests


@dataclass(frozen=True)
class ApiResponse:
    status_code: int
    success: bool
    json_body: Optional[Dict[str, Any]] = None
    text_body: str = ""
    error: str = ""


class ZadarWebApiClient:
    def __init__(
        self,
        sensor_host: str,
        *,
        port: int = 8080,
        api_prefix: str = "/api/v1",
        timeout_sec: float = 2.0,
        session: Optional[requests.Session] = None,
    ) -> None:
        self._sensor_host = sensor_host.strip()
        if not self._sensor_host:
            raise ValueError("sensor_host must not be empty")

        self._port = int(port)
        self._api_prefix = "/" + api_prefix.strip("/")
        self._timeout_sec = float(timeout_sec)
        self._owns_session = session is None
        self._session = session or requests.Session()
        self._base_url = f"http://{self._sensor_host}:{self._port}{self._api_prefix}"

    @property
    def base_url(self) -> str:
        return self._base_url

    def close(self) -> None:
        if self._owns_session:
            self._session.close()

    def __enter__(self) -> "ZadarWebApiClient":
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> bool:
        self.close()
        return False

    def _request(
        self,
        method: str,
        endpoint: str,
        *,
        json_body: Optional[Dict[str, Any]] = None,
        timeout_sec: Optional[float] = None,
    ) -> ApiResponse:
        url = f"{self._base_url}/{endpoint.strip('/')}"
        try:
            response = self._session.request(
                method=method,
                url=url,
                json=json_body,
                timeout=self._timeout_sec if timeout_sec is None else timeout_sec,
            )
        except requests.RequestException as error:
            return ApiResponse(
                status_code=0,
                success=False,
                json_body=None,
                error=str(error),
            )

        parsed_json: Optional[Dict[str, Any]]
        try:
            parsed = response.json() if response.content else {}
            parsed_json = parsed if isinstance(parsed, dict) else {"value": parsed}
        except ValueError:
            parsed_json = None

        return ApiResponse(
            status_code=response.status_code,
            success=200 <= response.status_code < 300,
            json_body=parsed_json,
            text_body=response.text,
        )

    def heartbeat(self) -> ApiResponse:
        return self.get_device_clock()

    def get_device_clock(self) -> ApiResponse:
        return self._request("GET", "device/clock")

    def get_device_modes(self) -> ApiResponse:
        return self._request("GET", "device/modes")

    def get_sensor_info(self) -> ApiResponse:
        return self._request("GET", "device/system/sensor_info")

    def get_device_ip_address(self) -> ApiResponse:
        return self.get_configured_device_ip_address()

    def get_configured_device_ip_address(self) -> ApiResponse:
        return self._request("GET", "system/network/ipv4/address")

    def set_device_ip_address_static(self, ip_address: str) -> ApiResponse:
        return self.set_configured_device_ip_address_static(ip_address)

    def set_configured_device_ip_address_static(self, ip_address: str) -> ApiResponse:
        return self._request(
            "PUT",
            "system/network/ipv4/address",
            json_body={"ip_address": ip_address},
        )

    def set_device_ip_address_dhcp(self) -> ApiResponse:
        return self.reset_configured_device_ip_address()

    def reset_configured_device_ip_address(self) -> ApiResponse:
        return self._request("DELETE", "system/network/ipv4/address")

    def get_current_device_ip_address(self) -> ApiResponse:
        return self._request("GET", "device/network/ipv4/address")

    def get_output_destination_ip_address(self) -> ApiResponse:
        return self._request("GET", "system/output_destination/ipaddress")

    def set_output_destination_ip_address(self, ip_address: str) -> ApiResponse:
        return self._request(
            "PUT",
            "system/output_destination/ipaddress",
            json_body={"ip_address": ip_address},
        )

    def reset_output_destination_ip_address(self) -> ApiResponse:
        return self._request("DELETE", "system/output_destination/ipaddress")

    def get_pcl_port(self) -> ApiResponse:
        return self._request("GET", "system/output_destination/pcl/port")

    def set_pcl_port(self, pcl_port: int) -> ApiResponse:
        return self._request(
            "PUT",
            "system/output_destination/pcl/port",
            json_body={"pcl_port": int(pcl_port)},
        )

    def reset_pcl_port(self) -> ApiResponse:
        return self._request("DELETE", "system/output_destination/pcl/port")

    def get_imu_port(self) -> ApiResponse:
        return self._request("GET", "system/output_destination/imu/port")

    def set_imu_port(self, imu_port: int) -> ApiResponse:
        return self._request(
            "PUT",
            "system/output_destination/imu/port",
            json_body={"imu_port": int(imu_port)},
        )

    def reset_imu_port(self) -> ApiResponse:
        return self._request("DELETE", "system/output_destination/imu/port")

    def get_running_mode(self, *, timeout_sec: float = 1.0) -> ApiResponse:
        return self._request("GET", "device/running_mode", timeout_sec=timeout_sec)

    def set_running_mode(self, mode: int) -> ApiResponse:
        return self._request(
            "POST",
            "device/running_mode",
            json_body={"mode": int(mode)},
        )

    def stop_running_mode(self) -> ApiResponse:
        return self._request("POST", "device/running_mode/stop")

    def get_startup_mode(self) -> ApiResponse:
        return self._request("GET", "system/startup_mode")

    def set_startup_mode(self, mode: int) -> ApiResponse:
        return self._request(
            "PUT",
            "system/startup_mode",
            json_body={"mode": int(mode)},
        )

    def reset_startup_mode(self) -> ApiResponse:
        return self._request("DELETE", "system/startup_mode")

    def get_ptp_sync(self) -> ApiResponse:
        return self.get_ptp_sync_status()

    def get_ptp_sync_status(self) -> ApiResponse:
        return self._request("GET", "device/ptp_sync")

    def get_ptp_mode(self) -> ApiResponse:
        return self._request("GET", "system/ptp/mode")

    def set_ptp_mode(self, ptp_mode: str) -> ApiResponse:
        return self._request(
            "PUT",
            "system/ptp/mode",
            json_body={"ptp_mode": ptp_mode},
        )

    def get_ptp_sync_accuracy(self) -> ApiResponse:
        return self._request("GET", "system/ptp/sync_accuracy")

    def set_ptp_sync_accuracy(self, sync_accuracy: int) -> ApiResponse:
        return self._request(
            "PUT",
            "system/ptp/sync_accuracy",
            json_body={"sync_accuracy": int(sync_accuracy)},
        )

    def get_ptp_trigger_offset(self) -> ApiResponse:
        return self._request("GET", "system/ptp/trigger_offset")

    def set_ptp_trigger_offset(self, trigger_offset: int) -> ApiResponse:
        return self._request(
            "PUT",
            "system/ptp/trigger_offset",
            json_body={"trigger_offset": int(trigger_offset)},
        )

    def get_diagnostics(self, *, timeout_sec: float = 10.0) -> ApiResponse:
        return self._request(
            "GET",
            "device/system/diagnostics",
            timeout_sec=timeout_sec,
        )

    def reboot(self) -> ApiResponse:
        return self._request("PUT", "device/reboot")
