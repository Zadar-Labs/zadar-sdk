"""CRC helpers for Zadar UDP SDK components."""

from __future__ import annotations

from typing import List, Optional, Tuple, Union


class CRC64Ecma182:
    """Reflected CRC64-ECMA-182 implementation used by IMU packets."""

    REVERSED_POLY = 0xC96C5795D7870F42
    _TABLE = None  # type: Optional[Tuple[int, ...]]

    @classmethod
    def _build_table(cls) -> None:
        table = []  # type: List[int]
        for value in range(256):
            crc = value
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ cls.REVERSED_POLY
                else:
                    crc >>= 1
            table.append(crc & 0xFFFFFFFFFFFFFFFF)
        cls._TABLE = tuple(table)

    def __init__(self) -> None:
        if type(self)._TABLE is None:
            type(self)._build_table()
        self._crc = 0xFFFFFFFFFFFFFFFF

    def update(self, data: Union[bytes, memoryview]) -> None:
        assert self._TABLE is not None
        for byte in data:
            table_index = (self._crc ^ byte) & 0xFF
            self._crc = (
                self._TABLE[table_index] ^ (self._crc >> 8)
            ) & 0xFFFFFFFFFFFFFFFF

    def digest(self) -> int:
        return self._crc ^ 0xFFFFFFFFFFFFFFFF
