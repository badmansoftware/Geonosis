# released/ — frozen shipment audit trail (COMMITTED)

Unlike `builds/` (regenerable, git-ignored), `released/` IS committed. It is
the immutable record of what actually shipped.

Layout: `released/<site>/<release_tag>/` — one folder per site per release,
containing the exact files uploaded plus the build `manifest.json`.

Workflow:
1. `tools/build_site.py` produces `builds/<site>/` (gated).
2. After James approves and uploads, copy that package to
   `released/<site>/<tag>/` and commit. Never edit a released folder.
