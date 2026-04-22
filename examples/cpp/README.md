# C++ Example Packages

The `examples/cpp/` area contains runnable C++ examples for both SDK surfaces:

- [zadar_udp](zadar_udp/README.md): live UDP radar listeners and raw IMU packet inspection
- [zadar_webapi](zadar_webapi/README.md): HTTP control and configuration examples

It also includes a top-level end-to-end SDK example:

- `api_example`: configures the sensor over the HTTP API, then reads radar data and raw IMU packets over UDP

Build from the UDP SDK root:

```bash
cmake -S . -B build
cmake --build build -j$(nproc)
```

Built binaries are placed under:

```text
build/examples/cpp/zadar_udp/
build/examples/cpp/zadar_webapi/
build/examples/cpp/api_example
```

Example command:

```bash
./build/examples/cpp/api_example \
  --sensor-host 192.168.0.10 \
  --running-mode 1
```
