#!/usr/bin/env python3
"""Regenerate the pdf/ mirror from all family SVGs using the fixed exporter
configuration (Inkscape: --export-area-page --export-dpi=72 --export-text-to-path).

Replaces the defective bare-cairosvg PDFs (font substitution + mm font-size
misscaling). Uses Inkscape shell mode for batch speed, then asserts every
PDF MediaBox against its SVG mm dimensions (tol 0.05mm).

Usage: python3 tools/regen_pdfs.py
"""
import shutil, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MASTER = REPO / "master"
FAMILIES = ["box", "materials", "spool"]
sys.path.insert(0, str(REPO / "tools"))
from geonosis_validate import check_mm, assert_pdf_size  # noqa: E402


def main():
    binpath = shutil.which("inkscape")
    if not binpath:
        raise SystemExit("inkscape not found on PATH")

    svgs = sorted(p for fam in FAMILIES for p in (MASTER / fam).rglob("*.svg"))
    print(f"{len(svgs)} SVGs to export")

    # Build inkscape shell-mode script
    lines = []
    pairs = []
    for svg in svgs:
        pdf = MASTER / "pdf" / svg.relative_to(MASTER).with_suffix(".pdf")
        pdf.parent.mkdir(parents=True, exist_ok=True)
        pairs.append((svg, pdf))
        lines.append(f"file-open:{svg}")
        lines.append("export-area-page")
        lines.append("export-dpi:72")
        lines.append("export-text-to-path")
        lines.append(f"export-filename:{pdf}")
        lines.append("export-do")
        lines.append("file-close")
    script = "\n".join(lines) + "\nquit\n"

    res = subprocess.run([binpath, "--shell"], input=script,
                         capture_output=True, text=True)
    if res.returncode != 0:
        print(res.stderr[-2000:])
        raise SystemExit("inkscape shell batch failed")

    fails = []
    for svg, pdf in pairs:
        if not pdf.exists():
            fails.append((svg, "pdf missing"))
            continue
        ok_mm, (w, h), msgs = check_mm(svg)
        if not ok_mm:
            fails.append((svg, "svg mm-dims: " + ";".join(msgs)))
            continue
        ok, (mw, mh) = assert_pdf_size(pdf, w, h)
        if not ok:
            fails.append((svg, f"MediaBox {mw:.3f}x{mh:.3f}mm != {w}x{h}mm"))
    print(f"exported {len(pairs)}, MediaBox failures: {len(fails)}")
    for svg, why in fails[:20]:
        print(f"  FAIL {svg.relative_to(REPO)}: {why}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()

