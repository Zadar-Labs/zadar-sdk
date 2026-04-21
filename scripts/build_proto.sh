#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROTO_DIR="${ROOT_DIR}/proto"
PROTO_FILE="${PROTO_DIR}/ZadarFrame.proto"
OUT_DIR="${ROOT_DIR}/generated"
CPP_OUT="${OUT_DIR}/cpp"
PY_OUT="${OUT_DIR}/python"
PROTOC_CPP_BIN="${PROTOC_CPP:-}"
PROTOC_PYTHON_BIN="${PROTOC_PYTHON:-${PROTOC:-}}"

if [[ -z "${PROTOC_CPP_BIN}" ]]; then
  if [[ -x /usr/bin/protoc ]]; then
    PROTOC_CPP_BIN="/usr/bin/protoc"
  elif command -v protoc >/dev/null 2>&1; then
    PROTOC_CPP_BIN="$(command -v protoc)"
  else
    echo "error: a protoc binary for C++ generation was not found in PATH" >&2
    exit 1
  fi
fi

if [[ -z "${PROTOC_PYTHON_BIN}" ]]; then
  if command -v protoc >/dev/null 2>&1; then
    PROTOC_PYTHON_BIN="$(command -v protoc)"
  elif [[ -x /usr/bin/protoc ]]; then
    PROTOC_PYTHON_BIN="/usr/bin/protoc"
  else
    echo "error: a protoc binary for Python generation was not found in PATH" >&2
    exit 1
  fi
fi

mkdir -p "${CPP_OUT}" "${PY_OUT}"

"${PROTOC_CPP_BIN}" \
  --proto_path="${PROTO_DIR}" \
  --cpp_out="${CPP_OUT}" \
  "${PROTO_FILE}"

"${PROTOC_PYTHON_BIN}" \
  --proto_path="${PROTO_DIR}" \
  --python_out="${PY_OUT}" \
  "${PROTO_FILE}"

echo "Using protoc for C++:    ${PROTOC_CPP_BIN}"
echo "Using protoc for Python: ${PROTOC_PYTHON_BIN}"
echo "Generated protobuf outputs:"
echo "  C++:    ${CPP_OUT}"
echo "  Python: ${PY_OUT}"
