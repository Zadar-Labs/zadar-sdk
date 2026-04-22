# zadar_udp_driver

`zadar_udp_driver` is the ROS 1 C++ driver package for Zadar UDP-based
sensors.

It provides the main ROS 1 launch surface:

- `driver.launch`
- `record.launch`
- `replay.launch`

The shared launch files default to `zadar_udp_driver`. The Python
implementation remains available through `driver_package` and
`driver_executable` overrides.

## Build

From `ros1` inside a ROS 1 environment:

```bash
source /opt/ros/<ros-distro>/setup.bash
catkin_make --cmake-args -DCMAKE_BUILD_TYPE=Release
source devel/setup.bash
```

## Launch

Run the default C++ driver:

```bash
roslaunch zadar_udp_driver driver.launch \
  namespace:=zadar \
  sensor_name:=front \
  sensor_hostname:=192.168.0.10 \
  running_mode:=1
```

Run the Python implementation through the same launch surface:

```bash
roslaunch zadar_udp_driver driver.launch \
  driver_package:=zadar_udp_driver_py \
  driver_executable:=zadar_udp_driver \
  namespace:=zadar \
  sensor_name:=front \
  sensor_hostname:=192.168.0.10 \
  running_mode:=1
```

For `record.launch` and `replay.launch`, relative `bag_file` values are
resolved from the directory where `roslaunch` is invoked.

For receive-only mode, leave `sensor_hostname` empty and provide the explicit
radar and IMU stream ports instead.
