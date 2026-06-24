#!/usr/bin/env python3
"""Long-name OVERFLOW fit — JSON-driven spool colour-name fitting.

Labels ship sized to the reference font tiers (1.30 / 1.15 / 1.00mm, from
`tools/healing/name_sizing.json`). This tool handles the residual case: where a
name still overflows the field at the smallest tier (the 1.00mm floor carries no
textLength, so the longest names overflow even there), drop it to the compact
font and lock textLength so it fits.

All values are DATA, read from tools/healing/name_sizing.json (field width,
advance, compact font) — there is NO hardcoded name list. The over-length set is
detected by width, so it tracks the spec/golden automatically. When the golden
is fixed upstream to constrain these names, remove the `over_length` block from
the JSON and re-run; this becomes a no-op.

Idempotent (a node already carrying textLength is left alone).

Usage:
  python3 tools/heal_long_names.py [--dirs DIR ...] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SPEC = json.loads((REPO / "tools" / "healing" / "name_sizing.json").read_text())
_SP = (((SPEC.get("families") or {}).get("spool") or {}).get("color_name")) or {}
FIELD = _SP.get("field_width_mm", 23.0)
ADV = _SP.get("advance_per_latin_unit", 1.4)
OVER = _SP.get("over_length") or {}
COMPACT = f"{OVER.get('compact_font_mm', 0.9):g}mm"
LENADJ = OVER.get("lengthAdjust", "spacingAndGlyphs")

DEFAULT_DIRS = (REPO / "master" / "spool" / "print_true" / "labels",
                REPO / "master" / "spool" / "print_true" / "sheets")

# the colour-name node: non-bold, start-anchored, at x=12.50 y=12.x
COLOR_RE = re.compile(r'<text(?P<a>[^>]*\bx="12\.50"[^>]*\by="12[^"]*"[^>]*)>(?P<c>[^<]*)</text>')
FONT_RE = re.compile(r'font-size="([\d.]+)mm"')


def wunits(s: str) -> float:
    u = 0.0
    for ch in s:
        o = ord(ch)
        wide = (0x1100 <= o <= 0x115F or 0x2E80 <= o <= 0xA4CF or 0xAC00 <= o <= 0xD7A3
                or 0xF900 <= o <= 0xFAFF or 0xFE30 <= o <= 0xFE4F
                or 0xFF00 <= o <= 0xFF60 or 0xFFE0 <= o <= 0xFFE6)
        u += 2.0 if wide else 1.0
    return u


def set_attr(attrs, name, value):
    if re.search(rf'\s{name}="[^"]*"', attrs):
        return re.sub(rf'\s{name}="[^"]*"', f' {name}="{value}"', attrs)
    return attrs + f' {name}="{value}"'


def heal_text(svg: str):
    healed = []

    def repl(m):
        a, c = m.group("a"), m.group("c")
        if 'font-weight="700"' in a or not c.strip():
            return m.group(0)
        if 'textLength' in a:          # already fit
            return m.group(0)
        fs = FONT_RE.search(a)
        cur = float(fs.group(1)) if fs else 1.30
        if wunits(c) * cur * ADV <= FIELD:   # fits at its current font
            return m.group(0)
        a = set_attr(a, "font-size", COMPACT)
        a = set_attr(a, "textLength", f"{FIELD:.2f}")
        a = set_attr(a, "lengthAdjust", LENADJ)
        healed.append(c.strip())
        return f"<text{a}>{c}</text>"

    return COLOR_RE.sub(repl, svg), healed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dirs", nargs="*", type=Path, default=list(DEFAULT_DIRS))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not OVER:
        print("over_length block absent from name_sizing.json — nothing to do (golden fixed?)")
        return
    total = 0
    for d in args.dirs:
        d = d.resolve()
        files = sorted(d.rglob("*.svg"))
        changed = 0
        for f in files:
            t = f.read_text(encoding="utf-8")
            new, healed = heal_text(t)
            if healed and new != t:
                changed += 1
                total += len(healed)
                if not args.dry_run:
                    f.write_text(new, encoding="utf-8")
        print(f"  {d.relative_to(REPO)}: {len(files)} scanned, {changed} {'would change' if args.dry_run else 'changed'}")
    print(f"{'(dry-run) ' if args.dry_run else ''}over-length nodes fit: {total}  "
          f"(field={FIELD}mm adv={ADV} compact={COMPACT}, all from name_sizing.json)")


if __name__ == "__main__":
    main()
