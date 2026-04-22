# zadar_udp_driver_py

`zadar_udp_driver_py` is the ROS 1 Python driver for Zadar UDP-based sensors.

The node consumes the shared UDP SDK under `sdk/python` to keep the ROS layer
thin and aligned with the examples interface.

## Build

Inside a ROS 1 environment:

```bash
source /opt/ros/<ros-distro>/setup.bash
cd ros1
catkin_make --cmake-args -DCMAKE_BUILD_TYPE=Release
source devel/setup.bash
```

## Launch

The shared ROS 1 launch files live in `zadar_udp_driver`.

Run the Python implementation explicitly with:

```bash
roslaunch zadar_udp_driver driver.launch \
  driver_package:=zadar_udp_driver_py \
  driver_executable:=zadar_udp_driver \
  namespace:=zadar \
  sensor_name:=front \
  sensor_hostname:=192.168.0.10 \
  running_mode:=1
```

Default stream ports:

- radar data: `7777`
- IMU data: `36636`

When `sensor_hostname` is omitted, the same launch surface remains available in
receive-only mode with explicit `data_port` and `imu_port` values.
