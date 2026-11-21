"""Test corpus: PAD videos (exact sizes, moov at head or tail) and real samples."""
from __future__ import annotations

import json
import shutil
import struct
import subprocess
from pathlib import Path

from .api import png_bytes
from .config import CORPUS_DIR, MIB, SAMPLES
from .util import log, sha256_file

SOURCE = SAMPLES / "sample_10s_720p.mp4"
SIZES_MIB = (10, 100, 500)
MANIFEST = CORPUS_DIR / "corpus.json"


def _boxes(path: Path) -> list[tuple[str, int, int]]:
    """Top-level MP4 boxes: (type, offset, size)."""
    out = []
    with open(path, "rb") as f:
        f.seek(0, 2)
        end = f.tell()
        off = 0
        while off < end:
            f.seek(off)
            hdr = f.read(16)
            if len(hdr) < 8:
                break
            size, typ = struct.unpack(">I4s", hdr[:8])
            if size == 1:
                size = struct.unpack(">Q", hdr[8:16])[0]
            elif size == 0:
                size = end - off
            out.append((typ.decode("latin-1"), off, size))
            off += size
    return out


def moov_position(path: Path) -> str:
    order = [b[0] for b in _boxes(path)]
    if "moov" not in order or "mdat" not in order:
        return "?"
    return "H" if order.index("moov") < order.index("mdat") else "T"


def _free_box(size: int) -> bytes:
    if size < 8:
        raise ValueError("free box too small")
    return struct.pack(">I4s", size, b"free")


def _write_padded(src: Path, dst: Path, total: int, before_moov: bool) -> None:
    """Pad to an exact size with a `free` box.

    H: ftyp, moov, mdat, free  (box appended at the end)
    T: ftyp, mdat, free, moov  (box inserted just before the trailing moov)
    Neither placement moves mdat, so the absolute chunk offsets in moov stay valid."""
    pad = total - src.stat().st_size
    with open(src, "rb") as fin, open(dst, "wb") as fout:
        if before_moov:
            moov = next(b for b in _boxes(src) if b[0] == "moov")
            remaining = moov[1]
            while remaining > 0:
                chunk = fin.read(min(remaining, 1 << 20))
                fout.write(chunk)
                remaining -= len(chunk)
            _write_zero_box(fout, pad)
            shutil.copyfileobj(fin, fout, 1 << 20)
        else:
            shutil.copyfileobj(fin, fout, 1 << 20)
            _write_zero_box(fout, pad)


def _write_zero_box(f, size: int) -> None:
    f.write(_free_box(size))
    remaining = size - 8
    zero = b"\0" * (1 << 20)
    while remaining > 0:
        n = min(remaining, len(zero))
        f.write(zero[:n])
        remaining -= n


def _ffprobe(path: Path) -> dict:
    r = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format",
                        "-show_streams", str(path)], capture_output=True, text=True)
    if r.returncode != 0:
        return {}
    data = json.loads(r.stdout)
    v = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
    return {"duration": float(data.get("format", {}).get("duration", 0) or 0), "codec": v.get("codec_name")}


def build() -> dict:
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    work = CORPUS_DIR / "_work"
    work.mkdir(exist_ok=True)
    head_src, tail_src = work / "h.mp4", work / "t.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(SOURCE), "-c", "copy",
                    "-movflags", "+faststart", str(head_src)], check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(SOURCE), "-c", "copy", str(tail_src)], check=True)
    if moov_position(head_src) != "H":
        raise SystemExit("faststart remux did not put moov first")
    if moov_position(tail_src) != "T":
        raise SystemExit("plain remux did not leave moov at the end")

    files: dict[str, dict] = {}

    def add(name: str, path: Path, kind: str, **extra) -> None:
        files[name] = {"path": str(path.relative_to(CORPUS_DIR)), "bytes": path.stat().st_size,
                       "sha256": sha256_file(path), "kind": kind, **extra}

    for size in SIZES_MIB:
        for pos, src in (("H", head_src), ("T", tail_src)):
            dst = CORPUS_DIR / f"pad_{size}MiB_{pos}.mp4"
            if not dst.exists() or dst.stat().st_size != size * MIB:
                log(f"corpus: {dst.name}")
                _write_padded(src, dst, size * MIB, before_moov=(pos == "T"))
            meta = _ffprobe(dst)
            if abs(meta.get("duration", 0) - 10) > 0.5 or meta.get("codec") != "h264":
                raise SystemExit(f"{dst.name} failed ffprobe validation: {meta}")
            if moov_position(dst) != pos:
                raise SystemExit(f"{dst.name}: moov position is not {pos}")
            add(dst.name, dst, "pad", size_mib=size, moov=pos)

    big = CORPUS_DIR / "pad_1024MiB_plus1_H.mp4"
    if not big.exists() or big.stat().st_size != 1024 * MIB + 1:
        log(f"corpus: {big.name}")
        _write_padded(head_src, big, 1024 * MIB + 1, before_moov=False)
    add(big.name, big, "pad_over_limit", size_mib=1024, moov="H")

    for name in ("sample_6s.mov", "speech_mandela_177s_1080p.webm", "too_long_90s.mp4", "corrupted.mp4"):
        dst = CORPUS_DIR / name
        if not dst.exists():
            shutil.copy2(SAMPLES / name, dst)
        add(name, dst, "sample")
    empty = CORPUS_DIR / "empty.mp4"
    empty.write_bytes(b"")
    add(empty.name, empty, "empty")
    png = CORPUS_DIR / "image.png"
    png.write_bytes(png_bytes(64, 77))
    add(png.name, png, "png")

    shutil.rmtree(work, ignore_errors=True)
    MANIFEST.write_text(json.dumps(files, indent=1))
    return files


def load() -> dict:
    if not MANIFEST.exists():
        raise SystemExit("Corpus missing: run `med.py corpus` first.")
    return json.loads(MANIFEST.read_text())


def path(name: str) -> Path:
    return CORPUS_DIR / name
