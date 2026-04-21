# zadar_udp_driver_py

`zadar_udp_driver_py` is the ROS 2 Python driver for Zadar UDP-based
sensors.

The node consumes the shared UDP SDK under `sdk/python`
to keep the ROS layer thin and aligned with the examples interfaces.

## Build

Inside a ROS 2 environment:

```bash
source /opt/ros/<ros-distro>/setup.bash
cd ros2
colcon build --base-paths src --packages-select zadar_msgs zadar_udp_driver_py zadar_udp_driver --symlink-install
source install/setup.bash
```

## Launch

```bash
ros2 launch zadar_udp_driver_py driver.launch.py
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

Default stream ports:

- radar data: `7777`
- IMU data: `36636`

The installed launch file includes:

- a default parameter file at `config/driver.yaml`
- `sensor_name` support for layouts such as `front` and `rear`
- `sensor_hostname` for sensor-managed launch
- `host_ip` as an optional managed-mode override for the host interface address
- `udp_bind_address` as the preferred bind parameter
- `bind_address` as a compatibility alias
- `record.launch.py` for rosbag2 capture
- `replay.launch.py` for rosbag2 playback
- implementation selection through `driver_package` and `driver_executable`

The shared launch files default to the C++ driver. To run the Python driver,
override `driver_package` and `driver_executable`.

For ROS 2 topic recording, `rosbag2` is the standard format. The default
storage backend is `sqlite3`, which produces `.db3` data files. `mcap` is also
commonly used when the storage plugin is available. Packet-level formats such
as `pcap` are better treated as a separate raw-capture workflow.

## Published Topics

- `points` (`sensor_msgs/PointCloud2`)
- `clusters` (`zadar_msgs/ZadarClusters`)
- `tracks` (`zadar_msgs/ZadarTracks`)
- `odometry` (`zadar_msgs/ZadarOdometry`)
- `imu` (`sensor_msgs/Imu`)

With the default namespace, these resolve to:

- `/zadar/points`
- `/zadar/clusters`
- `/zadar/tracks`
- `/zadar/odometry`
- `/zadar/imu`

With `namespace:=zadar` and `sensor_name:=front`, they resolve to:

- `/zadar/front/points`
- `/zadar/front/clusters`
- `/zadar/front/tracks`
- `/zadar/front/odometry`
- `/zadar/front/imu`

## Validation Commands

Live driver:

```bash
ros2 launch zadar_udp_driver_py driver.launch.py \
  namespace:=zadar \
  sensor_name:=front \
  sensor_hostname:=192.168.0.10 \
  running_mode:=1
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

Inspect the bag:

```bash
ros2 bag info front_drive_001
```

Replay:

```bash
ros2 launch zadar_udp_driver_py replay.launch.py \
  bag_file:=front_drive_001
```

Run the Python implementation explicitly:

```bash
ros2 launch zadar_udp_driver_py driver.launch.py \
  driver_package:=zadar_udp_driver_py \
  driver_executable:=zadar_udp_driver \
  namespace:=zadar \
  sensor_name:=front \
  sensor_hostname:=192.168.0.10 \
  running_mode:=1
```
