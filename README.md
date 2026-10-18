# omniconvert

Convert (almost) any file to any other format from one command: documents, spreadsheets,
slides, PDFs, images, audio and video.

```sh
omniconvert convert report.pptx -t pdf
omniconvert convert scan.pdf -t docx
omniconvert convert *.xlsx -t csv -o exports/
omniconvert convert notes.md -t pdf
omniconvert convert clip.mov -t mp3
```

## How it works

Each backend registers the format pairs it can handle. To convert, omniconvert finds the
cheapest chain of converters between the two formats, so conversions no single tool supports
still work. `md -> pdf`, for example, goes `md -> html (pandoc) -> pdf (pymupdf)`. To see the
route without running it, use `--dry-run`:

```sh
$ omniconvert convert notes.md -t pdf -n
notes.md: md -> html [pandoc] -> pdf [pymupdf-story]
```

| Backend | Handles |
|---|---|
| LibreOffice | doc/docx/odt/rtf, xls/xlsx/ods/csv, ppt/pptx/odp ↔ each other and → pdf |
| Pandoc (bundled) | md, html, docx, odt, rtf, epub, latex, rst, org, ipynb, txt, → pptx |
| pandas | csv, tsv, xlsx, xls, ods, json → csv, tsv, xlsx, ods, json, html |
| pdf2docx / PyMuPDF | pdf → docx, txt, png/jpg (one image per page); html/txt → pdf |
| Pillow | png, jpg, webp, bmp, gif, tiff, ico, ppm, tga, avif ↔ each other and → pdf |
| ffmpeg | mp3, wav, flac, ogg, m4a, aac, opus, wma, mp4, mkv, webm, avi, mov, flv, wmv, gif |

If a backend is missing, omniconvert tells you what to install. For full-fidelity Office
conversions (pptx/docx/xlsx → pdf) install **LibreOffice**; without it docx/xlsx → pdf falls
back to a simpler HTML render, and pptx → pdf isn't available.

## Install

Requires Python 3.10+ and [uv](https://docs.astral.sh/uv/).

```sh
git clone https://github.com/timsurrealedu/omniconvert
cd omniconvert
uv tool install .          # puts `omniconvert` on your PATH
```

Optional system tools:

```sh
# Arch
sudo pacman -S libreoffice-fresh ffmpeg
# Windows
winget install TheDocumentFoundation.LibreOffice Gyan.FFmpeg
```

## Usage

```
omniconvert convert FILES... -t FORMAT [-o OUTPUT] [-f] [--sheet NAME] [--dpi N] [-n]
omniconvert formats            # backend status and every known format
omniconvert formats pdf        # what pdf can be converted to
```

- `-o` takes a file path (single input) or a directory. By default output goes next to the input.
- `-f` overwrites existing files. Without it, omniconvert won't overwrite anything.
- `--sheet` picks which spreadsheet sheet to read (name or index; the first sheet by default).
- `--dpi` sets the resolution for PDF → image.

From Python:

```python
from omniconvert import convert
convert("deck.pptx", "pdf", output="out/")
```

## Development

```sh
uv sync
uv run pytest
```

## License

MIT
