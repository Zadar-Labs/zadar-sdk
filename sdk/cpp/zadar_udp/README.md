# C++ UDP SDK

This directory contains the shared C++ UDP SDK used by the UDP examples
and ROS frontends.

Scope of the SDK implementation:

- UDP packet reception
- fragmented frame reassembly
- protobuf parsing
- public frame and metadata types
- reusable conversion helpers for frontend integrations

The public headers live under `include/zadar/udp/`.
