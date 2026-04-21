# SDK Package Layout

The SDK is organized into several main categories.

## `proto/`

The canonical protobuf schema for UDP frame payloads.

## `generated/`

Generated protobuf bindings shipped with the package for Python and C++ use.

## `sdk/`

Shared Python and C++ packages used by the examples and ROS frontends.

Responsibilities:

- `sdk/cpp/zadar_udp/` and `sdk/python/zadar_udp/`: UDP socket setup, packet
  reception, frame reassembly, protobuf parsing, and decoded frame access
- `sdk/cpp/zadar_webapi/` and `sdk/python/zadar_webapi/`: HTTP client helpers
  for sensor control, configuration, diagnostics, and reboot workflows

## `examples/`

Runnable Python and C++ examples for both direct sensor-data inspection and
sensor control without ROS.

## `ros1/` and `ros2/`

ROS driver workspaces, packages, and launch surfaces for live streaming,
recording, and replay.

## Layout Principle

Code shared by more than one surface lives in `sdk/`. Surface-specific behavior
stays within `examples/`, `ros1/`, or `ros2/`.
