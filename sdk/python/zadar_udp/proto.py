"""Helpers for loading generated protobuf code for the UDP package."""

from __future__ import annotations

import ast
from importlib import util as importlib_util
from pathlib import Path
import re
import sys
from types import ModuleType
from typing import Optional, Union

from google.protobuf import descriptor_pool
from google.protobuf import message_factory


_MESSAGE_NAMES = (
    "RadarPoint",
    "RadarScanHeader",
    "RadarScan",
    "ZadarOdometry",
    "ZadarVertex",
    "ZadarClusters",
    "ZadarTracks",
    "ZadarCluster",
    "ZadarTrack",
    "ZadarFrame",
    "ZadarImu",
)

_SERIALIZED_FILE_PATTERN = re.compile(
    r"AddSerializedFile\((b(?P<quote>['\"]).*?(?<!\\)(?P=quote))\)",
    re.DOTALL,
)


def default_generated_python_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "generated" / "python"


def _build_dynamic_proto_module(
    module_name: str,
    module_path: Path,
) -> ModuleType:
    source_text = module_path.read_text(encoding="utf-8")
    match = _SERIALIZED_FILE_PATTERN.search(source_text)
    if match is None:
        raise RuntimeError(
            f"Unable to locate the serialized protobuf descriptor in {module_path}"
        )

    serialized_file = ast.literal_eval(match.group(1))
    pool = descriptor_pool.DescriptorPool()
    file_descriptor = pool.AddSerializedFile(serialized_file)
    package_name = file_descriptor.package

    module = ModuleType(module_name)
    module.__file__ = str(module_path)
    module.DESCRIPTOR = file_descriptor

    get_message_class = getattr(message_factory, "GetMessageClass", None)
    factory = message_factory.MessageFactory(pool)
    get_prototype = getattr(factory, "GetPrototype", None)

    for message_name in _MESSAGE_NAMES:
        full_name = f"{package_name}.{message_name}"
        message_descriptor = pool.FindMessageTypeByName(full_name)
        if get_message_class is not None:
            message_class = get_message_class(message_descriptor)
        elif get_prototype is not None:
            message_class = get_prototype(message_descriptor)
        else:
            raise RuntimeError(
                "The installed protobuf runtime does not provide a supported "
                "message factory API."
            )
        setattr(module, message_name, message_class)

    return module


def load_zadar_proto_module(
    generated_python_dir: Optional[Union[str, Path]] = None,
) -> Optional[ModuleType]:
    """Load the generated ``ZadarFrame_pb2`` module if it exists."""

    search_dir = (
        Path(generated_python_dir)
        if generated_python_dir is not None
        else default_generated_python_dir()
    )
    module_path = search_dir / "ZadarFrame_pb2.py"
    if not module_path.exists():
        return None

    module_name = "ZadarFrame_pb2"
    existing = sys.modules.get(module_name)
    if existing is not None:
        return existing

    spec = importlib_util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Failed to load protobuf module from {module_path}")

    module = importlib_util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(module_name, None)
        try:
            fallback_module = _build_dynamic_proto_module(module_name, module_path)
        except Exception as fallback_exc:
            raise RuntimeError(
                "Failed to load generated Zadar protobuf bindings from "
                f"{module_path}. Regenerate them with "
                "`scripts/build_proto.sh` and ensure "
                "the installed Python protobuf package is compatible with the "
                "generated file."
            ) from fallback_exc
        sys.modules[module_name] = fallback_module
        return fallback_module
    return module
