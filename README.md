# Zadar Ethernet Sensor SDK

## Build Status

| Surface | Build Status |
| --- | --- |
| ROS 1 Legacy: `noetic` (Ubuntu 20.04) | [![ROS 1](https://github.com/Zadar-Labs/zadar-sdk/actions/workflows/ros1.yml/badge.svg)](https://github.com/Zadar-Labs/zadar-sdk/actions/workflows/ros1.yml) |
| ROS 2 Stable / LTS: `humble` (Ubuntu 22.04), `jazzy` (Ubuntu 24.04) | [![ROS 2 Humble](https://github.com/Zadar-Labs/zadar-sdk/actions/workflows/ros2-humble.yml/badge.svg)](https://github.com/Zadar-Labs/zadar-sdk/actions/workflows/ros2-humble.yml) [![ROS 2 Jazzy](https://github.com/Zadar-Labs/zadar-sdk/actions/workflows/ros2-jazzy.yml/badge.svg)](https://github.com/Zadar-Labs/zadar-sdk/actions/workflows/ros2-jazzy.yml) |
| ROS 2 Current / Forward: `kilted` (Ubuntu 24.04), `rolling` (Ubuntu 24.04) | [![ROS 2 Kilted](https://github.com/Zadar-Labs/zadar-sdk/actions/workflows/ros2-kilted.yml/badge.svg)](https://github.com/Zadar-Labs/zadar-sdk/actions/workflows/ros2-kilted.yml) [![ROS 2 Rolling](https://github.com/Zadar-Labs/zadar-sdk/actions/workflows/ros2-rolling.yml/badge.svg)](https://github.com/Zadar-Labs/zadar-sdk/actions/workflows/ros2-rolling.yml) |
| C++ SDK (`ubuntu-22.04`, `ubuntu-24.04`) | [![C++](https://github.com/Zadar-Labs/zadar-sdk/actions/workflows/cpp.yml/badge.svg)](https://github.com/Zadar-Labs/zadar-sdk/actions/workflows/cpp.yml) |
| Python SDK (`ubuntu-22.04`, `ubuntu-24.04`; Python `3.8`, `3.10`, `3.12`) | [![Python](https://github.com/Zadar-Labs/zadar-sdk/actions/workflows/python.yml/badge.svg)](https://github.com/Zadar-Labs/zadar-sdk/actions/workflows/python.yml) |

This is the SDK and driver bundle for Zadar Ethernet sensors.

Supported sensor family:

- `zPRIME2.0`
- `zPRIME3.0`
- `zPULSE`

The SDK includes:

- UDP examples in Python and C++
- ROS 1 drivers in Python and C++
- ROS 2 drivers in Python and C++
- rosbag / rosbag2 record and replay workflows
- HTTP API surface in Python and C++
- shared SDK layers for UDP transport and protobuf decoding

## Table of Contents

- [Build Status](#build-status)
- [Start Here](#start-here)
- [IMU Output](#imu-output)
- [Quick Start](#quick-start)
  - [Python Examples](#python-examples)
  - [C++ Examples](#c-examples)
- [Protobuf Generation](#protobuf-generation)
  - [ROS 2](#ros-2)
  - [ROS 1](#ros-1)
  - [HTTP API](#http-api)
- [Default Ports](#default-ports)
- [Directory Map](#directory-map)
- [Documentation](#documentation)
- [Release Assets And Support](#release-assets-and-support)

## Start Here

Choose the entrypoint that matches your integration:

- [SDK Manual](SDK_MANUAL.md)
- [Examples](examples/README.md)
- [ROS 1 Driver](ros1/README.md)
- [ROS 2 Driver](ros2/README.md)
- [HTTP API Overview](docs/webapi_overview.md)
- [Supported Environments And Dependencies](docs/supported_environments.md)
- [ROS 1 Sample Configuration](ros1/config/README.md)
- [ROS 2 Sample Configuration](ros2/config/README.md)
- [Architecture Notes](docs/architecture.md)

## IMU Output

- `imu` provides raw onboard accelerometer and gyroscope measurements from the internal MEMS sensor.
- It is intended for low-level inspection and installation validation, including static mounting checks from accelerometer gravity measurements.
- It is not a GNSS/INS output, and no GNSS/GPS data is used or required.

## Quick Start

### Python Examples

Run a live radar example from the SDK root:

```bash
python3 examples/python/zadar_udp/radar_data_example.py \
  --port 7777 \
  --frame-limit 3
```

Run an odometry example from the radar stream:

```bash
python3 examples/python/zadar_udp/odometry_example.py \
  --port 7777 \
  --frame-limit 3
```

Run the IMU example:

```bash
python3 examples/python/zadar_udp/imu_data_example.py \
  --port 36636 \
  --packet-limit 5
```

### C++ Examples

Build the shared C++ SDK and examples:

```bash
cmake -S . -B build
cmake --build build -j$(nproc)
```

Run a live radar example:

```bash
./build/examples/cpp/zadar_udp/radar_data_example \
  --port 7777 \
  --frame-limit 3
```

Run an odometry example from the radar stream:

```bash
./build/examples/cpp/zadar_udp/odometry_example \
  --port 7777 \
  --frame-limit 3
```

Run the IMU example when raw onboard accelerometer and gyroscope packets are needed:

```bash
./build/examples/cpp/zadar_udp/imu_data_example \
  --port 36636 \
  --packet-limit 5
```

## Protobuf Generation

The SDK already ships generated protobuf bindings under `generated/`, so most
customers do not need to run `scripts/build_proto.sh`.

Use `scripts/build_proto.sh` only when:

- `proto/ZadarFrame.proto` has been changed
- generated protobuf files are missing
- protobuf version compatibility requires regenerated outputs

### ROS 2

Build inside a ROS 2 environment:

```bash
cd ros2
colcon build --base-paths src --packages-select zadar_msgs zadar_udp_driver_py zadar_udp_driver --symlink-install
source install/setup.bash
```

Managed single-sensor launch:

```bash
ros2 launch zadar_udp_driver_py driver.launch.py \
  namespace:=zadar \
  sensor_name:=front \
  sensor_hostname:=192.168.0.10 \
  running_mode:=1
```

Receive-only launch:

```bash
ros2 launch zadar_udp_driver_py driver.launch.py \
  namespace:=zadar \
  sensor_name:=front \
  data_port:=7777 \
  imu_port:=36636
```

### ROS 1

Build inside a ROS 1 environment:

```bash
cd ros1
catkin_make --cmake-args -DCMAKE_BUILD_TYPE=Release
source devel/setup.bash
```

Managed single-sensor launch:

```bash
roslaunch zadar_udp_driver driver.launch \
  namespace:=zadar \
  sensor_name:=front \
  sensor_hostname:=192.168.0.10 \
  running_mode:=1
```

Receive-only launch:

```bash
roslaunch zadar_udp_driver driver.launch \
  namespace:=zadar \
  sensor_name:=front \
  data_port:=7777 \
  imu_port:=36636
```

### HTTP API

Inspect sensor information over the HTTP API:

```bash
python3 examples/python/zadar_webapi/sensor_info_example.py \
  --sensor-host 192.168.0.10
```

Start or stop a running mode:

```bash
python3 examples/python/zadar_webapi/start_stop_mode_example.py \
  --sensor-host 192.168.0.10 \
  --mode 1
```

## Default Ports

Default stream ports:

- radar / point cloud UDP: `7777`
- raw IMU UDP: `36636`
- HTTP API: `8080`

If `data_port` and `imu_port` are omitted in receive-only mode, the driver
listens on these defaults.

If `sensor_hostname` is provided, the driver configures the sensor through the
HTTP API. In that managed mode:

- omitted ports start at `7777` and `36636`
- if those ports are already in use, the driver increments the radar and raw
  IMU port pair together until an available pair is found
- explicit port values are kept as provided

## Directory Map

- `docs/`: documentation
- `proto/`: canonical protobuf schema
- `generated/`: generated protobuf bindings shipped with the package
- `sdk/`: shared UDP and HTTP API SDK packages for Python and C++
- `examples/`: direct UDP and HTTP API examples for Python and C++
- `ros1/`: ROS 1 workspace, packages, and launch files
- `ros2/`: ROS 2 workspace, packages, and launch files
- `ros1/config/` and `ros2/config/`: sample sensor and driver configuration files
- `scripts/`: helper scripts such as protobuf generation

## Documentation

For a fuller walkthrough, see:

- [SDK Manual](SDK_MANUAL.md)
- [Quick Start Guide](docs/quickstart.md)
- [Supported Environments And Dependencies](docs/supported_environments.md)
- [ROS Topics And Parameters](docs/ros_topics_and_parameters.md)
- [Architecture](docs/architecture.md)

## Release Assets And Support

- Download the packaged `.zip` and `.tar.gz` bundles from [Releases](https://github.com/Zadar-Labs/zadar-sdk/releases).
- Track public release history in [CHANGELOG.md](CHANGELOG.md).
- For licensing or evaluation access, contact `support-team@zadarlabs.com`.
