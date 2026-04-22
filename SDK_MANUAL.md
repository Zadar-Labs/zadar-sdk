# Zadar Ethernet Sensor SDK Manual

This manual is the single-document guide for the Zadar Ethernet Sensor SDK.

It covers the complete SDK offering for supported Ethernet-based
Zadar sensors:

- `zPRIME2.0`
- `zPRIME3.0`
- `zPULSE`

## 1. Package Overview

The SDK provides three main path surfaces plus the shared SDK packages:

- `examples/`: direct UDP and HTTP API examples in Python and C++
- `ros1/`: ROS 1 drivers, launch files, recording, and replay
- `ros2/`: ROS 2 drivers, launch files, recording, and replay

Supporting package areas include:

- `proto/`: canonical protobuf schema
- `generated/`: shipped protobuf bindings
- `sdk/`: shared `zadar_udp` and `zadar_webapi` packages for Python and C++
- `ros1/config/` and `ros2/config/`: sample configuration files
- `scripts/`: helper scripts such as protobuf regeneration

## 2. Getting Started

Recommended reading order:

1. Review `docs/supported_environments.md`
2. Start with the network model in this manual
3. Validate live UDP data with `examples/`
4. Move to the `zadar_webapi` examples when sensor configuration or control is needed
5. Use `ros2/` or `ros1/` for production middleware integration

At the SDK root, the most common defaults are:

- radar / point cloud UDP port: `7777`
- raw IMU UDP port: `36636`
- HTTP API port: `8080`

IMU output:

- `imu` provides raw onboard accelerometer and gyroscope measurements from the internal MEMS sensor.
- It is intended for low-level inspection and installation validation, including static mounting checks from accelerometer gravity measurements.
- It is not a GNSS/INS output, and no GNSS/GPS data is used or required.

Environment and dependency guidance:

- [docs/supported_environments.md](docs/supported_environments.md)

## 3. Network Model

The UDP data path supports two operating styles:

- receive-only mode
- sensor-managed mode

Receive-only mode binds a local interface, listens on UDP ports, and decodes
all valid Zadar traffic that arrives on those ports.

Sensor-managed mode uses the HTTP API to configure a specific sensor first, then
starts the UDP listener on the selected ports.

### 3.1 Local Bind Address

`udp_bind_address` or `--bind-address` selects the local interface on the host.

Common values:

- `0.0.0.0`: listen on all local interfaces
- a specific host IP such as `192.168.0.12`: listen only on that interface

### 3.2 Sensor IP vs Local Port

Two different concepts matter here:

- sensor IP: the address of the radar itself, for example `192.168.0.11`
- local UDP port: the port on your host computer that receives the sensor UDP stream

In receive-only mode, the local port is what selects the incoming stream. The
source sensor IP is not used as the primary selection mechanism.

### 3.3 Multiple Sensors On One Host

Assume:

- sensor A: `192.168.0.10`
- sensor B: `192.168.0.11`

If both sensors are configured to stream to the same host IP and the same local radar
and raw IMU ports, their packets will arrive at the same listener and will be indistinguishable.
That is not the intended deployment model.

Recommended multi-sensor setup:

- give each sensor a unique radar UDP destination port
- give each sensor a unique raw IMU UDP destination port
- run one driver instance per sensor
- assign each instance a unique `sensor_name`

Example:

- sensor A outputs radar to host port `7777` and raw IMU to `36636`
- sensor B outputs radar to host port `7778` and raw IMU to `36637`

Then run:

```bash
ros2 launch zadar_udp_driver_py driver.launch.py \
  namespace:=zadar \
  sensor_name:=front \
  data_port:=7777 \
  imu_port:=36636
```

and:

```bash
ros2 launch zadar_udp_driver_py driver.launch.py \
  namespace:=zadar \
  sensor_name:=rear \
  data_port:=7778 \
  imu_port:=36637
```

The same pattern applies to ROS 1 and to the example tools. Refer to [docs/quickstart.md](docs/quickstart.md) for other examples.

### 3.4 Sensor-Managed Launch

When `sensor_hostname` is provided in the ROS drivers, the SDK enters
sensor-managed mode.

In that mode the driver:

1. determines the host IP to program into the sensor
2. chooses radar and raw IMU destination ports
3. configures those settings over the HTTP API
4. optionally starts `running_mode`
5. listens on the selected UDP ports

Port rules:

- if both ports are omitted, the driver tries `7777` and `36636`
- if that pair is already in use, the driver tries `7778` and `36637`, then the next pair
- if one port is provided, that port stays fixed and the other one is chosen from its default upward
- if both ports are provided, those exact values are used

`host_ip` optionally overrides the host interface address written to the
sensor. When `host_ip` is omitted, the driver chooses the local IP that routes
to the sensor. If `udp_bind_address` is left empty or set to a wildcard address
in sensor-managed mode, the driver binds to that same selected host IP.

## 4. Example Usage

Use the example tools first when validating a sensor or a network setup.

### 4.1 Python

Radar example:

```bash
python3 examples/python/zadar_udp/radar_data_example.py \
  --port 7777 \
  --frame-limit 3
```

Odometry example:

```bash
python3 examples/python/zadar_udp/odometry_example.py \
  --port 7777 \
  --frame-limit 3
```

IMU example:

```bash
python3 examples/python/zadar_udp/imu_data_example.py \
  --port 36636 \
  --packet-limit 5
```

Raw radar frame summary:

```bash
python3 examples/python/zadar_udp/live_frame_listener.py \
  --port 7777 \
  --frame-limit 3
```

### 4.2 C++

Build:

```bash
cmake -S . -B build
cmake --build build -j$(nproc)
```

Run:

```bash
./build/examples/cpp/zadar_udp/radar_data_example \
  --port 7777 \
  --frame-limit 3
```

```bash
./build/examples/cpp/zadar_udp/odometry_example \
  --port 7777 \
  --frame-limit 3
```

```bash
./build/examples/cpp/zadar_udp/imu_data_example \
  --port 36636 \
  --packet-limit 5
```

### 4.3 Example Use Cases

- validate that UDP packets are reaching the host
- inspect points, clusters, tracks, odometry, and raw IMU output
- confirm port assignments before using ROS
- build custom non-ROS applications on the shared SDK

## 5. HTTP API Usage

Use the `zadar_webapi` examples when you need to talk to a specific sensor
over HTTP.

HTTP API example coverage includes:

- sensor information and status
- running mode start and stop
- destination IP configuration
- radar and raw IMU UDP port configuration
- startup mode configuration
- PTP status and configuration
- diagnostics download
- reboot control

Python example:

```bash
python3 examples/python/zadar_webapi/sensor_info_example.py \
  --sensor-host 192.168.0.10
```

Running mode example:

```bash
python3 examples/python/zadar_webapi/start_stop_mode_example.py \
  --sensor-host 192.168.0.10 \
  --mode 1
```

Output configuration example:

```bash
python3 examples/python/zadar_webapi/configure_output_example.py \
  --sensor-host 192.168.0.10 \
  --destination-ip 192.168.0.12 \
  --pcl-port 7777 \
  --imu-port 36636
```

This is the correct surface to use when the software needs to act on a specific
sensor IP.

HTTP API reference:

- [docs/webapi_reference.md](docs/webapi_reference.md)

Administrative operations such as firmware image upload, mode-file upload or
extraction, and global configuration wipe are intentionally outside the SDK
HTTP API layer.

## 6. ROS 2 Usage

Build inside a ROS 2 environment:

```bash
cd ros2
colcon build --base-paths src --packages-select zadar_msgs zadar_udp_driver_py zadar_udp_driver --symlink-install
source install/setup.bash
```

Sensor-managed launch:

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

Validation:

```bash
ros2 topic hz /zadar/front/points
ros2 topic hz /zadar/front/imu
```

Record:

```bash
ros2 launch zadar_udp_driver_py record.launch.py \
  namespace:=zadar \
  sensor_name:=front \
  sensor_hostname:=192.168.0.10 \
  running_mode:=1 \
  bag_file:=front_drive_001
```

Replay:

```bash
ros2 launch zadar_udp_driver_py replay.launch.py \
  bag_file:=front_drive_001
```

## 7. ROS 1 Usage

Build inside a ROS 1 environment:

```bash
cd ros1
catkin_make --cmake-args -DCMAKE_BUILD_TYPE=Release
source devel/setup.bash
```

Sensor-managed launch:

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

Validation:

```bash
rostopic hz /zadar/front/points
rostopic hz /zadar/front/imu
```

Record:

```bash
roslaunch zadar_udp_driver record.launch \
  namespace:=zadar \
  sensor_name:=front \
  sensor_hostname:=192.168.0.10 \
  running_mode:=1 \
  bag_file:=front_drive_001
```

Replay:

```bash
roslaunch zadar_udp_driver replay.launch \
  bag_file:=front_drive_001.bag
```

## 8. Topic Layout

The drivers publish:

- `/zadar/<sensor_name>/points`
- `/zadar/<sensor_name>/imu`
- `/zadar/<sensor_name>/clusters`
- `/zadar/<sensor_name>/tracks`
- `/zadar/<sensor_name>/odometry`

Examples:

- `/zadar/front/points`
- `/zadar/rear/imu`

## 9. Parameter Summary

Common driver parameters include:

- `udp_bind_address`
- `host_ip`
- `sensor_hostname`
- `data_port`
- `imu_port`
- `webapi_port`
- `webapi_timeout_sec`
- `running_mode`
- `frame_id`
- `sensor_name`
- `publish_scan`
- `publish_imu`
- `publish_clusters (if your radar has an active clustering license)`
- `publish_tracks (if your radar has an active tracking license)`
- `publish_odometry (if your radar has an active odometry license)`
- `radar_socket_buffer_bytes`
- `imu_socket_buffer_bytes`
- `max_buffered_frames`
- `frame_timeout_sec`
- `socket_timeout_sec`

`sensor_hostname` switches the ROS drivers from receive-only mode into
sensor-managed mode.

## 10. Record And Replay

ROS 2 uses `rosbag2` as the standard record and replay path.

ROS 1 uses `rosbag`.

The record and replay modes operate at the ROS topic level, not as raw
UDP packet capture or raw UDP packet replay.

## 11. Troubleshooting

If no data appears:

- in sensor-managed mode, confirm the sensor is reachable over the HTTP API
- confirm the sensor is configured to stream to the correct host IP
- confirm the radar and IMU destination ports match the listener settings
- confirm the correct local interface is selected with `udp_bind_address` or `--bind-address`
- validate with the example tools before ROS

If multiple sensors are connected:

- do not point multiple sensors at the same host ports
- assign per-sensor radar and IMU destination ports
- run one driver instance per sensor
- use `sensor_name` to separate the topic trees

If control or configuration is needed:

- use the sensor-managed ROS launch mode, or use the `zadar_webapi` examples directly with the sensor IP or hostname
