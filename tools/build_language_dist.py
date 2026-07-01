#!/usr/bin/env python3
"""
build_language_dist.py — generate the full distribution set for each language,
SUB-TO-LANGUAGE under master/languages/<lang>/.

For every language + filament family (spool, box), composes (from the already
localized labels):
  <lang>/<fam>/print_true/sheets/<fam>_full_*_pNN_{print,cut}.svg   (batch)
  <lang>/<fam>/print_true/sheets/by_type/<fam>_<slug>_*_{print,cut}.svg
  <lang>/<fam>/bambu/cuts/<fam>_full_*_bambu_cut.svg  (+ by_type/)
then exports a PDF mirror of EVERYTHING (labels + sheets + cuts) into
  <lang>/pdf/<...>.pdf
gating every SVG (zero-trace + mm + clean) and asserting every PDF MediaBox.

Composition only — labels are never re-rendered. NOTE: CJK/Arabic PDFs carry
the Arial font-substitution issue until the Adobe pass re-exports them.

Usage:
  python3 tools/build_language_dist.py [--langs de,fr|all] [--clean] [--no-pdf]
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LANGROOT = REPO / "master" / "languages"
TOOLS = REPO / "tools"
sys.path.insert(0, str(TOOLS))
import geonosis_validate as gv  # noqa: E402

ALL_LANGS = ["en", "emoji", "gya", "ar", "de", "es", "fr", "it", "ja", "ko",
             "nl", "pl", "pt", "ru", "zh"]
FAMILIES = ["spool", "box"]
PAPER_EXPECT = {"letter": (279.4, 215.9), "bambu": (300.0, 285.0)}


def slugs(labels):
    g = defaultdict(list)
    for p in labels:
        g[p.name.split("__")[0]].append(p)
    return g


def cs(files, fam, name, out, cut_out, bambu_out):
    cmd = ["python3", str(TOOLS / "custom_sheet.py"), *[str(f) for f in files],
           "--family", fam, "--paper", "letter", "--bambu", "--name", name,
           "-o", str(out), "--cut-out", str(cut_out), "--bambu-out", str(bambu_out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"custom_sheet failed ({name}):\n{r.stderr or r.stdout}")


def gate_svg(p):
    f = []
    if gv.zero_trace(p):
        f.append("zero-trace")
    if not gv.check_mm(p)[0]:
        f.append("mm")
    if not gv.check_clean(p)[0]:
        f.append("clean")
    return f


def expect_for(svg: Path):
    return "bambu" if "bambu" in svg.parts else "letter"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--langs", default="all")
    ap.add_argument("--clean", action="store_true")
    ap.add_argument("--no-pdf", action="store_true")
    args = ap.parse_args()
    langs = ALL_LANGS if args.langs == "all" else [x.strip() for x in args.langs.split(",")]
    ink = shutil.which("inkscape")
    if not ink and not args.no_pdf:
        sys.exit("inkscape not found (needed for PDFs)")

    grand_svg = grand_pdf = grand_fail = 0
    for lang in langs:
        base = LANGROOT / lang
        if not base.is_dir():
            print(f"  skip {lang}: not generated"); continue
        new_svgs = []
        for fam in FAMILIES:
            labels = sorted((base / fam / "print_true" / "labels").glob("*.svg"))
            if not labels:
                continue
            sheets = base / fam / "print_true" / "sheets"
            cuts = base / fam / "print_true" / "cuts"
            bambu = base / fam / "bambu" / "cuts"
            if args.clean:
                for d in (sheets, cuts, bambu):
                    shutil.rmtree(d, ignore_errors=True)
                # also clear this language's matching PDF mirror (no orphans)
                pdfbase = base / "pdf" / fam
                for d in (pdfbase / "print_true" / "sheets", pdfbase / "print_true" / "cuts",
                          pdfbase / "bambu" / "cuts"):
                    shutil.rmtree(d, ignore_errors=True)
            (sheets / "by_type").mkdir(parents=True, exist_ok=True)
            cuts.mkdir(parents=True, exist_ok=True)
            (bambu / "by_type").mkdir(parents=True, exist_ok=True)
            # full batch: print->sheets, cut->cuts, bambu->bambu/cuts
            cs(labels, fam, f"{fam}_full", sheets, cuts, bambu)
            # per-type: print+cut->sheets/by_type, bambu->bambu/cuts/by_type
            for slug, files in sorted(slugs(labels).items()):
                cs(files, fam, f"{fam}_{slug}", sheets / "by_type",
                   sheets / "by_type", bambu / "by_type")
            new_svgs += list(sheets.rglob("*.svg")) + list(cuts.glob("*.svg")) + list(bambu.rglob("*.svg"))
        # gate generated sheet svgs
        gfail = [(p, gate_svg(p)) for p in new_svgs]
        gfail = [(p, f) for p, f in gfail if f]
        if gfail:
            print(f"  !! {lang} gate failures: {len(gfail)} e.g. {gfail[0]}")
            grand_fail += len(gfail)
        # PDFs: mirror EVERY svg under base (labels+sheets+cuts) into base/pdf/
        n_pdf = 0
        if not args.no_pdf:
            all_svgs = [p for p in base.rglob("*.svg") if "pdf" not in p.parts]
            lines, pairs = [], []
            for s in all_svgs:
                pdf = base / "pdf" / s.relative_to(base).with_suffix(".pdf")
                pdf.parent.mkdir(parents=True, exist_ok=True)
                pairs.append((s, pdf))
                lines += [f"file-open:{s}", "export-area-page", "export-dpi:72",
                          "export-text-to-path", f"export-filename:{pdf}", "export-do", "file-close"]
            subprocess.run([ink, "--shell"], input="\n".join(lines) + "\nquit\n",
                           capture_output=True, text=True)
            for s, pdf in pairs:
                ew, eh = PAPER_EXPECT[expect_for(s)] if ("sheets" in s.parts or "cuts" in s.parts) else gv.check_mm(s)[1]
                if pdf.exists() and gv.assert_pdf_size(pdf, ew, eh)[0]:
                    n_pdf += 1
                else:
                    grand_fail += 1
        grand_svg += len(new_svgs)
        grand_pdf += n_pdf
        print(f"  {lang}: +{len(new_svgs)} sheet svgs, {n_pdf} PDFs"
              + (f", {len(gfail)} gate-fail" if gfail else ""))
    print(f"\nTOTAL: {grand_svg} sheet svgs, {grand_pdf} PDFs, {grand_fail} failures")
    if grand_fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
