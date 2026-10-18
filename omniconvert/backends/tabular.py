"""Tabular data (CSV, Excel, ODS, JSON) via pandas."""

from __future__ import annotations

from pathlib import Path

from ..registry import pairs, register

READ = {"csv", "tsv", "xlsx", "xls", "ods", "json"}
WRITE = {"csv", "tsv", "xlsx", "ods", "json", "html"}


def _read(src: Path, fmt: str, options: dict):
    import pandas as pd

    if fmt == "csv":
        return pd.read_csv(src)
    if fmt == "tsv":
        return pd.read_csv(src, sep="\t")
    if fmt == "json":
        return pd.read_json(src)
    sheet = options.get("sheet") or 0
    if isinstance(sheet, str) and sheet.isdigit():
        sheet = int(sheet)
    return pd.read_excel(src, sheet_name=sheet)


@register("pandas", pairs(READ, WRITE), cost=1, hint="pip install pandas openpyxl xlrd odfpy")
def convert(src: Path, dst: Path, src_fmt: str, dst_fmt: str, options: dict) -> list[Path]:
    df = _read(src, src_fmt, options)
    if dst_fmt == "csv":
        df.to_csv(dst, index=False)
    elif dst_fmt == "tsv":
        df.to_csv(dst, sep="\t", index=False)
    elif dst_fmt == "xlsx":
        df.to_excel(dst, index=False)
    elif dst_fmt == "ods":
        df.to_excel(dst, index=False, engine="odf")
    elif dst_fmt == "json":
        df.to_json(dst, orient="records", indent=2, force_ascii=False)
    elif dst_fmt == "html":
        df.to_html(dst, index=False)
    return [dst]
