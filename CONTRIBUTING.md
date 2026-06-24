# Contributing to Smith Maker

This project lives or dies on good language sets and honest translations — and
that part is wide open to you. Real languages, constructed languages, emoji,
symbols, secret codes: if it maps cleanly, it ships.

**The full guide lives in [`docs/contributing.md`](docs/contributing.md).** Start there.

Quick links:

- 📖 **[How contributing works](docs/contributing.md)** — what we take, what's off the table, and how to build/submit a set
- 📐 **[Language spec](docs/language-spec.md)** — the pack format and how a set is defined
- 🛠️ **[Tooling](tools/language-builder/)** — the utilities that build and validate a set
- 🆘 **[Support & PR process](docs/support.md)** — pull-request and ticket flow
- 🤝 **[Code of Conduct](CODE_OF_CONDUCT.md)**

## TL;DR

1. Copy an existing pack under `tools/language-builder/locale_data/packs/` and rename it.
2. Fill in your color/material mappings. Leave a documented gap rather than guessing.
3. Register your language code in `tools/language-builder/gen_languages.py`
   (`LANGS` + `LANG_LABELS`), then build it:
   `python3 tools/language-builder/gen_languages.py --langs <code> --dry-run`
4. Note your gaps. Open a PR with the pack and a one-line description.

New languages don't need the PDF tooling — the language builder is pure standard
library. See [`requirements.txt`](requirements.txt) for the optional render deps.
