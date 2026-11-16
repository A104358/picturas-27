"""Create pad_<N>MiB.mp4 next to this script: the 10 s sample video followed by an
MP4 `free` box so the file is exactly N MiB. Same content, controlled size."""
import struct
from pathlib import Path

here = Path(__file__).resolve().parent
src = (here.parents[4] / 'samples' / 'video' / 'sample_10s_720p.mp4').read_bytes()
for mib in (10, 100, 500):
    pad = mib * 1024 * 1024 - len(src)
    with open(here / f'pad_{mib}MiB.mp4', 'wb') as f:
        f.write(src)
        f.write(struct.pack('>I4sQ', 1, b'free', pad))
        f.write(b'\0' * (pad - 16))
