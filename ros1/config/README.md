# ROS 1 Sample Configuration Files

This directory contains sample configuration files for the ROS 1 driver surface.

The sample YAML files follow the ROS driver parameter surface.

Managed single-sensor launch:

- set `sensor_hostname` to the sensor IP or hostname
- leave `data_port` and `imu_port` as `0` to let the driver choose ports
- set `running_mode` when the driver should start the sensor mode after
  configuring the output destination
- set `host_ip` only when the automatically selected host interface address
  needs to be overridden

Receive-only launch:

- leave `sensor_hostname` empty
- set `data_port` and `imu_port` to the stream ports that are already configured
  on the sensor

Default port values:

- radar / point cloud UDP: `7777`
- IMU UDP: `36636`
- HTTP API: `8080`
