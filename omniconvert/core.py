"""High-level conversion API."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from . import backends  # noqa: F401
from .registry import Step, detect, normalize, plan


class ConversionError(Exception):
    pass


def route(src_fmt: str, dst_fmt: str) -> list[Step]:
    if src_fmt == dst_fmt:
        raise ConversionError(f"already {dst_fmt}")
    steps = plan(src_fmt, dst_fmt)
    if steps is not None:
        return steps
    if blocked := plan(src_fmt, dst_fmt, include_unavailable=True):
        missing = {c.hint for c, _, _ in blocked if not c.available()}
        raise ConversionError(f"{src_fmt} -> {dst_fmt} needs a missing tool: " + "; ".join(missing))
    raise ConversionError(f"No conversion path from {src_fmt} to {dst_fmt}")


def convert(src: Path | str, target: str, output: Path | str | None = None,
            overwrite: bool = False, **options) -> list[Path]:
    """Convert src to the target format. Returns the files written."""
    src = Path(src).resolve()
    if not src.is_file():
        raise ConversionError(f"File not found: {src}")
    src_fmt, dst_fmt = detect(src), normalize(target)

    if output is None:
        dst = src.with_suffix(f".{dst_fmt}")
    else:
        output = Path(output)
        dst = output / f"{src.stem}.{dst_fmt}" if output.is_dir() or not output.suffix else output
    dst = dst.resolve()
    if dst.exists() and not overwrite:
        raise ConversionError(f"{dst} already exists (use --force to overwrite)")
    dst.parent.mkdir(parents=True, exist_ok=True)

    steps = route(src_fmt, dst_fmt)
    with tempfile.TemporaryDirectory(prefix="omniconvert-") as tmp:
        current = src
        for i, (conv, s, t) in enumerate(steps):
            last = i == len(steps) - 1
            # Build in temp, then move, so a failed run never leaves a half-written file at dst.
            step_dst = Path(tmp, f"{i}-{src.stem}.{t}")
            try:
                written = conv.func(current, step_dst, s, t, options)
            except Exception as e:
                raise ConversionError(f"{conv.name} failed on {s} -> {t}: {e}") from e
            if not last:
                if len(written) != 1:
                    raise ConversionError(f"{s} -> {t} produced {len(written)} files mid-route")
                current = written[0]
        results = []
        for f in written:
            final = dst.with_name(dst.stem + f.stem.removeprefix(step_dst.stem) + dst.suffix)
            shutil.move(f, final)
            results.append(final)
    return results
