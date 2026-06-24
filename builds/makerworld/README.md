# builds/makerworld — MakerWorld (Bambu Lab)

Generated packages for **MakerWorld (Bambu Lab)**. This folder is produced by
`tools/build_site.py` from `master/`; everything here EXCEPT this README is
git-ignored and must never be hand-edited. Rebuild, don't patch.

## Packaging rules
- **Layout:** ZIP attachment (model-centric host)
- **Accepted file types:** .3mf/.stl primary; label SVG+PDF bundled as a .zip 'print files' attachment
- **Image requirements:** Cover 1:1 square (min 1000px). Up to ~30 gallery images. No nudity/IP marks.

## Notes
Bambu H2D cut files (master/<fam>/bambu/cuts) are the differentiator here — pair each print sheet PDF with its H2D cut SVG.

## Build command
```bash
python3 tools/build_site.py --site makerworld --family spool [--family box --family materials] \
    [--variant print_true|bambu|all] [--with-pdf]
```
Each build writes `manifest.json` (run id, source commit, per-file sha256).
A build refuses to complete if any file fails the zero-trace gate.
