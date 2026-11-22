"""Entry for news-image-20261121: sum up 21 November 2026 in one image.

Writes the front page (entry.png, bundled beside this script) to
/output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png when that is set).
The bundled image is validated as a whole, well-formed PNG of the
expected size before it is copied. Standard library only; no network,
no randomness, no timestamps, so repeated runs produce identical bytes.
"""

import os
import shutil
import struct
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output")
OUT = OUT_DIR / "entry.png"

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
EXPECTED_WIDTH = 1024
EXPECTED_HEIGHT = 1024
MAX_BYTES = 1_048_576


def validate_png(path: Path) -> None:
    """Check that path is a whole, well-formed PNG of the expected size.

    Verifies the PNG signature, the IHDR chunk (dimensions, bit depth,
    colour type), every chunk's CRC, and that the file ends with IEND
    and nothing after it. Raises SystemExit with a clear reason on
    the first problem found.
    """
    data = path.read_bytes()
    if len(data) > MAX_BYTES:
        raise SystemExit(f"{path}: {len(data)} bytes exceeds 1 MiB")
    if data[:8] != PNG_SIGNATURE:
        raise SystemExit(f"{path}: not a PNG (bad signature)")
    pos = 8
    width = height = None
    saw_iend = False
    while pos < len(data):
        if pos + 8 > len(data):
            raise SystemExit(f"{path}: truncated chunk header at {pos}")
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        ctype = data[pos + 4:pos + 8]
        end = pos + 8 + length + 4
        if end > len(data):
            raise SystemExit(f"{path}: truncated {ctype.decode('latin1')} chunk")
        chunk = data[pos + 4:end - 4]
        (crc,) = struct.unpack(">I", data[end - 4:end])
        if zlib.crc32(chunk) & 0xFFFFFFFF != crc:
            raise SystemExit(f"{path}: bad CRC in {ctype.decode('latin1')} chunk")
        if ctype == b"IHDR":
            if length != 13:
                raise SystemExit(f"{path}: IHDR is {length} bytes, expected 13")
            width, height, depth, colour = struct.unpack(">IIBB", data[pos + 8:pos + 18])
            if (width, height) != (EXPECTED_WIDTH, EXPECTED_HEIGHT):
                raise SystemExit(
                    f"{path}: {width}x{height}, expected "
                    f"{EXPECTED_WIDTH}x{EXPECTED_HEIGHT}"
                )
            if depth != 8 or colour not in (2, 6):
                raise SystemExit(f"{path}: unsupported bit depth {depth} / colour {colour}")
        if ctype == b"IEND":
            saw_iend = True
            if end != len(data):
                raise SystemExit(f"{path}: trailing bytes after IEND")
            break
        pos = end
    if width is None:
        raise SystemExit(f"{path}: no IHDR chunk")
    if not saw_iend:
        raise SystemExit(f"{path}: no IEND chunk (truncated file)")


def main():
    src = HERE / "entry.png"
    if not src.is_file():
        raise SystemExit(f"missing {src}")
    validate_png(src)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, OUT)
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
