# ROS 2 Driver

This folder contains the ROS 2 frontend for Zadar UDP-based sensors, with
the following packages:

- `zadar_msgs`: custom ROS 2 messages for clusters, tracks, and odometry
- `zadar_udp_driver_py`: Python driver built on the shared UDP SDK
- `zadar_udp_driver`: C++ ROS 2 driver on the same topic and parameter contract

Launch entrypoints:

- `driver.launch.py`: live sensor mode
- `record.launch.py`: live sensor mode with rosbag2 recording
- `replay.launch.py`: rosbag2 replay mode (offline replay)

The `imu` topic contains raw onboard accelerometer and gyroscope measurements
from the internal MEMS sensor. It is intended for low-level inspection and
installation validation, and it is not a GNSS/INS topic. No GNSS/GPS data is
used or required.

## Workspace Layout

The ROS 2 packages live under:

```text
ros2/src
```

The ROS 2 implementations depend on the shared UDP SDK and protobuf schema
under:

```text
sdk/cpp
sdk/python
proto
```

The Python driver uses generated protobuf bindings under:

```text
generated/python
```

The recommended workflow is to work from the extracted SDK inside a
ROS 2 environment. Native and containerized setups are both valid when the
required dependencies are available.

## Build In A ROS 2 Environment

From the SDK root inside a ROS 2 environment:

```bash
source /opt/ros/<ros-distro>/setup.bash
cd ros2
colcon build --base-paths src --packages-select zadar_msgs zadar_udp_driver_py zadar_udp_driver --symlink-install
source install/setup.bash
```

If you move the ROS 2 packages outside the default SDK layout, set:

```bash
export ZADAR_UDP_PACKAGE_ROOT=/path/to/zadar_udp_sdk
```

## Launch

From `ros2` after sourcing the ROS 2 workspace:

```bash
ros2 launch zadar_udp_driver_py driver.launch.py
```

The shared ROS 2 launch surface defaults to the C++ driver. To run the Python
implementation instead, override `driver_package` and `driver_executable`.

### Sensor-Managed Launch

Set `sensor_hostname` when the driver should configure a specific sensor over
the HTTP API before receiving UDP data.

Example:

```bash
ros2 launch zadar_udp_driver_py driver.launch.py \
  namespace:=zadar \
  sensor_name:=front \
  sensor_hostname:=192.168.0.10 \
  running_mode:=1
```

In this mode:

- `host_ip` optionally overrides the host interface address written to the sensor
- `data_port:=0` and `imu_port:=0` mean "start from the default values"
- the driver tries `7777` and `36636` first, then increments the radar and raw IMU port pair if those ports are already in use
- if `running_mode` is omitted, the driver configures the sensor output but does not start a mode

### Receive-Only Launch

Example with explicit radar and raw IMU ports:

```bash
ros2 launch zadar_udp_driver_py driver.launch.py \
  namespace:=zadar \
  data_port:=7777 \
  imu_port:=36636
```

Set `data_port` and `imu_port` to the configured sensor stream ports if they
differ from the default values.

Recommended multi-sensor naming:

```bash
ros2 launch zadar_udp_driver_py driver.launch.py \
  namespace:=zadar \
  sensor_name:=front \
  data_port:=7777 \
  imu_port:=36636
```

For a second sensor:

```bash
ros2 launch zadar_udp_driver_py driver.launch.py \
  namespace:=zadar \
  sensor_name:=rear \
  sensor_hostname:=192.168.0.11 \
  running_mode:=1
```

If multiple sensor-managed instances are started on the same host and the ports
are omitted, each instance moves to the next available radar and raw IMU port pair.

## Record

Record live topics into a rosbag2 dataset:

```bash
ros2 launch zadar_udp_driver_py record.launch.py \
  namespace:=zadar \
  sensor_name:=front \
  sensor_hostname:=192.168.0.10 \
  running_mode:=1 \
  bag_file:=front_drive_001
```

The `bag_file` argument is the rosbag2 output directory name.

Common storage choices:

- `storage_id:=sqlite3`: default rosbag2 storage, produces `.db3` and metadata files
- `storage_id:=mcap`: commonly used alternative when the MCAP storage plugin is available

For ROS 2 topic-level record and replay, `rosbag2` is the standard convention.
Packet capture formats such as `pcap` are useful for raw sensor packet
debugging, but they are not the standard ROS 2 application-level record and
replay format.

## Replay

Replay a previously recorded rosbag2 dataset:

```bash
ros2 launch zadar_udp_driver_py replay.launch.py \
  bag_file:=front_drive_001
```

## Validation Commands

Live driver validation:

```bash
ros2 launch zadar_udp_driver_py driver.launch.py \
  namespace:=zadar \
  sensor_name:=front \
  sensor_hostname:=192.168.0.10 \
  running_mode:=1
```

In a second terminal:

```bash
ros2 node list
ros2 topic list
ros2 topic info /zadar/front/points
ros2 topic hz /zadar/front/points
ros2 topic hz /zadar/front/imu
```

Record validation:

```bash
ros2 launch zadar_udp_driver_py record.launch.py \
  namespace:=zadar \
  sensor_name:=front \
  sensor_hostname:=192.168.0.10 \
  running_mode:=1 \
  bag_file:=front_drive_001
```

After stopping the recorder:

```bash
ros2 bag info front_drive_001
```

Replay validation:

```bash
ros2 launch zadar_udp_driver_py replay.launch.py \
  bag_file:=front_drive_001
```

In a second terminal:

```bash
ros2 topic list
ros2 topic hz /zadar/front/points
ros2 topic hz /zadar/front/imu
```

## Driver Implementation Selection

The shared launch files default to the C++ driver.

To run the Python driver through the same launch surface:

```bash
ros2 launch zadar_udp_driver_py driver.launch.py \
  driver_package:=zadar_udp_driver_py \
  driver_executable:=zadar_udp_driver \
  namespace:=zadar \
  sensor_name:=front \
  data_port:=7777 \
  imu_port:=36636
```

## Parameters

Common parameters:

- `namespace`
- `sensor_name`
- `udp_bind_address`
- `host_ip`
- `sensor_hostname`
- `data_port`
- `imu_port`
- `webapi_port`
- `webapi_timeout_sec`
- `running_mode`
- `frame_id`
- `publish_scan`
- `publish_clusters`
- `publish_tracks`
- `publish_odometry`
- `publish_imu`
- `radar_socket_buffer_bytes`
- `imu_socket_buffer_bytes`
- `max_buffered_frames`
- `frame_timeout_sec`
- `socket_timeout_sec`
- `generated_python_dir`

The launch package includes a default parameter file at:

- `src/zadar_udp_driver_py/config/driver.yaml`

Default stream ports:

- `data_port:=7777`
- `imu_port:=36636`

When `sensor_hostname` is provided and one or both stream ports are left at `0`,
the driver chooses ports automatically using the same default values as the
starting point.

## Topics

With the default `namespace:=zadar`, the driver publishes:

- `/zadar/points`
- `/zadar/clusters`
- `/zadar/tracks`
- `/zadar/odometry`
- `/zadar/imu`

With `namespace:=zadar` and `sensor_name:=front`, the driver publishes:

- `/zadar/front/points`
- `/zadar/front/clusters`
- `/zadar/front/tracks`
- `/zadar/front/odometry`
- `/zadar/front/imu`

Using `sensor_name` is the recommended pattern for front, rear,
left, right, or other mounted sensor positions.

## Notes

- `points` publishes `sensor_msgs/PointCloud2`
- `imu` publishes raw onboard accelerometer and gyroscope measurements in `sensor_msgs/Imu`
- `odometry` uses `zadar_msgs/ZadarOdometry` when available
- `clusters`, `tracks`, and `odometry` use `zadar_msgs`
- the shared launch files support both the Python and C++ ROS 2 drivers
