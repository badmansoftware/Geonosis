#!/usr/bin/env python3
"""
inline_sheet_cells.py — convert base64-<image> sheet cells to INLINED artwork.

The materials print sheets embed each label as a base64 data-URI <image>.
Renderers (Inkscape, cairosvg) do not faithfully rasterize a nested SVG — they
scale/clip it and drop textLength — so the material type/name text prints off
the label. This replaces each cell's <image> with the label's artwork inlined
under a <g translate(x,y)> (the same fix applied to custom_sheet.py), so text
renders natively. Label coordinates are preserved exactly (image x/y must equal
the label's native mm size — no scaling; a mismatch is reported and skipped).

Idempotent: a cell already inlined (no <image>) is left alone.

Usage:
  python3 tools/inline_sheet_cells.py [--dry-run]
  python3 tools/inline_sheet_cells.py --paths master/materials/print_true/sheets
"""
from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path

try:
    from lxml import etree
except ImportError:
    sys.exit("lxml required")

REPO = Path(__file__).resolve().parents[1]
MASTER = REPO / "master"
SVG = "http://www.w3.org/2000/svg"
NS = "{%s}" % SVG
SIZE_TOL = 0.05


def parse_mm(v):
    import re
    m = re.match(r"^\s*([0-9.]+)\s*mm\s*$", v or "")
    return float(m.group(1)) if m else None


def label_artwork(label_path: Path):
    root = etree.fromstring(label_path.read_bytes().lstrip())
    w, h = parse_mm(root.get("width")), parse_mm(root.get("height"))
    kids = [c for c in root if not (isinstance(c.tag, str) and etree.QName(c).localname == "title")]
    return kids, (w, h)


def convert(sheet_path: Path, labels_dir: Path, dry_run: bool):
    tree = etree.parse(str(sheet_path))
    root = tree.getroot()
    converted, skipped = [], []
    for cell in list(root.iter()):
        if not isinstance(cell.tag, str):
            continue
        fn = cell.get("data-filename")
        if not fn:
            continue
        img = cell.find(NS + "image")
        if img is None:
            continue  # already inlined
        x, y = float(img.get("x", 0)), float(img.get("y", 0))
        w, h = float(img.get("width", 0)), float(img.get("height", 0))
        label = labels_dir / fn
        if not label.exists():
            skipped.append((fn, "label missing"))
            continue
        kids, (lw, lh) = label_artwork(label)
        if lw is None or abs(w - lw) > SIZE_TOL or abs(h - lh) > SIZE_TOL:
            skipped.append((fn, f"size {w}x{h} != label {lw}x{lh} (would scale)"))
            continue
        g = etree.SubElement(cell, NS + "g")
        g.set("transform", f"translate({x:g},{y:g})")
        for k in kids:
            g.append(copy.deepcopy(k))
        cell.remove(img)
        converted.append(fn)
    if converted and not dry_run:
        body = etree.tostring(root, pretty_print=True, encoding="UTF-8")
        sheet_path.write_bytes(b'<?xml version="1.0" encoding="UTF-8"?>\n' + body)
    return converted, skipped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paths", nargs="*", default=["materials/print_true/sheets"],
                    help="sheet dirs under master/ (default: materials sheets)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    sheets = []
    for p in args.paths:
        d = MASTER / p
        sheets += sorted(d.rglob("*.svg")) if d.is_dir() else [Path(p)]

    total_c = total_s = 0
    for s in sheets:
        # find the print_true/labels dir for this sheet (materials sheets sit an
        # extra <size-group>/ deep, so walk ancestors for the labels sibling)
        labels_dir = next((a / "labels" for a in s.parents if (a / "labels").is_dir()), None)
        if labels_dir is None:
            print(f"  {s.relative_to(MASTER)}: no sibling labels/ dir — skipped")
            continue
        c, sk = convert(s, labels_dir, args.dry_run)
        total_c += len(c)
        total_s += len(sk)
        flag = "" if not sk else "  SKIPPED: " + "; ".join(f"{n}:{w}" for n, w in sk)
        if c or sk:
            print(f"  {s.relative_to(MASTER)}: inlined {len(c)} cell(s){flag}")
    print(f"{'(dry-run) ' if args.dry_run else ''}total inlined: {total_c}, skipped: {total_s}")
    if total_s:
        sys.exit(1)


if __name__ == "__main__":
    main()
