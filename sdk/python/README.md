# Python SDK Packages

The `sdk/python/` area contains the shared Python packages used by the examples
and the Python-based ROS frontends.

Available packages:

- [zadar_udp](zadar_udp/README.md): UDP transport, frame reassembly, and protobuf decoding
- [zadar_webapi](zadar_webapi/README.md): HTTP client helpers for sensor control and configuration

Both packages are distributed from the shared `sdk/python/pyproject.toml`.

Install them together from the UDP SDK root:

```bash
python3 -m pip install ./sdk/python
```
