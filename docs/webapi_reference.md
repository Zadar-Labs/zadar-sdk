# HTTP API Reference

This reference covers the sensor HTTP API endpoints exposed through the SDK
clients.

The SDK includes the operational control path used for sensor inspection,
network configuration, output routing, running-mode control, startup behavior,
PTP configuration, diagnostics, and reboot.

The ROS 1 and ROS 2 sensor-managed launch flows use the same client methods for
destination IP selection, UDP port configuration, and optional mode start.

The SDK does not expose firmware image upload, mode-file upload or extraction,
or global configuration wipe operations.

The `imu` endpoints below configure the raw onboard accelerometer and
gyroscope output from the internal MEMS sensor. It is intended for low-level
inspection and installation validation, and it is not a GNSS/INS output. No
GNSS/GPS data is used or required.

## Defaults

- HTTP API port: `8080`
- API prefix: `/api/v1`

## Endpoint Table

| Method | Path | SDK Client Method | Purpose |
| --- | --- | --- | --- |
| `GET` | `/device/clock` | `get_device_clock()` | Retrieve the device clock timestamp. |
| `GET` | `/device/modes` | `get_device_modes()` | List the available running modes. |
| `GET` | `/device/running_mode` | `get_running_mode()` | Inspect the active running mode and device status. |
| `POST` | `/device/running_mode` | `set_running_mode(mode)` | Start a running mode. |
| `POST` | `/device/running_mode/stop` | `stop_running_mode()` | Stop the active mode and return to idle. |
| `GET` | `/system/startup_mode` | `get_startup_mode()` | Read the configured startup mode override. |
| `PUT` | `/system/startup_mode` | `set_startup_mode(mode)` | Set the startup mode override. |
| `DELETE` | `/system/startup_mode` | `reset_startup_mode()` | Remove the startup mode override. |
| `GET` | `/device/system/sensor_info` | `get_sensor_info()` | Read firmware, serial number, and sensor family information. |
| `GET` | `/device/system/diagnostics` | `get_diagnostics()` | Download diagnostic text from the sensor. |
| `PUT` | `/device/reboot` | `reboot()` | Reboot the sensor after the HTTP response is returned. |
| `GET` | `/system/network/ipv4/address` | `get_configured_device_ip_address()` | Read the configured device IP override. |
| `PUT` | `/system/network/ipv4/address` | `set_configured_device_ip_address_static(ip)` | Set a configured device IP override. |
| `DELETE` | `/system/network/ipv4/address` | `reset_configured_device_ip_address()` | Remove the configured device IP override. |
| `GET` | `/device/network/ipv4/address` | `get_current_device_ip_address()` | Read the device's active network IP. |
| `GET` | `/system/output_destination/ipaddress` | `get_output_destination_ip_address()` | Read the configured UDP destination IP. |
| `PUT` | `/system/output_destination/ipaddress` | `set_output_destination_ip_address(ip)` | Set the UDP destination IP. |
| `DELETE` | `/system/output_destination/ipaddress` | `reset_output_destination_ip_address()` | Remove the UDP destination IP override. |
| `GET` | `/system/output_destination/pcl/port` | `get_pcl_port()` | Read the configured radar / PCL UDP port. |
| `PUT` | `/system/output_destination/pcl/port` | `set_pcl_port(port)` | Set the radar / PCL UDP port. |
| `DELETE` | `/system/output_destination/pcl/port` | `reset_pcl_port()` | Remove the radar / PCL port override. |
| `GET` | `/system/output_destination/imu/port` | `get_imu_port()` | Read the configured raw IMU UDP port. |
| `PUT` | `/system/output_destination/imu/port` | `set_imu_port(port)` | Set the raw IMU UDP port. |
| `DELETE` | `/system/output_destination/imu/port` | `reset_imu_port()` | Remove the raw IMU port override. |
| `GET` | `/device/ptp_sync` | `get_ptp_sync_status()` | Read PTP synchronization state and quality. |
| `GET` | `/system/ptp/mode` | `get_ptp_mode()` | Read the configured PTP mode. |
| `PUT` | `/system/ptp/mode` | `set_ptp_mode(mode)` | Set the configured PTP mode. |
| `GET` | `/system/ptp/sync_accuracy` | `get_ptp_sync_accuracy()` | Read the configured PTP sync accuracy. |
| `PUT` | `/system/ptp/sync_accuracy` | `set_ptp_sync_accuracy(value)` | Set the configured PTP sync accuracy. |
| `GET` | `/system/ptp/trigger_offset` | `get_ptp_trigger_offset()` | Read the configured PTP trigger offset. |
| `PUT` | `/system/ptp/trigger_offset` | `set_ptp_trigger_offset(value)` | Set the configured PTP trigger offset. |

## Common Workflows

### Inspect Sensor State

Use this flow to confirm that the sensor is reachable and to inspect its mode,
identity, and network state.

Typical calls:

- `get_device_clock()`
- `get_sensor_info()`
- `get_device_modes()`
- `get_running_mode()`
- `get_current_device_ip_address()`
- `get_configured_device_ip_address()`

`get_current_device_ip_address()` returns the active IP address on the running
sensor. `get_configured_device_ip_address()` when a new IP address is configured, the saved IP address is reflected here. The actual active IP of the sensor will not change until the sensor is rebooted. Thus, the above two values can differ.

### Configure UDP Output

Use this flow before starting a UDP example or ROS listener.

The IMU port configures the raw onboard accelerometer and gyroscope stream.

- `set_output_destination_ip_address(host_ip)`
- `set_pcl_port(7777)`
- `set_imu_port(36636)`
- `get_output_destination_ip_address()`
- `get_pcl_port()`
- `get_imu_port()`

### Start Or Stop Data Streaming

Use this flow to switch the sensor into a running mode or to stop it.

- `set_running_mode(mode)`
- `get_running_mode()`
- `stop_running_mode()`

### Configure Startup Behavior

Use startup mode when the device should boot directly into a selected mode.

- `get_startup_mode()`
- `set_startup_mode(mode)`
- `reset_startup_mode()`

### Inspect Or Update PTP Settings

Use these endpoints when the deployment relies on PTP network time synchronization (IEEE 1588v2 or gPTP).

- `get_ptp_sync_status()`
- `get_ptp_mode()`
- `set_ptp_mode(mode)`
- `get_ptp_sync_accuracy()`
- `set_ptp_sync_accuracy(value)`
- `get_ptp_trigger_offset()`
- `set_ptp_trigger_offset(value)`

## Response Notes

- Most configuration endpoints return JSON objects with a `description` field.
- Diagnostics returns plain-text content.
- Several `GET` endpoints return values as strings even when the value is
  numerically meaningful, such as UDP port values.
- `DELETE` operations remove user overrides and return the sensor to its default
  configuration behavior for that field.
