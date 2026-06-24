#!/usr/bin/env python3
"""
build_type_sheets.py — Phase 4 batch: one sheet+cut(+Bambu cut) per filament
TYPE, for the filament families (spool, box), composed from master labels.

Groups master labels by type slug (filename prefix before '__'), then calls
custom_sheet.py per type. Outputs land in the master tree:
  master/<fam>/print_true/sheets/by_type/<fam>_<slug>_letter_<id>_print.svg
  master/<fam>/print_true/sheets/by_type/<fam>_<slug>_letter_<id>_cut.svg
  master/<fam>/bambu/cuts/by_type/<fam>_<slug>_letter_<id>_bambu_cut.svg

Then exports a PDF per sheet (Inkscape shell mode) into the master/pdf mirror
and asserts each PDF's MediaBox (letter sheets 279.4x215.9, Bambu 300x285).
Every generated SVG is run through the zero-trace gate. Refuses to finish if
any SVG fails the gate or any PDF MediaBox is wrong.

Usage:
  python3 tools/build_type_sheets.py [--families spool,box] [--no-pdf] [--clean]
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MASTER = REPO / "master"
TOOLS = REPO / "tools"
sys.path.insert(0, str(TOOLS))
import geonosis_validate as gv  # noqa: E402

PAPER_EXPECT = {"letter": (279.4, 215.9), "bambu": (300.0, 285.0)}


def slugs_for(fam):
    labels = sorted((MASTER / fam / "print_true" / "labels").glob("*.svg"))
    groups = defaultdict(list)
    for p in labels:
        groups[p.name.split("__")[0]].append(p)
    return groups


def gate_svg(path: Path):
    fails = []
    if gv.zero_trace(path) != 0:
        fails.append("zero-trace")
    ok_mm, _, _ = gv.check_mm(path)
    if not ok_mm:
        fails.append("mm-dims")
    ok_clean, bad = gv.check_clean(path)
    if not ok_clean:
        fails.append("clean:" + ",".join(bad))
    return fails


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--families", default="spool,box")
    ap.add_argument("--no-pdf", action="store_true")
    ap.add_argument("--clean", action="store_true", help="remove existing by_type dirs first")
    args = ap.parse_args()
    families = [f.strip() for f in args.families.split(",")]

    svg_outputs = []   # (svg_path, expect_key)
    for fam in families:
        sheets_dir = MASTER / fam / "print_true" / "sheets" / "by_type"
        bambu_dir = MASTER / fam / "bambu" / "cuts" / "by_type"
        if args.clean:
            shutil.rmtree(sheets_dir, ignore_errors=True)
            shutil.rmtree(bambu_dir, ignore_errors=True)
            # also clear the matching PDF mirror so no old PDFs are orphaned
            shutil.rmtree(MASTER / "pdf" / fam / "print_true" / "sheets" / "by_type", ignore_errors=True)
            shutil.rmtree(MASTER / "pdf" / fam / "bambu" / "cuts" / "by_type", ignore_errors=True)
        sheets_dir.mkdir(parents=True, exist_ok=True)
        bambu_dir.mkdir(parents=True, exist_ok=True)

        groups = slugs_for(fam)
        print(f"=== {fam}: {len(groups)} types ===")
        for slug, files in sorted(groups.items()):
            name = f"{fam}_{slug}"
            cmd = ["python3", str(TOOLS / "custom_sheet.py"), *[str(f) for f in files],
                   "--family", fam, "--paper", "letter", "--bambu",
                   "--name", name, "-o", str(sheets_dir), "--bambu-out", str(bambu_dir)]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                sys.exit(f"custom_sheet failed for {name}:\n{res.stderr or res.stdout}")
        # collect this family's generated svgs
        for p in sorted(sheets_dir.glob(f"{fam}_*_print.svg")) + sorted(sheets_dir.glob(f"{fam}_*_cut.svg")):
            svg_outputs.append((p, "letter"))
        for p in sorted(bambu_dir.glob(f"{fam}_*_bambu_cut.svg")):
            svg_outputs.append((p, "bambu"))

    print(f"generated {len(svg_outputs)} sheet SVGs")

    # gate every SVG
    gate_fails = [(p, gate_svg(p)) for p, _ in svg_outputs]
    gate_fails = [(p, f) for p, f in gate_fails if f]
    if gate_fails:
        print("!! GATE FAILURES:")
        for p, f in gate_fails[:20]:
            print(f"   {p.relative_to(MASTER)}: {f}")
        sys.exit(2)
    print(f"zero-trace gate: {len(svg_outputs)}/{len(svg_outputs)} pass")

    if args.no_pdf:
        print("(--no-pdf: skipping PDF export)")
        return

    # PDF export via Inkscape shell mode -> master/pdf mirror
    ink = shutil.which("inkscape")
    if not ink:
        sys.exit("inkscape not found on PATH (needed for sheet PDFs)")
    pairs = []
    lines = []
    for svg, _ in svg_outputs:
        pdf = MASTER / "pdf" / svg.relative_to(MASTER).with_suffix(".pdf")
        pdf.parent.mkdir(parents=True, exist_ok=True)
        pairs.append((svg, pdf))
        lines += [f"file-open:{svg}", "export-area-page", "export-dpi:72",
                  "export-text-to-path", f"export-filename:{pdf}", "export-do", "file-close"]
    print(f"exporting {len(pairs)} PDFs via Inkscape shell...")
    res = subprocess.run([ink, "--shell"], input="\n".join(lines) + "\nquit\n",
                         capture_output=True, text=True)
    if res.returncode != 0:
        print(res.stderr[-1500:])
        sys.exit("inkscape shell batch failed")

    # assert MediaBox on every PDF
    pdf_fails = []
    for (svg, pdf), (_, key) in zip(pairs, svg_outputs):
        ew, eh = PAPER_EXPECT[key]
        if not pdf.exists():
            pdf_fails.append((pdf, "missing"))
            continue
        ok, (mw, mh) = gv.assert_pdf_size(pdf, ew, eh)
        if not ok:
            pdf_fails.append((pdf, f"MediaBox {mw:.2f}x{mh:.2f} != {ew}x{eh}"))
    print(f"PDF MediaBox: {len(pairs) - len(pdf_fails)}/{len(pairs)} OK")
    if pdf_fails:
        print("!! PDF FAILURES:")
        for p, why in pdf_fails[:20]:
            print(f"   {p.relative_to(MASTER)}: {why}")
        sys.exit(3)

    n_letter = sum(1 for _, k in svg_outputs if k == "letter")
    n_bambu = sum(1 for _, k in svg_outputs if k == "bambu")
    print(f"\nDONE: {len(svg_outputs)} sheet SVGs ({n_letter} letter print/cut, {n_bambu} bambu cut) "
          f"+ {len(pairs)} PDFs, all gated + MediaBox-checked.")


if __name__ == "__main__":
    main()
