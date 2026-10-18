"""PDF in and out via PyMuPDF and pdf2docx."""

from __future__ import annotations

import html
from pathlib import Path

from ..registry import pairs, register


@register("pdf2docx", {("pdf", "docx")}, cost=1, hint="pip install pdf2docx")
def pdf_to_docx(src: Path, dst: Path, src_fmt: str, dst_fmt: str, options: dict) -> list[Path]:
    from pdf2docx import Converter

    conv = Converter(str(src))
    try:
        conv.convert(str(dst))
    finally:
        conv.close()
    return [dst]


@register("pymupdf-render", pairs({"pdf"}, {"png", "jpg"}), cost=1, hint="pip install pymupdf")
def pdf_to_image(src: Path, dst: Path, src_fmt: str, dst_fmt: str, options: dict) -> list[Path]:
    """One image per page; multi-page PDFs get a _p001 style suffix."""
    import pymupdf

    written = []
    with pymupdf.open(src) as doc:
        for i, page in enumerate(doc, 1):
            out = dst if len(doc) == 1 else dst.with_name(f"{dst.stem}_p{i:03d}{dst.suffix}")
            page.get_pixmap(dpi=options.get("dpi", 150)).save(out)
            written.append(out)
    return written


@register("pymupdf-text", {("pdf", "txt")}, cost=1, hint="pip install pymupdf")
def pdf_to_text(src: Path, dst: Path, src_fmt: str, dst_fmt: str, options: dict) -> list[Path]:
    import pymupdf

    with pymupdf.open(src) as doc:
        dst.write_text("\f".join(page.get_text() for page in doc), encoding="utf-8")
    return [dst]


# Basic HTML layout engine: lower fidelity than LibreOffice, so it is only picked as a fallback.
# txt costs more so formatted sources (md, docx) route through html rather than plain text.
@register("pymupdf-story", {("html", "pdf")}, cost=5, hint="pip install pymupdf")
@register("pymupdf-story", {("txt", "pdf")}, cost=6, hint="pip install pymupdf")
def html_to_pdf(src: Path, dst: Path, src_fmt: str, dst_fmt: str, options: dict) -> list[Path]:
    import pymupdf

    text = src.read_text(encoding="utf-8", errors="replace")
    if src_fmt == "txt":
        text = f"<pre>{html.escape(text)}</pre>"
    story = pymupdf.Story(html=text, archive=str(src.parent))
    mediabox = pymupdf.paper_rect("a4")
    where = mediabox + (54, 54, -54, -54)
    writer = pymupdf.DocumentWriter(str(dst))
    more = True
    while more:
        device = writer.begin_page(mediabox)
        more, _ = story.place(where)
        story.draw(device)
        writer.end_page()
    writer.close()
    return [dst]
