# Python HTTP API

The Python offering provides direct access to supported sensor HTTP API control
endpoints.

Reference:

- [`docs/webapi_reference.md`](../../../docs/webapi_reference.md)

## Requirements

- Python 3.8 or newer
- `requests`

Install `requests` if needed:

```bash
python3 -m pip install requests
```

## Examples

Sensor information:

```bash
python3 examples/python/zadar_webapi/sensor_info_example.py \
  --sensor-host 192.168.0.10
```

Network and output settings:

```bash
python3 examples/python/zadar_webapi/network_info_example.py \
  --sensor-host 192.168.0.10
```

Start or stop a running mode:

```bash
python3 examples/python/zadar_webapi/start_stop_mode_example.py \
  --sensor-host 192.168.0.10 \
  --mode 1
```

The HTTP API examples assume the default sensor HTTP API port `8080`.

Inspect or update startup mode:

```bash
python3 examples/python/zadar_webapi/startup_mode_example.py \
  --sensor-host 192.168.0.10 \
  --mode 1
```

Configure output destination and UDP ports:

```bash
python3 examples/python/zadar_webapi/configure_output_example.py \
  --sensor-host 192.168.0.10 \
  --destination-ip 192.168.0.12 \
  --pcl-port 7777 \
  --imu-port 36636
```

Inspect or update PTP configuration:

```bash
python3 examples/python/zadar_webapi/ptp_configuration_example.py \
  --sensor-host 192.168.0.10
```

Download diagnostics:

```bash
python3 examples/python/zadar_webapi/diagnostics_example.py \
  --sensor-host 192.168.0.10 \
  --save-path diagnostics.txt
```

## Supported Client Coverage

The Python client covers:

- device clock and mode inspection
- running-mode start and stop
- startup-mode get, set, and reset
- configured device IP and current device IP inspection
- output destination IP configuration
- PCL and IMU UDP port configuration
- PTP synchronization status and configuration
- diagnostics download
- reboot

Administrative operations such as firmware image upload, mode-file upload or
extraction, and global configuration wipe are not included in the SDK client.
