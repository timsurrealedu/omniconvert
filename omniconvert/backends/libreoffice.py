"""Office documents, spreadsheets and presentations via headless LibreOffice."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from functools import cache
from pathlib import Path

from ..registry import pairs, register

WRITER_IN = {"doc", "docx", "odt", "rtf", "txt", "html"}
WRITER_OUT = {"pdf", "doc", "docx", "odt", "rtf", "txt", "html", "epub"}
CALC_IN = {"xls", "xlsx", "ods", "csv"}
CALC_OUT = {"pdf", "xls", "xlsx", "ods", "csv", "html"}
IMPRESS_IN = {"ppt", "pptx", "odp"}
IMPRESS_OUT = {"pdf", "ppt", "pptx", "odp"}

# Export filters where LibreOffice's default isn't UTF-8 or isn't the one we want.
FILTERS = {
    ("writer", "txt"): "txt:Text (encoded):UTF8",
    ("calc", "csv"): "csv:Text - txt - csv (StarCalc):44,34,76",
}

HINT = "Install LibreOffice (Arch: pacman -S libreoffice-fresh, Windows: libreoffice.org)"


@cache
def soffice() -> str | None:
    for name in ("soffice", "libreoffice"):
        if found := shutil.which(name):
            return found
    for base in (os.environ.get("PROGRAMFILES"), os.environ.get("PROGRAMFILES(X86)")):
        if base and (exe := Path(base, "LibreOffice", "program", "soffice.exe")).exists():
            return str(exe)
    if (mac := Path("/Applications/LibreOffice.app/Contents/MacOS/soffice")).exists():
        return str(mac)
    return None


def _run(src: Path, dst: Path, dst_fmt: str, family: str) -> list[Path]:
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        # A private profile avoids clashing with an already-open LibreOffice window.
        cmd = [
            soffice(),
            "--headless",
            "--norestore",
            f"-env:UserInstallation={(tmp / 'profile').as_uri()}",
            "--convert-to",
            FILTERS.get((family, dst_fmt), dst_fmt),
            "--outdir",
            str(tmp / "out"),
            str(src),
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=600)
        produced = list((tmp / "out").glob(f"*.{dst_fmt}"))
        if not produced:
            raise RuntimeError(f"LibreOffice produced no output for {src.name}")
        shutil.move(produced[0], dst)
    return [dst]


def _make(family: str, sources: set[str], targets: set[str], cost: int) -> None:
    @register(f"libreoffice-{family}", pairs(sources, targets), cost=cost,
              available=lambda: soffice() is not None, hint=HINT)
    def convert(src, dst, src_fmt, dst_fmt, options):
        return _run(src, dst, dst_fmt, family)


_make("writer", WRITER_IN, WRITER_OUT, cost=1)
_make("impress", IMPRESS_IN, IMPRESS_OUT, cost=1)
# Plain data conversions are faster through pandas; LibreOffice handles the rest (pdf, xls, ...).
_make("calc", CALC_IN, CALC_OUT, cost=2)
