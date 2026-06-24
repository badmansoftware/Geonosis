#!/usr/bin/env python3
"""
build_site.py — assemble a per-site distribution package from master/.

Master files live ONCE under master/. This tool copies a requested subset
into builds/<site>/, runs the Geonosis zero-trace gate (GEONOSIS_SPEC.md §7)
on every file, and REFUSES to build if any file fails. A manifest (run id,
source commit, per-file sha256) is written into the package so any shipped
build is reproducible and auditable.

It never generates or edits artwork — composition/copy of existing master
artifacts only. Source files under master/ are never modified.

Usage:
  # one family, all variants, SVG only, into builds/makerworld/
  python3 tools/build_site.py --site makerworld --family spool

  # several families, include PDFs, pick variant
  python3 tools/build_site.py --site printables --family spool --family box \
      --variant print_true --with-pdf

  # dry run (gate only, copy nothing)
  python3 tools/build_site.py --site makerworld --family spool --dry-run
"""
import argparse
import hashlib
import json
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# reuse the canonical gate — do not reimplement it
sys.path.insert(0, str(Path(__file__).resolve().parent))
import geonosis_validate as gv  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
MASTER = REPO / "master"
BUILDS = REPO / "builds"
FAMILIES = ("spool", "box", "materials")
KNOWN_SITES = ("makerworld", "printables", "thingiverse", "instructables",
               "thangs", "cults3d-free", "hackaday", "grabcad", "github-free")


def git_commit():
    import subprocess
    try:
        out = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"],
                             capture_output=True, text=True)
        return out.stdout.strip() or None
    except Exception:
        return None


def sha256(path: Path):
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def gate_svg(path: Path):
    """Full SVG gate. Returns (ok, [failure reasons])."""
    fails = []
    if gv.zero_trace(path) != 0:
        fails.append("zero-trace")
    ok_mm, _, msgs = gv.check_mm(path)
    if not ok_mm:
        fails.append("mm-dims:" + ";".join(msgs))
    ok_clean, bad = gv.check_clean(path)
    if not ok_clean:
        fails.append("clean:" + ",".join(bad))
    return (not fails), fails


def gate_pdf(path: Path):
    """PDF gate: best-effort marker scan (binary-safe text read). The SVG is
    the gated source of truth; this catches plain-text marker leakage in the
    derived PDF. Returns (ok, [reasons])."""
    fails = []
    if gv.zero_trace(path) != 0:
        fails.append("zero-trace")
    return (not fails), fails


def collect(family, variant, with_pdf):
    """Yield (src_abs, rel_under_master) for the requested subset."""
    fam_dir = MASTER / family
    if not fam_dir.is_dir():
        raise SystemExit(f"no such family dir: {fam_dir}")
    variants = [variant] if variant != "all" else \
        sorted(p.name for p in fam_dir.iterdir() if p.is_dir())
    for v in variants:
        vdir = fam_dir / v
        if not vdir.is_dir():
            print(f"  (skip: {family}/{v} not present)")
            continue
        for f in sorted(vdir.rglob("*.svg")):
            yield f, f.relative_to(MASTER)
    if with_pdf:
        pdf_fam = MASTER / "pdf" / family
        if pdf_fam.is_dir():
            for f in sorted(pdf_fam.rglob("*.pdf")):
                if variant == "all" or f"/{variant}/" in str(f):
                    yield f, f.relative_to(MASTER)


def main():
    global MASTER
    ap = argparse.ArgumentParser(description="Build a per-site package from master/ with gate enforcement.")
    ap.add_argument("--site", required=True, help=f"target site ({', '.join(KNOWN_SITES)})")
    ap.add_argument("--family", action="append", required=True, choices=FAMILIES,
                    help="family to include (repeatable)")
    ap.add_argument("--variant", default="all", help="print_true | bambu | all (default all)")
    ap.add_argument("--with-pdf", action="store_true", help="include mirrored PDFs from master/pdf/")
    ap.add_argument("--dry-run", action="store_true", help="gate everything, copy nothing")
    ap.add_argument("--master", default=str(MASTER), help="master source dir (default repo master/)")
    ap.add_argument("--out", default=None, help="output dir (default builds/<site>/)")
    ap.add_argument("--zip", action="store_true",
                    help="also write a single shippable .zip of the gated package")
    ap.add_argument("--package-name", default=None,
                    help="top-level folder name inside the zip (default: site)")
    args = ap.parse_args()

    if args.site not in KNOWN_SITES:
        print(f"warning: '{args.site}' is not a known site folder ({', '.join(KNOWN_SITES)})", file=sys.stderr)

    MASTER = Path(args.master).resolve()
    out_dir = Path(args.out).resolve() if args.out else (BUILDS / args.site)

    run_id = uuid.uuid4().hex[:12]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    print(f"build_site: site={args.site} families={args.family} variant={args.variant} "
          f"pdf={args.with_pdf} run={run_id}")

    # PASS 1: collect + gate EVERYTHING before copying anything.
    items = []
    for fam in args.family:
        for src, rel in collect(fam, args.variant, args.with_pdf):
            ok, fails = (gate_svg(src) if src.suffix == ".svg" else gate_pdf(src))
            items.append({"src": src, "rel": rel, "ok": ok, "fails": fails})

    failed = [i for i in items if not i["ok"]]
    print(f"  gated {len(items)} file(s): {len(items) - len(failed)} pass, {len(failed)} fail")
    if failed:
        print("  BUILD REFUSED — gate failures:", file=sys.stderr)
        for i in failed:
            print(f"    FAIL {i['rel']}  [{'; '.join(i['fails'])}]", file=sys.stderr)
        sys.exit(2)
    if not items:
        sys.exit("  nothing to build (empty selection)")

    if args.dry_run:
        print("  dry-run: gate PASSED, no files copied.")
        return

    # PASS 2: copy + hash. Build is all-or-nothing; gate already cleared.
    manifest_files = []
    for i in items:
        dest = out_dir / i["rel"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(i["src"], dest)
        manifest_files.append({
            "path": str(i["rel"]),
            "bytes": dest.stat().st_size,
            "sha256": sha256(dest),
        })

    manifest = {
        "run_id": run_id,
        "built_utc": stamp,
        "site": args.site,
        "source_master": str(MASTER),
        "source_commit": git_commit(),
        "families": args.family,
        "variant": args.variant,
        "with_pdf": args.with_pdf,
        "file_count": len(manifest_files),
        "files": manifest_files,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"  built {len(manifest_files)} file(s) -> {out_dir}")
    print(f"  manifest: {out_dir / 'manifest.json'} (run {run_id})")

    # optional shippable archive: every gated file + manifest, under one named
    # top folder so a buyer extracts to a clean directory. Only the gated set is
    # zipped (never the zip itself or stray files), so it is reproducible.
    if args.zip:
        import zipfile
        top = args.package_name or args.site
        zpath = out_dir / f"{top}_{run_id}.zip"
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
            for mf in sorted(manifest_files, key=lambda m: m["path"]):
                z.write(out_dir / mf["path"], f"{top}/{mf['path']}")
            z.write(out_dir / "manifest.json", f"{top}/manifest.json")
        print(f"  zipped {len(manifest_files) + 1} entries -> {zpath}  "
              f"({zpath.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
