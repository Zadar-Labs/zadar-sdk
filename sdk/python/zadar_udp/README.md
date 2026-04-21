# Python UDP SDK

This directory contains the shared Python UDP SDK used by UDP examples
and Python-based ROS frontends.

The Python SDK mirrors the C++ SDK architecture closely enough that
documentation and examples stay aligned across languages.

SDK foundation modules:

- `zadar_udp.packet`: UDP packet header parsing
- `zadar_udp.reassembly`: fragmented frame reassembly
- `zadar_udp.source`: reusable UDP frame source
- `zadar_udp.proto`: generated protobuf loader
- `zadar_udp.radar`: radar listener API
- `zadar_udp.imu`: IMU listener API
- `zadar_udp.crc`: shared CRC helpers

This package is distributed together with `zadar_webapi` from the shared
`sdk/python/pyproject.toml`.
