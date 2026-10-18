"""Raster images via Pillow."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageSequence, features

from ..registry import pairs, register

FORMATS = {"png", "jpg", "webp", "bmp", "gif", "tiff", "ico", "ppm", "tga"}
if features.check("avif"):
    FORMATS.add("avif")

# Formats that can't store an alpha channel.
NO_ALPHA = {"jpg", "bmp", "ppm", "pdf"}


def _flatten(img: Image.Image) -> Image.Image:
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        bg = Image.new("RGB", img.size, "white")
        bg.paste(img, mask=img.getchannel("A"))
        return bg
    return img.convert("RGB")


@register("pillow", pairs(FORMATS, FORMATS | {"pdf"}), cost=1, hint="pip install pillow")
def convert(src: Path, dst: Path, src_fmt: str, dst_fmt: str, options: dict) -> list[Path]:
    with Image.open(src) as img:
        if dst_fmt == "pdf":
            frames = [_flatten(f) for f in ImageSequence.Iterator(img)]
            frames[0].save(dst, "PDF", save_all=True, append_images=frames[1:])
            return [dst]
        if dst_fmt in NO_ALPHA:
            img = _flatten(img)
        img.save(dst, quality=options.get("quality", 92)) if dst_fmt in {"jpg", "webp", "avif"} \
            else img.save(dst)
    return [dst]
