from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, OpaqueFunction
from launch.substitutions import LaunchConfiguration


def _bool_argument(context, name: str) -> bool:
    return LaunchConfiguration(name).perform(context).strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _launch_setup(context, *args, **kwargs):
    command = [
        "ros2",
        "bag",
        "play",
        LaunchConfiguration("bag_file").perform(context),
    ]

    rate = LaunchConfiguration("rate").perform(context).strip()
    if rate:
        command.extend(["--rate", rate])

    clock = LaunchConfiguration("clock").perform(context).strip()
    if clock:
        command.extend(["--clock", clock])

    if _bool_argument(context, "loop"):
        command.append("--loop")
    if _bool_argument(context, "start_paused"):
        command.append("--start-paused")

    return [ExecuteProcess(cmd=command, output="screen")]


def generate_launch_description() -> LaunchDescription:
    arguments = [
        DeclareLaunchArgument("bag_file"),
        DeclareLaunchArgument("rate", default_value="1.0"),
        DeclareLaunchArgument("clock", default_value=""),
        DeclareLaunchArgument("loop", default_value="false"),
        DeclareLaunchArgument("start_paused", default_value="false"),
    ]

    return LaunchDescription(arguments + [OpaqueFunction(function=_launch_setup)])
