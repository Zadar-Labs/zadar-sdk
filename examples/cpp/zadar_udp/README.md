# C++ UDP Examples

The C++ examples package provides runnable applications for consuming the live
Zadar UDP radar stream and the separate raw IMU stream without ROS.

These examples are receive-only. They do not configure the sensor or start a
running mode. Use the HTTP API examples under `examples/cpp/zadar_webapi/` or
`examples/python/zadar_webapi/` first when the output destination, ports, or
running mode need to be set from software.

The separate `imu` stream contains raw onboard accelerometer and gyroscope
measurements from the internal MEMS sensor. It is intended for low-level
inspection and installation validation, and it is not a GNSS/INS output. No
GNSS/GPS data is used or required.

All examples print decoded timestamps in the host local timezone
using `YYYY-DD-MM HH:MM:SS.XXX`.

## Build

Build from the SDK root:

```bash
cmake -S . -B build
cmake --build build
```

Built example binaries are placed under:

```text
build/examples/cpp/zadar_udp/
```

## Example Binaries

- `radar_data_example`
- `clusters_example`
- `tracks_example`
- `odometry_example`
- `imu_data_example`

## Example Commands

```bash
./build/examples/cpp/zadar_udp/radar_data_example
```

```bash
./build/examples/cpp/zadar_udp/clusters_example
```

```bash
./build/examples/cpp/zadar_udp/tracks_example
```

```bash
./build/examples/cpp/zadar_udp/odometry_example
```

```bash
./build/examples/cpp/zadar_udp/imu_data_example
```

## Stream Selection

The examples are split by stream type:

- `radar_data_example`, `clusters_example`, `tracks_example`, and `odometry_example`
  expect the radar UDP stream
- `imu_data_example` expects the separate raw IMU UDP stream

Pointing a radar parser at the IMU port, or the IMU parser at the radar port,
will produce warnings because the packet layouts are different.

`clusters_example` and `tracks_example` may legitimately report zero objects if
the active stream or sensor configuration is not producing those outputs.

## Common CLI Options

Radar examples support:

- `--bind-address`
- `--port`
- `--frame-limit`

The scan, cluster, and track examples also support `--sample-count`.

The IMU example supports:

- `--bind-address`
- `--port`
- `--packet-limit`

Use `--help` on any example to view the available options. Example:

```bash
./build/examples/cpp/zadar_udp/radar_data_example --help
```

## Default Ports

- PCL / radar data: `7777`
- raw IMU data: `36636`

## Toolchain Notes

Use a protobuf development package and C++ compiler toolchain that are
ABI-compatible with each other. A system-installed `libprotobuf-dev` and
`protobuf-compiler` pair is the recommended baseline for local builds.
