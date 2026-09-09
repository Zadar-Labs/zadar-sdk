from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def _normalized_value(context, name: str) -> str:
    return LaunchConfiguration(name).perform(context).strip().strip("/")


def _resolved_namespace(context) -> str:
    namespace = _normalized_value(context, "namespace")
    sensor_name = _normalized_value(context, "sensor_name")
    return "/".join(part for part in (namespace, sensor_name) if part)


def _namespaced_topic(namespace: str, topic: str) -> str:
    if namespace:
        return f"/{namespace}/{topic}"
    return f"/{topic}"


def _bool_argument(context, name: str) -> bool:
    return LaunchConfiguration(name).perform(context).strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _launch_setup(context, *args, **kwargs):
    namespace = _resolved_namespace(context)
    topics = []

    if _bool_argument(context, "record_points"):
        topics.append(_namespaced_topic(namespace, "points"))
    if _bool_argument(context, "record_clusters"):
        topics.append(_namespaced_topic(namespace, "clusters"))
    if _bool_argument(context, "record_tracks"):
        topics.append(_namespaced_topic(namespace, "tracks"))
    if _bool_argument(context, "record_odometry"):
        topics.append(_namespaced_topic(namespace, "odometry"))
    if _bool_argument(context, "record_imu"):
        topics.append(_namespaced_topic(namespace, "imu"))

    if not topics:
        raise RuntimeError("record.launch.py requires at least one enabled record_* topic")

    driver_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("zadar_udp_driver_py"), "launch", "driver.launch.py"]
            )
        ),
        launch_arguments={
            "driver_package": LaunchConfiguration("driver_package"),
            "driver_executable": LaunchConfiguration("driver_executable"),
            "namespace": LaunchConfiguration("namespace"),
            "sensor_name": LaunchConfiguration("sensor_name"),
            "params_file": LaunchConfiguration("params_file"),
            "udp_bind_address": LaunchConfiguration("udp_bind_address"),
            "bind_address": LaunchConfiguration("bind_address"),
            "sensor_hostname": LaunchConfiguration("sensor_hostname"),
            "host_ip": LaunchConfiguration("host_ip"),
            "data_port": LaunchConfiguration("data_port"),
            "imu_port": LaunchConfiguration("imu_port"),
            "webapi_port": LaunchConfiguration("webapi_port"),
            "webapi_timeout_sec": LaunchConfiguration("webapi_timeout_sec"),
            "running_mode": LaunchConfiguration("running_mode"),
            "frame_id": LaunchConfiguration("frame_id"),
            "publish_scan": LaunchConfiguration("publish_scan"),
            "publish_clusters": LaunchConfiguration("publish_clusters"),
            "publish_tracks": LaunchConfiguration("publish_tracks"),
            "publish_odometry": LaunchConfiguration("publish_odometry"),
            "publish_imu": LaunchConfiguration("publish_imu"),
            "radar_socket_buffer_bytes": LaunchConfiguration(
                "radar_socket_buffer_bytes"
            ),
            "imu_socket_buffer_bytes": LaunchConfiguration("imu_socket_buffer_bytes"),
            "max_buffered_frames": LaunchConfiguration("max_buffered_frames"),
            "frame_timeout_sec": LaunchConfiguration("frame_timeout_sec"),
            "socket_timeout_sec": LaunchConfiguration("socket_timeout_sec"),
            "generated_python_dir": LaunchConfiguration("generated_python_dir"),
        }.items(),
    )

    record_command = [
        "ros2",
        "bag",
        "record",
        "-o",
        LaunchConfiguration("bag_file").perform(context),
        "-s",
        LaunchConfiguration("storage_id").perform(context),
    ] + topics

    recorder = ExecuteProcess(cmd=record_command, output="screen")
    return [driver_launch, recorder]


def generate_launch_description() -> LaunchDescription:
    default_params_file = PathJoinSubstitution(
        [FindPackageShare("zadar_udp_driver_py"), "config", "driver.yaml"]
    )

    arguments = [
        DeclareLaunchArgument("driver_package", default_value="zadar_udp_driver"),
        DeclareLaunchArgument("driver_executable", default_value="zadar_udp_driver_node"),
        DeclareLaunchArgument("namespace", default_value="zadar"),
        DeclareLaunchArgument("sensor_name", default_value=""),
        DeclareLaunchArgument("params_file", default_value=default_params_file),
        DeclareLaunchArgument("udp_bind_address", default_value=""),
        DeclareLaunchArgument("bind_address", default_value=""),
        DeclareLaunchArgument("sensor_hostname", default_value=""),
        DeclareLaunchArgument("host_ip", default_value=""),
        DeclareLaunchArgument("data_port", default_value="0"),
        DeclareLaunchArgument("imu_port", default_value="0"),
        DeclareLaunchArgument("webapi_port", default_value="8080"),
        DeclareLaunchArgument("webapi_timeout_sec", default_value="5.0"),
        DeclareLaunchArgument("running_mode", default_value="-1"),
        DeclareLaunchArgument("frame_id", default_value=""),
        DeclareLaunchArgument("publish_scan", default_value="true"),
        DeclareLaunchArgument("publish_clusters", default_value="true"),
        DeclareLaunchArgument("publish_tracks", default_value="true"),
        DeclareLaunchArgument("publish_odometry", default_value="true"),
        DeclareLaunchArgument("publish_imu", default_value="true"),
        DeclareLaunchArgument("radar_socket_buffer_bytes", default_value="67108864"),
        DeclareLaunchArgument("imu_socket_buffer_bytes", default_value="4194304"),
        DeclareLaunchArgument("max_buffered_frames", default_value="128"),
        DeclareLaunchArgument("frame_timeout_sec", default_value="1.0"),
        DeclareLaunchArgument("socket_timeout_sec", default_value="0.25"),
        DeclareLaunchArgument("generated_python_dir", default_value=""),
        DeclareLaunchArgument("bag_file", default_value="zadar_udp_recording"),
        DeclareLaunchArgument("storage_id", default_value="sqlite3"),
        DeclareLaunchArgument("record_points", default_value="true"),
        DeclareLaunchArgument("record_clusters", default_value="true"),
        DeclareLaunchArgument("record_tracks", default_value="true"),
        DeclareLaunchArgument("record_odometry", default_value="true"),
        DeclareLaunchArgument("record_imu", default_value="true"),
    ]

    return LaunchDescription(arguments + [OpaqueFunction(function=_launch_setup)])
