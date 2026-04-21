"""ROS message conversion helpers for the Zadar UDP ROS 1 driver."""

from __future__ import annotations

import struct
from typing import Iterable, List, Tuple

import rospy
from geometry_msgs.msg import Point32
from sensor_msgs.msg import Imu, PointCloud2, PointField
from std_msgs.msg import Header
from zadar_msgs.msg import (
    ZadarCluster,
    ZadarClusters,
    ZadarOdometry,
    ZadarTrack,
    ZadarTracks,
)


POINT_FIELD_LAYOUT = [
    ("x", PointField.FLOAT32, "f"),
    ("y", PointField.FLOAT32, "f"),
    ("z", PointField.FLOAT32, "f"),
    ("snr", PointField.FLOAT32, "f"),
    ("range", PointField.FLOAT32, "f"),
    ("noise", PointField.FLOAT32, "f"),
    ("doppler", PointField.FLOAT32, "f"),
    ("adjusted_doppler", PointField.FLOAT32, "f"),
    ("frame_num", PointField.UINT32, "I"),
    ("is_static", PointField.UINT8, "B"),
    ("removed", PointField.UINT8, "B"),
    ("subframe_index", PointField.UINT32, "I"),
    ("fence_id", PointField.UINT32, "I"),
    ("power", PointField.FLOAT32, "f"),
]

POINT_STRUCT = struct.Struct("<" + "".join(item[2] for item in POINT_FIELD_LAYOUT))


def ros_time_from_ns(timestamp_ns: int) -> rospy.Time:
    return rospy.Time(
        secs=int(timestamp_ns // 1_000_000_000),
        nsecs=int(timestamp_ns % 1_000_000_000),
    )


def ros_time_from_sec_nsec(timestamp_sec: int, timestamp_nsec: int) -> rospy.Time:
    return rospy.Time(secs=int(timestamp_sec), nsecs=int(timestamp_nsec))


def header_from_ns(frame_id: str, timestamp_ns: int) -> Header:
    return Header(frame_id=frame_id, stamp=ros_time_from_ns(timestamp_ns))


def frame_timestamp_ns(timestamp: Tuple[int, int]) -> int:
    return int(timestamp[0]) * 1_000_000_000 + int(timestamp[1])


def scan_timestamp_ns(radar_scan: object, fallback_timestamp_ns: int) -> int:
    stamp = int(radar_scan.header.stamp)
    return stamp if stamp > 0 else fallback_timestamp_ns


def radar_scan_to_pointcloud2(
    radar_scan: object,
    frame_id: str,
    fallback_timestamp_ns: int,
) -> PointCloud2:
    msg = PointCloud2()
    msg.header = header_from_ns(frame_id, scan_timestamp_ns(radar_scan, fallback_timestamp_ns))
    msg.is_bigendian = False
    msg.is_dense = bool(radar_scan.is_dense)

    offset = 0
    msg.fields = []
    for name, datatype, format_char in POINT_FIELD_LAYOUT:
        msg.fields.append(
            PointField(
                name=name,
                offset=offset,
                datatype=datatype,
                count=1,
            )
        )
        offset += struct.calcsize(format_char)
    msg.point_step = POINT_STRUCT.size

    point_count = len(radar_scan.points)
    width = int(radar_scan.width) if int(radar_scan.width) > 0 else point_count
    height = int(radar_scan.height) if int(radar_scan.height) > 0 else 1
    if width * height != point_count:
        width = point_count
        height = 1

    msg.width = width
    msg.height = height
    msg.row_step = msg.point_step * msg.width

    data = bytearray(msg.point_step * point_count)
    for index, point in enumerate(radar_scan.points):
        POINT_STRUCT.pack_into(
            data,
            index * msg.point_step,
            float(point.x),
            float(point.y),
            float(point.z),
            float(point.snr),
            float(point.range),
            float(point.noise),
            float(point.doppler),
            float(point.adjusted_doppler),
            int(point.frame_num),
            int(point.is_static),
            int(point.removed),
            int(point.subframe_index),
            int(point.fence_id),
            float(point.power),
        )
    msg.data = bytes(data)
    return msg


def _vertices_to_ros(vertices: Iterable[object]) -> List[Point32]:
    return [Point32(x=float(vertex.x), y=float(vertex.y), z=float(vertex.z)) for vertex in vertices]


def clusters_to_msg(
    clusters: Iterable[object],
    frame_id: str,
    timestamp_ns: int,
) -> ZadarClusters:
    cluster_list = list(clusters)
    msg = ZadarClusters()
    msg.header = header_from_ns(frame_id, timestamp_ns)
    msg.frame_num = int(cluster_list[0].frame_num) if cluster_list else 0

    converted: List[ZadarCluster] = []
    for cluster in cluster_list:
        cluster_msg = ZadarCluster()
        cluster_msg.cluster_id = int(cluster.cluster_id)
        cluster_msg.frame_num = int(cluster.frame_num)
        cluster_msg.subframe_index = int(cluster.subframe_index)
        cluster_msg.is_static = bool(cluster.is_static)
        cluster_msg.x = float(cluster.x)
        cluster_msg.y = float(cluster.y)
        cluster_msg.z = float(cluster.z)
        cluster_msg.doppler = float(cluster.doppler)
        cluster_msg.snr = float(cluster.snr)
        cluster_msg.noise = float(cluster.noise)
        cluster_msg.d_min = float(cluster.d_min)
        cluster_msg.d_max = float(cluster.d_max)
        cluster_msg.r_min = float(cluster.r_min)
        cluster_msg.r_max = float(cluster.r_max)
        cluster_msg.lambda1 = float(cluster.lambda1)
        cluster_msg.lambda2 = float(cluster.lambda2)
        cluster_msg.lambda3 = float(cluster.lambda3)
        cluster_msg.num_points = int(cluster.num_points)
        cluster_msg.vertices = _vertices_to_ros(cluster.vertices)
        cluster_msg.scan = radar_scan_to_pointcloud2(cluster.scan, frame_id, timestamp_ns)
        converted.append(cluster_msg)

    msg.clusters = converted
    return msg


def tracks_to_msg(
    tracks: Iterable[object],
    frame_id: str,
    timestamp_ns: int,
    frame_number: int,
) -> ZadarTracks:
    track_list = list(tracks)
    msg = ZadarTracks()
    msg.header = header_from_ns(frame_id, timestamp_ns)
    msg.frame_num = int(frame_number)

    converted: List[ZadarTrack] = []
    for track in track_list:
        track_msg = ZadarTrack()
        track_msg.track_id = int(track.track_id)
        track_msg.x = float(track.x)
        track_msg.y = float(track.y)
        track_msg.z = float(track.z)
        track_msg.vx = float(track.vx)
        track_msg.vy = float(track.vy)
        track_msg.vz = float(track.vz)
        track_msg.ax = float(track.ax)
        track_msg.ay = float(track.ay)
        track_msg.az = float(track.az)
        track_msg.yaw = float(track.yaw)
        track_msg.speed = float(track.speed)
        track_msg.num_points = int(track.num_points)
        track_msg.latest_observed_frame_num = int(track.latest_observed_frame_num)
        track_msg.latest_cluster_id = int(track.latest_cluster_id)
        track_msg.state = int(track.state)
        track_msg.classification_output = int(track.classification_output)
        track_msg.fence_id = int(track.fence_id)
        track_msg.scan = radar_scan_to_pointcloud2(track.scan, frame_id, timestamp_ns)
        converted.append(track_msg)

    msg.tracks = converted
    return msg


def odometry_to_msg(odometry: object, frame_id: str, fallback_timestamp_ns: int) -> ZadarOdometry:
    timestamp_ns = int(odometry.stamp) if int(odometry.stamp) > 0 else fallback_timestamp_ns
    msg = ZadarOdometry()
    msg.header = header_from_ns(frame_id, timestamp_ns)
    msg.sensor_stamp = int(timestamp_ns)
    msg.frame_num = int(odometry.frame_num)
    msg.raw_vx = float(odometry.raw_vx)
    msg.raw_vy = float(odometry.raw_vy)
    msg.raw_vz = float(odometry.raw_vz)
    msg.vx = float(odometry.vx)
    msg.vy = float(odometry.vy)
    msg.vz = float(odometry.vz)
    msg.phi = float(odometry.phi)
    msg.psi = float(odometry.psi)
    msg.theta = float(odometry.theta)
    msg.omega_x = float(odometry.omega_x)
    msg.omega_y = float(odometry.omega_y)
    msg.omega_z = float(odometry.omega_z)
    return msg


def imu_payload_to_msg(payload: object, frame_id: str) -> Imu:
    packet = payload.data_object
    msg = Imu()
    msg.header.frame_id = frame_id
    msg.header.stamp = ros_time_from_sec_nsec(payload.timestamp[0], payload.timestamp[1])

    msg.orientation_covariance[0] = -1.0
    msg.angular_velocity_covariance[0] = -1.0
    msg.linear_acceleration_covariance[0] = -1.0

    msg.linear_acceleration.x = float(packet.acceleration_x)
    msg.linear_acceleration.y = float(packet.acceleration_y)
    msg.linear_acceleration.z = float(packet.acceleration_z)
    msg.angular_velocity.x = float(packet.angular_rate_x)
    msg.angular_velocity.y = float(packet.angular_rate_y)
    msg.angular_velocity.z = float(packet.angular_rate_z)
    return msg
