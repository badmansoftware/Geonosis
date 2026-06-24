#!/usr/bin/env python3
"""
fix_alignment_marks.py — move the corner registration crosses inward so the
right-edge marks aren't clipped by the printer.

The original marks sat 12mm from each edge with 5mm arms, so the right-edge
cross reached to ~7mm from the paper edge — inside many printers' unprintable
margin, so it printed cut off. This re-places the crosses at a larger inset
with a shorter arm, regenerated deterministically from each file's OWN paper
size, so a print sheet and its matching cut stay byte-for-byte identical in
their marks (they keep registering).

Surgical: only the `class="alignment-mark"` lines are removed and re-emitted;
every other byte of the file is untouched. Idempotent. Refuses (reports) if a
new mark would land inside the label content bbox instead of the margin.

Default inset/arm (15mm / 3mm) is the max inward the spool grid allows — it
fills x=22..259 of the 279.4mm Letter width, leaving only a ~20mm right margin.

Usage:
  python3 tools/fix_alignment_marks.py [--offset 15] [--arm 3] [--dry-run]
  python3 tools/fix_alignment_marks.py --paths master/spool/print_true/sheets ...
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MASTER = REPO / "master"

MARK_LINE_RE = re.compile(r'[ \t]*<line\b[^>]*class="alignment-mark"[^>]*/>\n?')
ROOT_WH_RE = re.compile(r'<svg\b[^>]*\bwidth="([\d.]+)mm"[^>]*\bheight="([\d.]+)mm"', re.S)
COORD_RE = re.compile(r'\b(?:x|x1|x2|cx)="([\d.]+)"')
COORDY_RE = re.compile(r'\b(?:y|y1|y2|cy)="([\d.]+)"')
TRANS_RE = re.compile(r'translate\(([\d.]+),\s*([\d.]+)\)')


def default_paths():
    pats = ["*/print_true/sheets/**/*.svg", "*/print_true/cuts/**/*.svg",
            "*/bambu/cuts/**/*.svg"]
    out = []
    for p in pats:
        out += [f for f in MASTER.glob(p)]
    return sorted(set(out))


def content_bbox(text_without_marks: str):
    """Absolute label-cell bbox in mm (marks already stripped).

    Two cell styles exist: (1) inlined artwork inside `<g transform="translate">`
    groups (v0.1 spool sheets) — here ONLY the translate origins are absolute,
    so inner <image>/coords are ignored; (2) top-level base64 `<image>` cells
    (box/materials/by_type) — here the image boxes are absolute. Using the wrong
    source mixes cell-local coords into the bbox, so pick by which style the
    file uses."""
    trans = TRANS_RE.findall(text_without_marks)
    if trans:
        xs = [float(x) for x, _ in trans]
        ys = [float(y) for _, y in trans]
        return (min(xs), min(ys), max(xs), max(ys))
    xs, ys = [], []
    for m in re.finditer(r'<image\b[^>]*\bx="([\d.]+)"[^>]*\by="([\d.]+)"[^>]*\bwidth="([\d.]+)"[^>]*\bheight="([\d.]+)"', text_without_marks):
        x, y, w, h = (float(g) for g in m.groups())
        xs += [x, x + w]; ys += [y, y + h]
    if not xs or not ys:
        return None
    return (min(xs), min(ys), max(xs), max(ys))


def make_marks(pw, ph, offset, arm):
    centers = [(offset, offset), (pw - offset, offset),
               (offset, ph - offset), (pw - offset, ph - offset)]
    lines = []
    for cx, cy in centers:
        for x1, y1, x2, y2 in ((cx, cy - arm, cx, cy + arm), (cx - arm, cy, cx + arm, cy)):
            lines.append(f'  <line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
                         f'stroke="black" stroke-width="0.3" class="alignment-mark"/>')
    return centers, "\n".join(lines) + "\n"


def overlaps(centers, arm, bbox):
    if not bbox:
        return []
    minx, miny, maxx, maxy = bbox
    bad = []
    for cx, cy in centers:
        # the cross spans [cx-arm,cx+arm] x [cy-arm,cy+arm]
        if (cx + arm > minx and cx - arm < maxx) and (cy + arm > miny and cy - arm < maxy):
            bad.append((round(cx, 1), round(cy, 1)))
    return bad


def fix_file(path: Path, offset, arm, dry_run):
    text = path.read_text(encoding="utf-8")
    n_old = len(MARK_LINE_RE.findall(text))
    if n_old == 0:
        return {"file": path, "skipped": "no alignment marks"}
    stripped = MARK_LINE_RE.sub("", text)
    m = ROOT_WH_RE.search(stripped)
    if not m:
        return {"file": path, "skipped": "no mm width/height"}
    pw, ph = float(m.group(1)), float(m.group(2))
    centers, marks_svg = make_marks(pw, ph, offset, arm)
    bad = overlaps(centers, arm, content_bbox(stripped))
    # insert new marks just before the closing </svg>
    idx = stripped.rfind("</svg>")
    new = stripped[:idx] + marks_svg + stripped[idx:]
    if not dry_run and not bad:
        path.write_text(new, encoding="utf-8")
    return {"file": path, "paper": (pw, ph), "old_marks": n_old,
            "right_tip_mm_from_edge": round(offset - arm, 2),
            "overlap": bad, "wrote": (not dry_run and not bad)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offset", type=float, default=15.0, help="mm inset of cross centers from each edge")
    ap.add_argument("--arm", type=float, default=3.0, help="mm half-length of each cross arm")
    ap.add_argument("--paths", nargs="*", help="dirs/files (default: all master sheets + cuts)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    targets = []
    if args.paths:
        for p in args.paths:
            pp = Path(p)
            targets += sorted(pp.rglob("*.svg")) if pp.is_dir() else [pp]
    else:
        targets = default_paths()

    print(f"fix_alignment_marks: offset={args.offset}mm arm={args.arm}mm "
          f"-> right-edge tip {args.offset - args.arm:.1f}mm from paper edge "
          f"({len(targets)} files){' [dry-run]' if args.dry_run else ''}")
    wrote = skipped = overlapped = 0
    for t in targets:
        r = fix_file(t, args.offset, args.arm, args.dry_run)
        if r.get("skipped"):
            skipped += 1
        elif r["overlap"]:
            overlapped += 1
            print(f"  !! OVERLAP {t.relative_to(MASTER)}: marks {r['overlap']} hit content — NOT written")
        elif r["wrote"] or args.dry_run:
            wrote += 1
    print(f"  {wrote} updated, {skipped} skipped (no marks), {overlapped} refused (overlap)")
    if overlapped:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
