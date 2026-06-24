# builds/grabcad — GrabCAD

Generated packages for **GrabCAD**. This folder is produced by
`tools/build_site.py` from `master/`; everything here EXCEPT this README is
git-ignored and must never be hand-edited. Rebuild, don't patch.

## Packaging rules
- **Layout:** Loose files; native-CAD friendly
- **Accepted file types:** STEP/IGES/native CAD preferred; SVG/PDF accepted as supporting docs
- **Image requirements:** Rendered preview required.

## Notes
CAD audience — lead with cut geometry; PDFs are supporting docs.

## Build command
```bash
python3 tools/build_site.py --site grabcad --family spool [--family box --family materials] \
    [--variant print_true|bambu|all] [--with-pdf]
```
Each build writes `manifest.json` (run id, source commit, per-file sha256).
A build refuses to complete if any file fails the zero-trace gate.
