# zadar_udp_driver

`zadar_udp_driver` is the ROS 2 C++ driver package for Zadar UDP-based
sensors.

It follows the same topic and parameter contract as `zadar_udp_driver_py` so
the launch surface stays consistent across the Python and C++
implementations.

Requirements:

- a ROS 2 environment with `rclcpp`, `sensor_msgs`, and `zadar_msgs`
- protobuf development headers and libraries, such as `libprotobuf-dev`
- `protoc`, such as the `protobuf-compiler` package
- `libcurl4-openssl-dev` for sensor-managed launch through the HTTP API

The C++ build regenerates its protobuf sources from `proto/ZadarFrame.proto`
using the active build environment.

Build from `/ros2` with:

```bash
source /opt/ros/<ros-distro>/setup.bash
colcon build --base-paths src --packages-select zadar_msgs zadar_udp_driver --symlink-install
source install/setup.bash
```

To run the C++ driver through the shared launch surface:

```bash
ros2 launch zadar_udp_driver_py driver.launch.py \
  namespace:=zadar \
  sensor_name:=front \
  sensor_hostname:=192.168.0.10 \
  running_mode:=1
```

The shared launch files default to `zadar_udp_driver`.

For receive-only mode, leave `sensor_hostname` empty and provide explicit
`data_port` and `imu_port` values.
