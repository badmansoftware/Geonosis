#!/usr/bin/env python3
"""
set_font.py — swap the font-family on Geonosis label/sheet SVGs in one command.

"Let them change font": a community tweaker (or a language that needs a
different script) sets the font from ONE place instead of hand-editing every
<text> node. Replaces every font-family="..." with the chosen stack, in place.

The label SIZING (textLength / colour tiers) is tuned to Arial metrics, so an
Arial-metric font (Liberation Sans, Helvetica, Nimbus Sans) is a drop-in.
Anything notably wider/narrower may shift spacing — re-render one label to
check. Only font-family changes; nothing else is touched, so
output stays clean / zero-trace.

Usage:
  # whole label set
  python3 tools/set_font.py --font "Liberation Sans, Arial, sans-serif" \
      master/languages/qya/spool/print_true/labels
  # add non-Latin fallbacks for a CJK/Arabic tweak
  python3 tools/set_font.py --font "Liberation Sans, 'Noto Sans CJK SC', sans-serif" DIR
  python3 tools/set_font.py --font "Arial, sans-serif" a.svg b.svg   # specific files
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FONT_RE = re.compile(r'font-family="[^"]*"')


def main():
    ap = argparse.ArgumentParser(description="Swap font-family across label/sheet SVGs.")
    ap.add_argument("--font", required=True,
                    help='font stack, e.g. "Liberation Sans, Arial, sans-serif"')
    ap.add_argument("paths", nargs="+", help="SVG files or directories")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    repl = f'font-family="{args.font}"'
    files = []
    for p in args.paths:
        pp = Path(p)
        files += sorted(pp.rglob("*.svg")) if pp.is_dir() else [pp]
    if not files:
        sys.exit("no SVG files found")

    changed = nodes = 0
    for f in files:
        t = f.read_text(encoding="utf-8")
        new, n = FONT_RE.subn(repl, t)
        if n and new != t:
            nodes += n
            changed += 1
            if not args.dry_run:
                f.write_text(new, encoding="utf-8")
    print(f"{'(dry-run) ' if args.dry_run else ''}font-family -> {args.font!r}")
    print(f"  {changed}/{len(files)} files updated, {nodes} text nodes")
    print("  NOTE: re-render one label to check spacing if the font isn't Arial-metric.")


if __name__ == "__main__":
    main()
