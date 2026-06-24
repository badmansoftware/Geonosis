# builds/thingiverse — Thingiverse

Generated packages for **Thingiverse**. This folder is produced by
`tools/build_site.py` from `master/`; everything here EXCEPT this README is
git-ignored and must never be hand-edited. Rebuild, don't patch.

## Packaging rules
- **Layout:** ZIP recommended (flat file list, no nested dirs in UI)
- **Accepted file types:** STL/SVG/PDF accepted as 'Thing Files'; zip to preserve folder structure
- **Image requirements:** At least one image; first image is the thumbnail.

## Notes
Flatten or zip — Thingiverse shows a flat file list.

## Build command
```bash
python3 tools/build_site.py --site thingiverse --family spool [--family box --family materials] \
    [--variant print_true|bambu|all] [--with-pdf]
```
Each build writes `manifest.json` (run id, source commit, per-file sha256).
A build refuses to complete if any file fails the zero-trace gate.
