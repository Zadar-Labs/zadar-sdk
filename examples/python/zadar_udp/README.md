# Python UDP Examples

The Python examples package provides runnable scripts for the live UDP radar
stream and the separate raw IMU stream using the shared `zadar_udp` SDK.

Use this area when you want to:

- validate sensor output directly from Python
- inspect decoded scans, clusters, tracks, odometry, and raw IMU packets
- start a custom Python integration from a working example

These examples are receive-only. They do not configure the sensor or
start a running mode. Use the HTTP API examples under
`examples/python/zadar_webapi/` or `examples/cpp/zadar_webapi/` first when the
sensor output destination, ports, or running mode need to be set from software.

The separate `imu` stream contains raw onboard accelerometer and gyroscope
measurements from the internal MEMS sensor. It is intended for low-level
inspection and installation validation, and it is not a GNSS/INS output. No
GNSS/GPS data is used or required.

Use the radar examples on the radar port and the IMU example on the separate
IMU port. The package defaults are:

- PCL / radar data: `7777`
- raw IMU data: `36636`

All examples print decoded timestamps in the host local timezone
using `YYYY-DD-MM HH:MM:SS.XXX`.

## Requirements

- Python 3.8 or later
- `protobuf`

The SDK already includes the generated Python protobuf module at:

```text
generated/python/ZadarFrame_pb2.py
```

No protobuf generation step is required to run the bundled examples.

Use `scripts/build_proto.sh` only when protobuf bindings need to be
regenerated, such as after changing `proto/ZadarFrame.proto`, when generated
files are missing, or when a protobuf compatibility issue requires fresh
outputs.

## Example Commands

Radar scan example:

```bash
python3 examples/python/zadar_udp/radar_data_example.py
```

Cluster example:

```bash
python3 examples/python/zadar_udp/clusters_example.py
```

Track example:

```bash
python3 examples/python/zadar_udp/tracks_example.py
```

Odometry example:

```bash
python3 examples/python/zadar_udp/odometry_example.py
```

IMU example:

```bash
python3 examples/python/zadar_udp/imu_data_example.py
```

Raw frame summary:

```bash
python3 examples/python/zadar_udp/live_frame_listener.py
```

## Stream Selection

The examples are split by stream type:

- `radar_data_example.py`, `clusters_example.py`, `tracks_example.py`,
  `odometry_example.py`, and `live_frame_listener.py` expect the radar UDP
  stream
- `imu_data_example.py` expects the separate raw IMU UDP stream

Pointing a radar parser at the IMU port, or the IMU parser at the radar port,
will produce warnings because the packet layouts are different.

Recommended first checks:

- start with `live_frame_listener.py` on the radar port to confirm radar frame reception
- then move to the higher-level radar examples for points, clusters, tracks, and odometry
- use `imu_data_example.py` on the IMU port to inspect raw onboard accelerometer and gyroscope packets when needed

`clusters_example.py` and `tracks_example.py` may legitimately report zero
objects if the active stream or sensor configuration is not producing those
outputs.

## Common CLI Options

Radar examples support:

- `--bind-address`
- `--port`
- `--frame-limit`
- `--socket-timeout-sec`
- `--generated-python-dir`

The scan, cluster, and track examples also support `--sample-count`.

IMU examples support:

- `--bind-address`
- `--port`
- `--packet-limit`
- `--socket-timeout-sec`

Use `--help` on any example to view the full option set. Example:

```bash
python3 examples/python/zadar_udp/radar_data_example.py --help
```

## Example Coverage

- `radar_data_example.py`: scan metadata and sampled radar points
- `clusters_example.py`: cluster counts and sampled cluster summaries
- `tracks_example.py`: track counts and sampled track summaries
- `odometry_example.py`: odometry output when present in the frame
- `imu_data_example.py`: formatted timestamps, raw acceleration, raw angular rate, and a local packet counter
- `live_frame_listener.py`: low-level frame summaries with formatted timestamps for link validation

## SDK Import Path

Applications can import the shared SDK directly:

```python
from zadar_udp import RadarDataListener, RadarStatusCodes
from zadar_udp import ImuDataListener, ImuStatusCodes
```
