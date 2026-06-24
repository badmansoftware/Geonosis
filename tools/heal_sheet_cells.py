#!/usr/bin/env python3
"""Re-embed print-sheet cells from the clean, healed Geonosis label files.

Box and materials print sheets carry base64-embedded copies of label artwork
taken from the upstream pipeline. Those copies are stale (e.g. YG018 carbon
fiber still red) and contain internal <metadata> blocks hidden from the
zero-trace grep by base64. This tool replaces each cell's data-URI payload
with the current Geonosis label file content, so sheets always match the
healed labels.

Spool sheets are intentionally NOT touched: their cells use a clean artwork
image plus direct <text> overlay nodes (healed by heal_long_names.py).

Cell geometry (image x/y/width/height) is never modified — the grid is the
invariant; the payload is the variable.

Usage:
  python3 tools/heal_sheet_cells.py [--dry-run]
"""

from __future__ import annotations

import argparse
import base64
import json
import re
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MASTER = REPO / "master"

# (sheet glob, labels dir) pairs — relative to master/
TARGETS = (
    ("box/print_true/sheets/*.svg", "box/print_true/labels"),
    ("materials/print_true/sheets/*/*.svg", "materials/print_true/labels"),
)

CELL_RE = re.compile(
    r'(<g[^>]*data-filename="(?P<fn>[^"]+)"[^>]*>.*?href="data:image/svg\+xml;base64,)'
    r'(?P<payload>[A-Za-z0-9+/=]+)'
    r'(".*?</g>)',
    re.S,
)


def heal_sheet(sheet: Path, labels_dir: Path, dry_run: bool) -> dict:
    text = sheet.read_text(encoding="utf-8")
    replaced, missing, unchanged = [], [], []

    def _repl(m: re.Match[str]) -> str:
        fn = m.group("fn")
        label = labels_dir / fn
        if not label.exists():
            missing.append(fn)
            return m.group(0)
        new_payload = base64.b64encode(label.read_bytes()).decode("ascii")
        if new_payload == m.group("payload"):
            unchanged.append(fn)
            return m.group(0)
        replaced.append(fn)
        return m.group(1) + new_payload + m.group(4)

    patched = CELL_RE.sub(_repl, text)
    if replaced and not dry_run:
        sheet.write_text(patched, encoding="utf-8")
    return {
        "sheet": str(sheet.relative_to(REPO)),
        "cells_replaced": len(replaced),
        "cells_unchanged": len(unchanged),
        "missing_labels": sorted(set(missing)),
        "replaced": sorted(set(replaced)),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Re-embed sheet cells from healed Geonosis labels.")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    reports = []
    for glob, labels in TARGETS:
        for sheet in sorted(MASTER.glob(glob)):
            reports.append(heal_sheet(sheet, MASTER / labels, args.dry_run))

    summary = {
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "dry_run": args.dry_run,
        "sheets": reports,
        "total_replaced": sum(r["cells_replaced"] for r in reports),
        "total_missing": sum(len(r["missing_labels"]) for r in reports),
    }
    print(json.dumps(summary, indent=2))
    if not args.dry_run and summary["total_replaced"]:
        out = REPO / "proof" / f"heal_sheet_cells_report_{summary['timestamp']}.json"
        out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return 1 if summary["total_missing"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

