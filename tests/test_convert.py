import json
import shutil
import subprocess

import pandas as pd
import pymupdf
import pytest
from PIL import Image

from omniconvert import ConversionError, convert
from omniconvert.backends.libreoffice import soffice
from omniconvert.registry import plan

needs_ffmpeg = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
needs_lo = pytest.mark.skipif(soffice() is None, reason="LibreOffice not installed")


@pytest.fixture
def csv_file(tmp_path):
    p = tmp_path / "data.csv"
    p.write_text("name,score\nAda,95\nLinus,88\n")
    return p


@pytest.fixture
def md_file(tmp_path):
    p = tmp_path / "doc.md"
    p.write_text("# Title\n\nHello **world**.\n\n- one\n- two\n")
    return p


def test_csv_xlsx_json_roundtrip(csv_file):
    (xlsx,) = convert(csv_file, "xlsx")
    (out,) = convert(xlsx, "json")
    assert json.loads(out.read_text()) == [{"name": "Ada", "score": 95}, {"name": "Linus", "score": 88}]


def test_xlsx_sheet_option(tmp_path):
    xlsx = tmp_path / "book.xlsx"
    with pd.ExcelWriter(xlsx) as w:
        pd.DataFrame({"a": [1]}).to_excel(w, sheet_name="first", index=False)
        pd.DataFrame({"b": [2]}).to_excel(w, sheet_name="second", index=False)
    (out,) = convert(xlsx, "csv", sheet="second")
    assert out.read_text().splitlines() == ["b", "2"]


def test_image_formats_and_pdf(tmp_path):
    png = tmp_path / "pic.png"
    Image.new("RGBA", (40, 30), (255, 0, 0, 128)).save(png)
    (jpg,) = convert(png, "jpeg")
    assert jpg.suffix == ".jpg" and Image.open(jpg).size == (40, 30)
    (pdf,) = convert(png, "pdf")
    assert pymupdf.open(pdf).page_count == 1


def test_markdown_to_docx_html_pdf(md_file):
    (docx,) = convert(md_file, "docx")
    (html,) = convert(docx, "html")
    assert "<strong>world</strong>" in html.read_text()
    (pdf,) = convert(md_file, "pdf")
    assert "Hello world" in pymupdf.open(pdf)[0].get_text()


def test_pdf_to_docx_txt_and_pages(tmp_path):
    pdf = tmp_path / "two.pdf"
    doc = pymupdf.open()
    for i in range(2):
        doc.new_page().insert_text((72, 72), f"Page {i + 1}")
    doc.save(pdf)
    (docx,) = convert(pdf, "docx")
    (md,) = convert(docx, "md")
    assert "Page 1" in md.read_text()
    (txt,) = convert(pdf, "txt")
    assert "Page 2" in txt.read_text()
    pngs = convert(pdf, "png")
    assert [p.name for p in pngs] == ["two_p001.png", "two_p002.png"]


def test_output_dir_and_overwrite(csv_file, tmp_path):
    out_dir = tmp_path / "out"
    (out,) = convert(csv_file, "tsv", out_dir)
    assert out == out_dir / "data.tsv"
    with pytest.raises(ConversionError, match="already exists"):
        convert(csv_file, "tsv", out_dir)
    convert(csv_file, "tsv", out_dir, overwrite=True)


def test_no_route_or_missing_tool():
    with pytest.raises(ConversionError):
        convert(__file__, "mp3")


def test_media_is_not_chained():
    assert plan("docx", "mp3") is None


@needs_ffmpeg
def test_audio(tmp_path):
    wav = tmp_path / "tone.wav"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "sine=d=0.5", str(wav)], check=True)
    (mp3,) = convert(wav, "mp3")
    assert mp3.stat().st_size > 0


@needs_lo
def test_office_to_pdf(md_file):
    (pptx,) = convert(md_file, "pptx")
    (pdf,) = convert(pptx, "pdf")
    assert pymupdf.open(pdf).page_count >= 1
