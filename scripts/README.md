# UDP Package Scripts

This directory contains helper scripts that are shipped with the package.

Included script:

- `build_proto.sh`: generate C++ and Python protobuf outputs from `proto/ZadarFrame.proto`

Use `build_proto.sh` only when protobuf bindings need to be regenerated, for example:

- after changing `proto/ZadarFrame.proto`
- if generated files under `generated/` are missing
- if a protobuf toolchain update requires regenerated outputs for compatibility

Normal SDK use does not require running this script because the package already
ships generated protobuf bindings.
