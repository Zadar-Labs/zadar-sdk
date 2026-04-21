# Supported Environments And Dependencies

The SDK can be used in either of these environments:

- native Linux installation
- containerized Linux environment

The ROS 1 and ROS 2 workflows do not require containers, but containerized
setups are fully valid when they match the required ROS distribution and system
dependencies.

## Validated Environments

The following combinations have been validated during SDK bring-up:

- Python and C++ examples on Ubuntu Linux with live sensor traffic
- ROS 1 in a ROS Noetic environment with live driver, record, and replay flows
- ROS 2 in a ROS Rolling environment with live driver, record, and replay flows

Equivalent native and containerized Linux environments may also be used when
the same dependency sets are available.

## Core SDK Dependencies

Common tooling:

- Linux environment with standard POSIX socket support
- CMake 3.16 or newer for C++ builds
- Python 3.8 or newer for Python examples and tools

Common Ubuntu packages:

- `build-essential`
- `cmake`
- `libprotobuf-dev`
- `protobuf-compiler`
- `libcurl4-openssl-dev`

Protocol and build tooling:

- `libprotobuf-dev`
- `protobuf-compiler`

These packages are required when building the C++ SDK layers or regenerating
protobuf bindings from `proto/ZadarFrame.proto`.

## Example Dependencies

Python examples:

- Python 3.8 or newer
- `protobuf`

C++ examples:

- C++17 compiler
- CMake 3.16 or newer
- `libprotobuf-dev`
- `protobuf-compiler`

## HTTP API Dependencies

Python HTTP API:

- Python 3.8 or newer
- `requests`

C++ HTTP API:

- C++17 compiler
- CMake 3.16 or newer
- `libcurl4-openssl-dev`

The default top-level CMake configure expects `libcurl4-openssl-dev` to be
installed when building the C++ HTTP API surface. If it is missing, configure
fails with an explicit installation hint.

Customers who intentionally want a UDP-only C++ build can disable the HTTP API
surface with:

- `-DZADAR_BUILD_WEBAPI_CPP=OFF`

## ROS 2 Dependencies

ROS 2 requirements:

- supported ROS 2 environment
- `colcon`
- standard ROS 2 build tools and message-generation packages
- `libprotobuf-dev`
- `protobuf-compiler`
- `python3-requests` for the Python driver in sensor-managed mode
- `libcurl4-openssl-dev` for the C++ driver in sensor-managed mode

Optional ROS 2 tooling:

- `rosbag2` storage plugins such as `sqlite3` or `mcap`
- `foxglove_bridge` or `rosbridge_server` for external visualization workflows

## ROS 1 Dependencies

ROS 1 requirements:

- supported ROS 1 environment
- `catkin_make`
- standard ROS 1 build tools and message-generation packages
- `libprotobuf-dev`
- `protobuf-compiler`
- `python3-requests` for the Python driver in sensor-managed mode
- `libcurl4-openssl-dev` for the C++ driver in sensor-managed mode

Optional ROS 1 tooling:

- `rosbag`

## Notes

- The bundled Python protobuf bindings and the installed Python `protobuf`
  runtime should be kept compatible.
- The SDK root can be built with system protobuf tooling. When regenerating
  bindings, prefer the `scripts/build_proto.sh` helper from the SDK root.
- The HTTP API surface intentionally excludes firmware image upload, mode-file
  upload or extraction, and global configuration wipe operations.
