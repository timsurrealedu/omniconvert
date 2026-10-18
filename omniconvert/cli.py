from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core import ConversionError, convert, route
from .registry import CONVERTERS, all_formats, detect, normalize, reachable


def cmd_convert(args: argparse.Namespace) -> int:
    if len(args.files) > 1 and args.output and Path(args.output).suffix:
        print("With several input files, -o must be a directory", file=sys.stderr)
        return 2
    options = {k: v for k, v in (("sheet", args.sheet), ("dpi", args.dpi)) if v is not None}
    failures = 0
    for f in args.files:
        try:
            if args.dry_run:
                steps = route(detect(Path(f)), normalize(args.to))
                print(f"{f}: " + " -> ".join([steps[0][1]] + [f"{t} [{c.name}]" for c, _, t in steps]))
                continue
            for out in convert(f, args.to, args.output, overwrite=args.force, **options):
                print(f"{f} -> {out}")
        except (ConversionError, ValueError) as e:
            failures += 1
            print(f"error: {f}: {e}", file=sys.stderr)
    return 1 if failures else 0


def cmd_formats(args: argparse.Namespace) -> int:
    if args.format:
        src = normalize(args.format)
        targets = sorted(reachable(src))
        print(f"{src} can be converted to: {', '.join(targets) or '(nothing with installed tools)'}")
        return 0
    print("Backends:")
    for name in dict.fromkeys(c.name for c in CONVERTERS):
        conv = next(c for c in CONVERTERS if c.name == name)
        status = "ok" if conv.available() else f"missing - {conv.hint}"
        print(f"  {name:<20} {status}")
    print("\nKnown formats:\n  " + ", ".join(sorted(all_formats())))
    print("\nRun `omniconvert formats <fmt>` to see what a format converts to.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omniconvert", description="Convert files between formats.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("convert", aliases=["c"], help="convert files")
    p.add_argument("files", nargs="+", help="input files")
    p.add_argument("-t", "--to", required=True, help="target format, e.g. pdf, docx, csv, png")
    p.add_argument("-o", "--output", help="output file or directory (default: next to input)")
    p.add_argument("-f", "--force", action="store_true", help="overwrite existing output")
    p.add_argument("--sheet", help="spreadsheet sheet name or index to read (default: first)")
    p.add_argument("--dpi", type=int, help="resolution for PDF -> image (default: 150)")
    p.add_argument("-n", "--dry-run", action="store_true", help="show the conversion route only")
    p.set_defaults(func=cmd_convert)

    p = sub.add_parser("formats", aliases=["f"], help="list formats and backend status")
    p.add_argument("format", nargs="?", help="show targets reachable from this format")
    p.set_defaults(func=cmd_formats)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
