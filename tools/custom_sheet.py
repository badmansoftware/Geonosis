#!/usr/bin/env python3
"""
custom_sheet.py — compose a print sheet + matched cut file from EXISTING master
label files. Pure composition: no artwork is generated, scaled, or redrawn.

A print sheet embeds each chosen label (unmodified, at true mm size) as a
base64 <image> in a fixed grid on a paper-sized canvas. The matched cut file
places each label's border outline at the same grid coordinates, plus corner
registration crosses. Print and cut are emitted in ONE run, share a filename
stem + run id, and use identical label coordinates (the grid is the invariant).

Targets (Geonosis dual-sheet doctrine):
  * --paper letter | a4   : print sheet + standard cut (craft cutter)
  * --bambu               : additionally emit a cut on the Bambu H2D envelope
                            (300x285mm), paths only — print sheet stays Letter.

Doctrine guards:
  * NEVER scales. Labels are embedded at their native mm size; if a label's
    size disagrees with the family preset it is reported and SKIPPED, not fixed.
  * Cut outlines are translated copies of each label's own border geometry
    (paths only) — Bambu on-machine registration remains an open verify item.
  * Output must pass tools/geonosis_validate.py gate; PDFs (via that tool's
    Inkscape exporter) must assert MediaBox == paper size.

Usage:
  # per-filament-type spool sheet (Letter print + cut + Bambu cut)
  python3 tools/custom_sheet.py master/spool/print_true/labels/pla_basic__*.svg \
      --family spool --paper letter --bambu --name spool_pla_basic -o builds/_sheets

  # arbitrary custom selection
  python3 tools/custom_sheet.py a.svg b.svg c.svg --family spool --paper letter \
      --name my_picks -o OUTDIR
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

try:
    from lxml import etree
except ImportError:
    sys.exit("lxml required: pip3 install lxml")

SVG_NS = "http://www.w3.org/2000/svg"
SVGNS = "{%s}" % SVG_NS
PAPER = {"letter": (279.4, 215.9), "a4": (297.0, 210.0), "bambu-h2d-cut": (300.0, 285.0)}

# family presets: label size + grid (origin + pitch + cells/page), matched to
# the v0.1 batch sheets so custom sheets share their registration conventions.
FAMILIES = {
    "spool": dict(w=45.0, h=19.0, ox=22.0, oy=20.0, px=48.0, py=22.0, cols=5, rows=8),
    "box":   dict(w=22.0, h=22.0, ox=22.0, oy=22.0, px=26.0, py=26.0, cols=8, rows=7),
}
# registration crosses inset 15mm with 3mm arms -> right-edge tip sits 12mm
# from the paper edge (the old 12/5 put it 7mm out, where printers clip it).
MARK_OFFSET, MARK_ARM = 15.0, 3.0
SIZE_TOL = 0.05


def parse_mm(v):
    m = re.match(r"^\s*([0-9.]+)\s*mm\s*$", v or "")
    return float(m.group(1)) if m else None


def load_label(path: Path, preset):
    """Return (artwork_children, border_geometry_element, (w,h)) or raise.

    artwork_children: the label's drawable child elements (everything except
    <title>), to be INLINED into the sheet under a translate group. Inlining —
    not base64 <image> embedding — is required: renderers (Inkscape, cairosvg)
    do not faithfully rasterize a nested data-URI SVG (they scale/clip it and
    drop textLength), which pushes the material/colour text off the label.
    Inlined artwork renders natively, exactly like the standalone label.

    border_geometry: the outline element (first stroked <path>, else <rect>)
    for the matched cut file."""
    raw = path.read_bytes().lstrip()
    root = etree.fromstring(raw)
    w, h = parse_mm(root.get("width")), parse_mm(root.get("height"))
    if w is None or h is None:
        raise ValueError(f"{path.name}: width/height not in mm")
    if abs(w - preset["w"]) > SIZE_TOL or abs(h - preset["h"]) > SIZE_TOL:
        raise ValueError(f"{path.name}: size {w}x{h}mm != preset {preset['w']}x{preset['h']}mm (NOT scaling)")
    children = [c for c in root if not (isinstance(c.tag, str) and etree.QName(c).localname == "title")]
    # border geometry for the cut: prefer a stroked path/rect (the outline)
    border = None
    for tag in ("path", "rect"):
        for el in root.findall(f"{SVGNS}{tag}"):
            if el.get("stroke") and (el.get("fill") in ("white", "none", "#FFFFFF", "#ffffff", None)):
                border = el
                break
        if border is not None:
            break
    return children, border, (w, h)


_TOKEN = re.compile(r"[A-Za-z]|-?[0-9]*\.?[0-9]+")


def translate_path_d(d: str, dx: float, dy: float) -> str:
    """Translate an absolute-command path's coordinates by (dx,dy). Supports
    M L H V C S Q T A Z (uppercase/absolute). Lowercase relative commands are
    left as-is except the leading move. Raises on anything unexpected so the
    caller can fall back rather than emit a wrong cut line."""
    toks = _TOKEN.findall(d)
    out, i, cmd = [], 0, None
    # consume command + N coords pattern
    def nxt():
        nonlocal i
        v = float(toks[i]); i += 1; return v
    while i < len(toks):
        t = toks[i]
        if re.match(r"[A-Za-z]", t):
            cmd = t; i += 1; out.append(cmd)
            if cmd in ("Z", "z"):
                continue
            continue
        # numeric run for current command
        if cmd in ("M", "L", "T"):
            out.append(f"{nxt()+dx:.4f}"); out.append(f"{nxt()+dy:.4f}")
        elif cmd in ("H",):
            out.append(f"{nxt()+dx:.4f}")
        elif cmd in ("V",):
            out.append(f"{nxt()+dy:.4f}")
        elif cmd in ("C",):
            for _ in range(3):
                out.append(f"{nxt()+dx:.4f}"); out.append(f"{nxt()+dy:.4f}")
        elif cmd in ("S", "Q"):
            for _ in range(2):
                out.append(f"{nxt()+dx:.4f}"); out.append(f"{nxt()+dy:.4f}")
        elif cmd in ("A",):
            out.append(f"{nxt():g}"); out.append(f"{nxt():g}"); out.append(f"{nxt():g}")
            out.append(f"{int(nxt())}"); out.append(f"{int(nxt())}")
            out.append(f"{nxt()+dx:.4f}"); out.append(f"{nxt()+dy:.4f}")
        else:
            raise ValueError(f"unsupported path command {cmd!r}")
    # re-space: commands as letters, numbers separated by spaces
    s = ""
    for tok in out:
        s += (tok + " ") if re.match(r"-?[0-9]", tok) or "." in tok else (tok + " ")
    return s.strip()


def cut_outline(border, dx, dy, preset):
    """Return a cut <path>/<rect> for one cell at (dx,dy). Falls back to a
    rounded-rect of the label bounds if border geometry can't be translated."""
    def styled(el):
        el.set("fill", "none"); el.set("stroke", "#ff0000")
        el.set("stroke-width", "0.3"); el.set("stroke-opacity", "0.55")
        for a in ("data-object-id", "data-filename"):
            if a in el.attrib:
                del el.attrib[a]
        return el
    if border is not None:
        tag = etree.QName(border).localname
        if tag == "path" and border.get("d"):
            try:
                p = etree.Element(SVGNS + "path")
                p.set("d", translate_path_d(border.get("d"), dx, dy))
                return styled(p)
            except ValueError:
                pass
        if tag == "rect":
            r = etree.Element(SVGNS + "rect")
            r.set("x", f"{float(border.get('x', 0)) + dx:.4f}")
            r.set("y", f"{float(border.get('y', 0)) + dy:.4f}")
            r.set("width", border.get("width", str(preset["w"])))
            r.set("height", border.get("height", str(preset["h"])))
            for a in ("rx", "ry"):
                if border.get(a):
                    r.set(a, border.get(a))
            return styled(r)
    # fallback: plain bounds rect
    r = etree.Element(SVGNS + "rect")
    r.set("x", f"{dx:.4f}"); r.set("y", f"{dy:.4f}")
    r.set("width", f"{preset['w']:g}"); r.set("height", f"{preset['h']:g}")
    return styled(r)


def alignment_marks(parent, pw, ph):
    centers = [(MARK_OFFSET, MARK_OFFSET), (pw - MARK_OFFSET, MARK_OFFSET),
               (MARK_OFFSET, ph - MARK_OFFSET), (pw - MARK_OFFSET, ph - MARK_OFFSET)]
    for cx, cy in centers:
        for x1, y1, x2, y2 in ((cx, cy - MARK_ARM, cx, cy + MARK_ARM),
                               (cx - MARK_ARM, cy, cx + MARK_ARM, cy)):
            ln = etree.SubElement(parent, SVGNS + "line")
            ln.set("x1", f"{x1:.2f}"); ln.set("y1", f"{y1:.2f}")
            ln.set("x2", f"{x2:.2f}"); ln.set("y2", f"{y2:.2f}")
            ln.set("stroke", "black"); ln.set("stroke-width", "0.3")
            ln.set("class", "alignment-mark")


def new_root(pw, ph, title):
    root = etree.Element(SVGNS + "svg", nsmap={None: SVG_NS})
    root.set("width", f"{pw:g}mm"); root.set("height", f"{ph:g}mm")
    root.set("viewBox", f"0 0 {pw:g} {ph:g}")
    t = etree.SubElement(root, SVGNS + "title"); t.text = title
    return root


def cell_xy(idx, preset):
    col = idx % preset["cols"]
    row = idx // preset["cols"]
    return preset["ox"] + col * preset["px"], preset["oy"] + row * preset["py"]


def write_svg(root, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    body = etree.tostring(root, pretty_print=True, encoding="UTF-8")
    path.write_bytes(b'<?xml version="1.0" encoding="UTF-8"?>\n' + body)


def sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description="Compose print sheet + matched cut from master labels (no artwork generated).")
    ap.add_argument("labels", nargs="+", help="label .svg files (globs expanded by the shell)")
    ap.add_argument("--family", required=True, choices=list(FAMILIES))
    ap.add_argument("--paper", default="letter", choices=["letter", "a4"])
    ap.add_argument("--bambu", action="store_true", help="also emit a Bambu H2D (300x285) cut")
    ap.add_argument("--name", required=True, help="filename stem")
    ap.add_argument("-o", "--out", required=True, help="output directory (print sheet; also cut unless --cut-out)")
    ap.add_argument("--cut-out", default=None, help="separate dir for the Letter cut (default: --out)")
    ap.add_argument("--bambu-out", default=None, help="separate dir for the Bambu cut (default: --out)")
    args = ap.parse_args()

    preset = FAMILIES[args.family]
    pw, ph = PAPER[args.paper]
    per_page = preset["cols"] * preset["rows"]
    out_dir = Path(args.out)
    cut_dir = Path(args.cut_out) if args.cut_out else out_dir
    bambu_dir = Path(args.bambu_out) if args.bambu_out else out_dir
    run_id = uuid.uuid4().hex[:12]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    # load labels (skip + report mismatches, never scale)
    loaded, skipped = [], []
    for p in (Path(x) for x in args.labels):
        try:
            loaded.append((p, *load_label(p, preset)))
        except Exception as e:
            skipped.append((p.name, str(e)))
    if skipped:
        print("  SKIPPED (reported, not fixed):")
        for n, why in skipped:
            print(f"    - {n}: {why}")
    if not loaded:
        sys.exit("no usable labels")

    n_pages = (len(loaded) + per_page - 1) // per_page
    print(f"custom_sheet: {len(loaded)} labels -> {n_pages} page(s) of {per_page} "
          f"[{args.family} {preset['w']:g}x{preset['h']:g}mm on {args.paper} {pw:g}x{ph:g}mm] run={run_id}")

    manifest = {"run_id": run_id, "built_utc": stamp, "family": args.family,
                "paper": args.paper, "stem": args.name, "label_size_mm": [preset["w"], preset["h"]],
                "labels": [p.name for p, *_ in loaded], "skipped": skipped,
                "pages": [], "bambu": bool(args.bambu)}

    for page in range(n_pages):
        chunk = loaded[page * per_page:(page + 1) * per_page]
        suffix = "" if n_pages == 1 else f"_p{page + 1:02d}"
        # STABLE filename (no run-id) so regeneration overwrites in place and
        # never orphans an old copy. The run-id lives in the manifest only.
        stem = f"{args.name}_{args.paper}{suffix}"

        # print sheet
        proot = new_root(pw, ph, f"{args.name} — {pw:g}mm x {ph:g}mm — print at 100%")
        bg = etree.SubElement(proot, SVGNS + "rect")
        bg.set("x", "0"); bg.set("y", "0"); bg.set("width", "100%"); bg.set("height", "100%"); bg.set("fill", "white")
        # cut sheet (standard paper)
        croot = new_root(pw, ph, f"{args.name} cut — {pw:g}mm x {ph:g}mm — print at 100%")
        # bambu cut
        broot = None
        if args.bambu:
            bw, bh = PAPER["bambu-h2d-cut"]
            broot = new_root(bw, bh, f"{args.name} bambu cut — {bw:g}mm x {bh:g}mm")

        for i, (p, children, border, _sz) in enumerate(chunk):
            cx, cy = cell_xy(i, preset)
            # inline the label artwork in a translate group (renders natively,
            # honours textLength — see load_label). NOT a base64 <image>.
            g = etree.SubElement(proot, SVGNS + "g")
            g.set("transform", f"translate({cx:g},{cy:g})")
            for child in children:
                g.append(copy.deepcopy(child))
            croot.append(cut_outline(border, cx, cy, preset))
            if broot is not None:
                broot.append(cut_outline(border, cx, cy, preset))
        alignment_marks(proot, pw, ph)
        alignment_marks(croot, pw, ph)
        if broot is not None:
            bw, bh = PAPER["bambu-h2d-cut"]
            alignment_marks(broot, bw, bh)

        pfile = out_dir / f"{stem}_print.svg"
        cfile = cut_dir / f"{stem}_cut.svg"
        write_svg(proot, pfile); write_svg(croot, cfile)
        page_rec = {"page": page + 1, "stem": stem, "labels": len(chunk),
                    "print": pfile.name, "cut": cfile.name,
                    "print_sha256": sha256(pfile), "cut_sha256": sha256(cfile)}
        if broot is not None:
            bfile = bambu_dir / f"{stem}_bambu_cut.svg"
            write_svg(broot, bfile)
            page_rec["bambu_cut"] = bfile.name
            page_rec["bambu_cut_sha256"] = sha256(bfile)
        manifest["pages"].append(page_rec)
        print(f"  page {page + 1}: {pfile.name} + {cfile.name}"
              + (f" + {stem}_bambu_cut.svg" if broot is not None else ""))

    out_dir.mkdir(parents=True, exist_ok=True)
    mpath = out_dir / f"{args.name}_manifest.json"
    mpath.write_text(json.dumps(manifest, indent=2))
    print(f"  manifest: {mpath.name} (run {run_id}, {n_pages} page(s), {len(loaded)} labels)")


if __name__ == "__main__":
    main()
