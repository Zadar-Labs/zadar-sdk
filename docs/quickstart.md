# Quick Start

This guide gives a compact build-and-run path from the SDK root.

`imu` provides raw onboard accelerometer and gyroscope measurements from the
internal MEMS sensor. It is intended for low-level inspection and installation
validation, and it is not a GNSS/INS output. No GNSS/GPS data is used or
required.

## 1. Python Examples

Radar data example:

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

IMU data example:

```bash
python3 examples/python/zadar_udp/imu_data_example.py \
  --port 36636 \
  --packet-limit 5
```

Radar header summary:

```bash
python3 examples/python/zadar_udp/live_frame_listener.py \
  --port 7777 \
  --frame-limit 3
```

## 2. C++ Examples (Linux)

Build:

```bash
cmake -S . -B build
cmake --build build -j$(nproc)
```

Radar example:

```bash
./build/examples/cpp/zadar_udp/radar_data_example \
  --port 7777 \
  --frame-limit 3
```

Odometry example:

```bash
./build/examples/cpp/zadar_udp/odometry_example \
  --port 7777 \
  --frame-limit 3
```

IMU example:

```bash
./build/examples/cpp/zadar_udp/imu_data_example \
  --port 36636 \
  --packet-limit 5
```

## 3. ROS 2 (Linux)

Build:

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

Validate:

```bash
ros2 topic hz /zadar/front/points
ros2 topic hz /zadar/front/imu
```

Record from a managed launch:

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

## 4. ROS 1 (Linux)

Build:

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

Validate:

```bash
rostopic hz /zadar/front/points
rostopic hz /zadar/front/imu
```

Record from a managed launch:

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

## 5. HTTP API

Sensor information:

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

Configure output destination and UDP ports:

```bash
python3 examples/python/zadar_webapi/configure_output_example.py \
  --sensor-host 192.168.0.10 \
  --destination-ip 192.168.0.12 \
  --pcl-port 7777 \
  --imu-port 36636
```

## Notes

- In receive-only mode, omitted ports resolve to `7777` for radar data and `36636` for raw IMU data.
- In sensor-managed mode, omitted ports start at the same defaults and increment together if those ports are already in use. For more context, see [SDK Manual section 3.4](../SDK_MANUAL.md#34-sensor-managed-launch).
- A common use of the raw IMU stream is installation validation, including static mounting checks from accelerometer gravity measurements.
- HTTP API examples use port `8080` by default.
