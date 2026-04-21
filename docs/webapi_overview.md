# HTTP API

This package contains helpers for the sensor HTTP API on supported Zadar
ethernet sensors.

This surface is used for:

- sensor inspection and reachability checks
- running-mode start, stop, and startup-mode configuration
- device and output network configuration
- radar / PCL and raw IMU UDP port configuration
- PTP status and configuration
- diagnostics download and reboot control

The `imu_port` setting configures the raw onboard accelerometer and gyroscope
output from the internal MEMS sensor. It is intended for low-level inspection
and installation validation, and it is not a GNSS/INS output. No GNSS/GPS data
is used or required.

Language support:

- [Python examples](../examples/python/zadar_webapi/README.md)
- [C++ examples](../examples/cpp/zadar_webapi/README.md)
- [Python SDK package](../sdk/python/zadar_webapi/README.md)
- [C++ SDK package](../sdk/cpp/zadar_webapi/README.md)

Reference:

- [HTTP API Reference](webapi_reference.md)

HTTP API defaults:

- HTTP API port: `8080`
- API base path: `/api/v1`

Common workflows:

Inspect sensor state:

```bash
python3 examples/python/zadar_webapi/sensor_info_example.py \
  --sensor-host 192.168.0.10
```

Inspect configured and active network settings:

```bash
python3 examples/python/zadar_webapi/network_info_example.py \
  --sensor-host 192.168.0.10
```

Configure output destination and UDP ports:

```bash
python3 examples/python/zadar_webapi/configure_output_example.py \
  --sensor-host 192.168.0.10 \
  --destination-ip 192.168.0.12 \
  --pcl-port 7777 \
  --imu-port 36636
```

Start or stop a running mode:

```bash
python3 examples/python/zadar_webapi/start_stop_mode_example.py \
  --sensor-host 192.168.0.10 \
  --mode 1
```

```bash
python3 examples/python/zadar_webapi/start_stop_mode_example.py \
  --sensor-host 192.168.0.10 \
  --stop
```

Inspect or update startup mode:

```bash
python3 examples/python/zadar_webapi/startup_mode_example.py \
  --sensor-host 192.168.0.10 \
  --mode 1
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

The HTTP API surface complements the UDP data listeners under:

- `examples/`
- `ros1/`
- `ros2/`

The ROS 1 and ROS 2 sensor-managed launch flows use this same HTTP API layer to
configure destination IP and UDP ports before the listeners start.

Advanced administrative operations such as firmware image upload, mode-file
upload or extraction, and global configuration wipe are intentionally excluded
from the SDK HTTP API layer.
