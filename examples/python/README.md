# Python Example Packages

The `examples/python/` area contains runnable Python examples for both SDK
surfaces:

- [zadar_udp](zadar_udp/README.md): live UDP radar listeners and raw IMU packet inspection
- [zadar_webapi](zadar_webapi/README.md): HTTP control and configuration examples

It also includes a top-level end-to-end SDK example:

- `api_example.py`: configures the sensor over the HTTP API, then reads radar data and raw IMU packets over UDP

The examples import the shared packages from `sdk/python/`.

Example command:

```bash
python3 examples/python/api_example.py \
  --sensor-host 192.168.0.10 \
  --running-mode 1
```
