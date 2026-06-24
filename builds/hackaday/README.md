# builds/hackaday — Hackaday.io

Generated packages for **Hackaday.io**. This folder is produced by
`tools/build_site.py` from `master/`; everything here EXCEPT this README is
git-ignored and must never be hand-edited. Rebuild, don't patch.

## Packaging rules
- **Layout:** Loose files in project 'Files' section, or external link
- **Accepted file types:** PDF/SVG/ZIP attachments on a project page
- **Image requirements:** Project banner + logo.

## Notes
Often a pointer to the github-free repo rather than a re-upload.

## Build command
```bash
python3 tools/build_site.py --site hackaday --family spool [--family box --family materials] \
    [--variant print_true|bambu|all] [--with-pdf]
```
Each build writes `manifest.json` (run id, source commit, per-file sha256).
A build refuses to complete if any file fails the zero-trace gate.
