#!/usr/bin/env python3
"""Validate receiver UF2s against a conservative legacy bootloader budget."""
from pathlib import Path
import struct
import sys


def check(path):
    data = path.read_bytes()
    if not data or len(data) % 512:
        raise ValueError("not a complete UF2 file")
    count = len(data) // 512
    addresses = []
    for index in range(count):
        block = data[index * 512:(index + 1) * 512]
        magic0, magic1, flags, address, size, number, total, family = struct.unpack_from("<8I", block)
        if (magic0, magic1, struct.unpack_from("<I", block, 508)[0]) != (
            0x0A324655, 0x9E5D5157, 0x0AB16F30
        ):
            raise ValueError(f"invalid UF2 magic in block {index}")
        if flags != 0x2000 or family != 0xADA52840 or size != 256:
            raise ValueError(f"unexpected nRF52840 block format at {index}")
        if number != index or total != count:
            raise ValueError(f"incomplete/out-of-order block set at {index}")
        addresses.append(address)
    if addresses[0] != 0x26000 or any(
        address != 0x26000 + index * 256 for index, address in enumerate(addresses)
    ):
        raise ValueError("unexpected receiver application address range")
    # Avoid both old block-count limits and old application flash boundaries.
    # This is deliberately stricter than Zephyr's 792 KB linker region.
    if count >= 2048:
        raise ValueError(
            f"{count} blocks / {count * 256:,} payload bytes exceeds legacy budget "
            "(fewer than 2048 blocks / 512 KiB required)"
        )
    print(f"{path.name}: OK, {count} blocks, {count * 256:,} payload bytes, "
          f"{len(data):,} UF2 bytes, end 0x{addresses[-1] + 256:X}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(f"Usage: {sys.argv[0]} firmware.uf2 [...]")
    for arg in sys.argv[1:]:
        try:
            check(Path(arg))
        except (OSError, ValueError) as error:
            raise SystemExit(f"{arg}: FAIL: {error}")
