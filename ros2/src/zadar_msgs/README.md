# zadar_msgs

`zadar_msgs` contains ROS 2 message definitions for Zadar UDP driver outputs
that are not covered by standard ROS message types.

Supported message groups:

- `ZadarCluster` and `ZadarClusters`
- `ZadarTrack` and `ZadarTracks`
- `ZadarOdometry`

Standard ROS message types are used where possible:

- `sensor_msgs/PointCloud2` for radar scan output
- `sensor_msgs/Imu` for IMU output
