# builds/cults3d-free — Cults3D (free listings)

Generated packages for **Cults3D (free listings)**. This folder is produced by
`tools/build_site.py` from `master/`; everything here EXCEPT this README is
git-ignored and must never be hand-edited. Rebuild, don't patch.

## Packaging rules
- **Layout:** ZIP (single downloadable archive per listing)
- **Accepted file types:** One .zip per free model; include SVG+PDF inside
- **Image requirements:** Square cover (min 600px); several gallery images.

## Notes
FREE listings only. Paid Cults3D goes through maker-vault, never this folder.

## Build command
```bash
python3 tools/build_site.py --site cults3d-free --family spool [--family box --family materials] \
    [--variant print_true|bambu|all] [--with-pdf]
```
Each build writes `manifest.json` (run id, source commit, per-file sha256).
A build refuses to complete if any file fails the zero-trace gate.
