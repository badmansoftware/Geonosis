# builds/instructables — Instructables

Generated packages for **Instructables**. This folder is produced by
`tools/build_site.py` from `master/`; everything here EXCEPT this README is
git-ignored and must never be hand-edited. Rebuild, don't patch.

## Packaging rules
- **Layout:** Loose downloadable files attached to steps
- **Accepted file types:** PDF + SVG attachable per step; this is a tutorial format, not a file dump
- **Image requirements:** Step photos required; one cover photo.

## Notes
Package = the printable PDFs + a written 'how to apply' guide. Composition, not just files.

## Build command
```bash
python3 tools/build_site.py --site instructables --family spool [--family box --family materials] \
    [--variant print_true|bambu|all] [--with-pdf]
```
Each build writes `manifest.json` (run id, source commit, per-file sha256).
A build refuses to complete if any file fails the zero-trace gate.
