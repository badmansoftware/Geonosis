# builds/github-free — GitHub (free release repo)

Generated packages for **GitHub (free release repo)**. This folder is produced by
`tools/build_site.py` from `master/`; everything here EXCEPT this README is
git-ignored and must never be hand-edited. Rebuild, don't patch.

## Packaging rules
- **Layout:** Loose files, committed in folder structure
- **Accepted file types:** SVG + PDF committed directly; release .zip attached to a GitHub Release
- **Image requirements:** README preview image(s); no platform image rules.

## Notes
Mirror of master subset + manifest.json. The most faithful 1:1 of a build.

## Build command
```bash
python3 tools/build_site.py --site github-free --family spool [--family box --family materials] \
    [--variant print_true|bambu|all] [--with-pdf]
```
Each build writes `manifest.json` (run id, source commit, per-file sha256).
A build refuses to complete if any file fails the zero-trace gate.
