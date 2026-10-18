"""Audio and video via ffmpeg."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from ..registry import pairs, register

AUDIO = {"mp3", "wav", "flac", "ogg", "m4a", "aac", "opus", "wma"}
VIDEO = {"mp4", "mkv", "webm", "avi", "mov", "flv", "wmv"}


@register(
    "ffmpeg",
    pairs(AUDIO | VIDEO, AUDIO) | pairs(VIDEO | {"gif"}, VIDEO) | pairs(VIDEO, {"gif"}),
    cost=1,
    available=lambda: shutil.which("ffmpeg") is not None,
    hint="Install ffmpeg (Arch: pacman -S ffmpeg, Windows: winget install ffmpeg)",
    chainable=False,
)
def convert(src: Path, dst: Path, src_fmt: str, dst_fmt: str, options: dict) -> list[Path]:
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(src)]
    if dst_fmt in AUDIO:
        cmd.append("-vn")
    elif dst_fmt in {"mp4", "mov"}:
        # H.264 needs even dimensions and yuv420p for broad player support.
        cmd += ["-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", "-pix_fmt", "yuv420p"]
    subprocess.run([*cmd, str(dst)], check=True, capture_output=True)
    return [dst]
