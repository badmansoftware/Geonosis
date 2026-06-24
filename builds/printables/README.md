# builds/printables — Printables (Prusa)

Generated packages for **Printables (Prusa)**. This folder is produced by
`tools/build_site.py` from `master/`; everything here EXCEPT this README is
git-ignored and must never be hand-edited. Rebuild, don't patch.

## Packaging rules
- **Layout:** Loose files OR zip; both accepted
- **Accepted file types:** STL/3MF as models; SVG and PDF allowed as 'Other files'
- **Image requirements:** At least one render/photo; 1:1 cover preferred (min 1280px).

## Notes
Good home for the Standard (print_true) Letter sheet+cut PDFs.

## Build command
```bash
python3 tools/build_site.py --site printables --family spool [--family box --family materials] \
    [--variant print_true|bambu|all] [--with-pdf]
```
Each build writes `manifest.json` (run id, source commit, per-file sha256).
A build refuses to complete if any file fails the zero-trace gate.
