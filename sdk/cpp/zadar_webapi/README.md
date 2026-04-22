# C++ HTTP API SDK

This directory contains the shared C++ SDK for the sensor HTTP API used by the
examples and the sensor-managed ROS frontends.

Scope of the SDK implementation:

- HTTP request execution through `libcurl`
- response parsing and error normalization
- reusable helpers for running-mode, network, output, PTP, diagnostics, and reboot control
