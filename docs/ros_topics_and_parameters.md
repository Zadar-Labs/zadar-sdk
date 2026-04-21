# ROS Topics And Parameters

## Topic Namespace

The ROS drivers publish:

- `/zadar/<sensor_name>/points`
- `/zadar/<sensor_name>/imu`
- `/zadar/<sensor_name>/clusters`
- `/zadar/<sensor_name>/tracks`
- `/zadar/<sensor_name>/odometry`

Examples:

- `/zadar/front/points`
- `/zadar/rear/imu`

Using `sensor_name` keeps multi-sensor topic layouts readable and avoids
embedding numeric device IDs directly in topic names.

## Message Types

- `points`: `sensor_msgs/PointCloud2`
- `imu`: `sensor_msgs/Imu`

`imu` is the raw onboard accelerometer and gyroscope stream from the internal
MEMS sensor. It is intended for low-level inspection and installation
validation, and it is not a GNSS/INS output. No GNSS/GPS data is used or
required.

If enabled via software license, these messages will be populated:
- `odometry`: `zadar_msgs/ZadarOdometry`
- `clusters`: `zadar_msgs/ZadarClusters`
- `tracks`: `zadar_msgs/ZadarTracks`

## Launch Modes

The ROS drivers support two launch modes.

Receive-only mode:

- leave `sensor_hostname` empty
- the driver only listens for UDP traffic
- no HTTP API calls are made

Sensor-managed mode:

- set `sensor_hostname` to the sensor IP or hostname
- the driver configures the sensor over the HTTP API before listening
- if `running_mode` is provided, the driver starts that mode after configuring
  the sensor output

## Driver Parameters

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
- `publish_imu`
- `publish_clusters`
- `publish_tracks`
- `publish_odometry`
- `radar_socket_buffer_bytes`
- `imu_socket_buffer_bytes`
- `max_buffered_frames`
- `frame_timeout_sec`
- `socket_timeout_sec`

Parameter behavior:

- `sensor_hostname`: when set, the driver enters sensor-managed mode
- `host_ip`: optional host interface address to program into the sensor in
  sensor-managed mode
- `udp_bind_address`: local bind address in receive-only mode; optional
  interface override in sensor-managed mode
- `data_port`: radar UDP destination port; `0` means use the default or the
  next available managed port
- `imu_port`: raw IMU UDP destination port; `0` means use the default or the
  next available managed port
- `running_mode`: optional sensor mode to start after HTTP API configuration

## Managed Port Selection

In sensor-managed mode:

- if neither port is provided, the driver tries `7777` and `36636`
- if that pair is busy, it tries `7778` and `36637`, then the next pair, and so on
- if only one port is provided, that port stays fixed and the other one is
  chosen from its default upward
- if both ports are provided, those exact values are used

In receive-only mode:

- omitted radar and raw IMU ports resolve to `7777` and `36636`
- the driver does not change the sensor configuration

## Sensor IP And Hostname

In sensor-managed mode, `sensor_hostname` identifies the sensor for HTTP API
control-plane operations.

`host_ip` and `udp_bind_address` affect the host side differently:

- `host_ip`: the destination IP written to the sensor
- `udp_bind_address`: the local listener bind address

When `host_ip` is not provided, the driver chooses the host IP that routes to
the sensor. If `udp_bind_address` is left empty or set to a wildcard address in
sensor-managed mode, the driver binds to that same chosen host IP.

## Multi-Sensor Implication

If multiple sensors stream to the same host, they should not be configured to
send radar and raw IMU traffic to the same local UDP ports unless packet mixing is
intentional.

The recommended pattern is:

- assign each sensor its own radar UDP port
- assign each sensor its own raw IMU UDP port
- give each running driver instance its own `sensor_name`

When multiple managed single-sensor driver instances are started on the same
host and the ports are omitted, each instance will move to the next available
radar and raw IMU port pair.

Example:

- sensor `192.168.0.10` streams to host ports `7777` and `36636`
- sensor `192.168.0.11` streams to host ports `7778` and `36637`
- run one driver instance with `sensor_name:=front`
- run another driver instance with `sensor_name:=rear`
