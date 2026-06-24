# builds/thangs — Thangs

Generated packages for **Thangs**. This folder is produced by
`tools/build_site.py` from `master/`; everything here EXCEPT this README is
git-ignored and must never be hand-edited. Rebuild, don't patch.

## Packaging rules
- **Layout:** Loose files OR zip
- **Accepted file types:** STL/3MF/STEP models; SVG/PDF as attachments
- **Image requirements:** Cover image; 3D viewer auto-thumbnails models.

## Notes
Free tier here; membership variants are a sales-sites concern, not this build.

## Build command
```bash
python3 tools/build_site.py --site thangs --family spool [--family box --family materials] \
    [--variant print_true|bambu|all] [--with-pdf]
```
Each build writes `manifest.json` (run id, source commit, per-file sha256).
A build refuses to complete if any file fails the zero-trace gate.
