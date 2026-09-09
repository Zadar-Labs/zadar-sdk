# Changelog

All notable changes to `zadar-sdk` are documented in this file.

## Unreleased

- Release notes for the next version will be added here.


## 0.2.0 - 2026-09-09

### Overview

- Channel: `release`
- Package: `Zadar UDP Sensor SDK`
- Supported sensor family: `zPRIME2.0`, `zPRIME3.0`, `zPULSE`

### Highlights

- **ROS 1**: Updated ROS 1 messages, drivers, launch files, or sample configuration. Representative paths: `ros1/src/zadar_udp_driver`, `ros1/src/zadar_udp_driver_py`.
- **ROS 2**: Updated ROS 2 messages, drivers, launch files, or sample configuration. Representative paths: `ros2/src/zadar_udp_driver`, `ros2/src/zadar_udp_driver_py`.
- **SDK**: Updated shared C++ and/or Python SDK packages. Representative paths: `sdk/cpp/zadar_webapi`, `sdk/python/zadar_webapi`.
- **Examples**: Updated standalone example applications and usage samples. Representative paths: `examples/cpp/zadar_udp`, `examples/python/zadar_udp`.
- **Documentation**: Updated public documentation, quick-start material, or integration guidance. Representative paths: `SDK_MANUAL.md`, `docs/ros_topics_and_parameters.md`.
- **Protocol / Generated Bindings**: Updated protobuf schema files or shipped generated bindings. Representative paths: `generated/cpp/ZadarFrame.pb.cc`, `generated/cpp/ZadarFrame.pb.h`, `generated/python/ZadarFrame_pb2.py`, and 1 more.
- **Build / Tooling**: Updated build helpers, packaging metadata, or developer tooling. Representative paths: `PACKAGE_RELEASE.json`.
- **Repository Metadata**: Updated repository-level metadata such as changelog or licensing information. Representative paths: `CHANGELOG.md`.

### Maintainer Notes

**RCS Support**

- Added RCS values to radar points in the C++ and Python SDKs.
- Added the `rcs` field to ROS 1 and ROS 2 PointCloud2 output.
- RCS values are populated when enabled by the selected sensor mode.
- Older firmware and modes without RCS remain compatible.

**Driver Improvements**

- Increased the default WebAPI timeout to five seconds.
- Improved ROS 2 recording compatibility across Humble and Jazzy.
- Improved Python driver shutdown handling.

### Assets

- `zadar_sdk_udp-0.2.0.zip`
- `zadar_sdk_udp-0.2.0.tar.gz`

## 0.1.1

### Added

- Initial public UDP SDK release.
- CI workflows for ROS 1, ROS 2, C++, and Python validation.
- Release metadata scaffolding for badges, changelog, and GitHub Releases.
