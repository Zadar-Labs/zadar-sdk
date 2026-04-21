# UDP Examples

The `examples/` area provides runnable customer examples for the two SDK
surfaces:

- direct UDP data inspection with `zadar_udp`
- sensor control and configuration with `zadar_webapi`

Available language offerings:

- [Python](./python/README.md)
- [C++](./cpp/README.md)

The UDP data examples under `examples/python/zadar_udp/` and
`examples/cpp/zadar_udp/` use the shared `zadar_udp` SDK together with the
canonical protobuf schema from [`../proto/ZadarFrame.proto`](../proto/ZadarFrame.proto).

The HTTP API examples under `examples/python/zadar_webapi/` and
`examples/cpp/zadar_webapi/` use the shared `zadar_webapi` SDK and assume the
default sensor HTTP API port `8080`.

Cross-surface end-to-end examples are also available at:

- `examples/python/api_example.py`
- `examples/cpp/api_example.cpp`

These combine the HTTP API control flow with the UDP listeners in a single
example.
