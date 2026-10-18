"""Markup and document formats via Pandoc (bundled by pypandoc-binary)."""

from __future__ import annotations

from functools import cache
from pathlib import Path

from ..registry import pairs, register

READERS = {
    "md": "markdown", "txt": "markdown", "html": "html", "docx": "docx", "odt": "odt",
    "rtf": "rtf", "epub": "epub", "latex": "latex", "rst": "rst", "org": "org", "ipynb": "ipynb",
}
WRITERS = {
    "md": "gfm", "txt": "plain", "html": "html", "docx": "docx", "odt": "odt", "rtf": "rtf",
    "epub": "epub", "latex": "latex", "rst": "rst", "org": "org", "ipynb": "ipynb", "pptx": "pptx",
}


@cache
def _available() -> bool:
    try:
        import pypandoc

        pypandoc.get_pandoc_version()
        return True
    except Exception:
        return False


@register("pandoc", pairs(READERS, WRITERS), cost=2, available=_available,
          hint="pip install pypandoc-binary")
def convert(src: Path, dst: Path, src_fmt: str, dst_fmt: str, options: dict) -> list[Path]:
    import pypandoc

    args = ["--standalone"]
    if dst_fmt == "html":
        args.append("--embed-resources")
    pypandoc.convert_file(str(src), WRITERS[dst_fmt], format=READERS[src_fmt],
                          outputfile=str(dst), extra_args=args)
    return [dst]
