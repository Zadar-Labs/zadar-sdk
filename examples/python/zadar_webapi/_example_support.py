from __future__ import annotations

import json
from pathlib import Path
import sys


UDP_ROOT = Path(__file__).resolve().parents[3]
SDK_PYTHON_DIR = UDP_ROOT / "sdk" / "python"

if str(SDK_PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(SDK_PYTHON_DIR))


def print_response(title: str, response) -> None:
    print(f"\n=== {title} ===")
    print(f"status_code={response.status_code} success={response.success}")
    if response.error:
        print(f"error={response.error}")
    elif response.json_body is not None:
        print(json.dumps(response.json_body, indent=2, sort_keys=True))
    elif response.text_body:
        print(response.text_body)
