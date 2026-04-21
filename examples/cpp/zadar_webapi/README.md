# C++ HTTP API

The C++ offering provides direct access to supported sensor HTTP API control
endpoints.

Reference:

- [`docs/webapi_reference.md`](../../../docs/webapi_reference.md)

## Requirements

- C++17 compiler
- `libcurl`

Build from the SDK root:

```bash
cmake -S . -B build
cmake --build build -j$(nproc)
```

If `libcurl` is not available, the default CMake configure step fails with a
message telling the user to install `libcurl4-openssl-dev`.

If a customer intentionally wants a UDP-only C++ build, they can disable the
C++ HTTP API surface explicitly:

```bash
cmake -S . -B build -DZADAR_BUILD_WEBAPI_CPP=OFF
cmake --build build -j$(nproc)
```

## Examples

Sensor information:

```bash
./build/examples/cpp/zadar_webapi/sensor_info_example \
  --sensor-host 192.168.0.10
```

Network and output settings:

```bash
./build/examples/cpp/zadar_webapi/network_info_example \
  --sensor-host 192.168.0.10
```

Start or stop a running mode:

```bash
./build/examples/cpp/zadar_webapi/start_stop_mode_example \
  --sensor-host 192.168.0.10 \
  --mode 1
```

The HTTP API examples assume the default sensor HTTP API port `8080`.

Inspect or update startup mode:

```bash
./build/examples/cpp/zadar_webapi/startup_mode_example \
  --sensor-host 192.168.0.10 \
  --mode 1
```

Configure output destination and UDP ports:

```bash
./build/examples/cpp/zadar_webapi/configure_output_example \
  --sensor-host 192.168.0.10 \
  --destination-ip 192.168.0.12 \
  --pcl-port 7777 \
  --imu-port 36636
```

Inspect or update PTP configuration:

```bash
./build/examples/cpp/zadar_webapi/ptp_configuration_example \
  --sensor-host 192.168.0.10
```

Download diagnostics:

```bash
./build/examples/cpp/zadar_webapi/diagnostics_example \
  --sensor-host 192.168.0.10 \
  --timeout-ms 10000
```

## Supported Client Coverage

The C++ client covers:

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
