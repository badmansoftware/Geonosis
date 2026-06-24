# Contributing to Smith Maker

### A Nemo Station / BadManSoftware Resource

Thanks for wanting to make this better. This project lives or dies on good
language sets and honest translations, and that part is wide open to you.

Here's how it works, what we'll take, and what's off the table.

---

## WHAT YOU CAN CONTRIBUTE

- **New language sets** — official, unofficial, or things too questionable
  for even BadMan to endorse officially. Real languages, constructed
  languages, emoji, symbols, secret codes. If it maps cleanly, it ships.
- **Translation improvements** — fix or complete the Gray Elvish reference
  set, or any other set with documented gaps.
- **Tooling fixes** — bugs, clarity, and quality-of-life improvements to the
  Python utilities in `/tools`.
- **Docs** — corrections, clarifications, better examples.

---

## WHAT A LANGUAGE SET IS

A language set maps Bambu filament **color names** and **material types** to
your chosen terms or symbols. Nothing more exotic than that.

- **Gray Elvish** is the reference implementation. It covers the full Bambu
  filament line with translated terms where available and documented gaps
  where it isn't. Read it before you build your own — it's the worked example.
- Official sets are products. **Forked sets are yours** to do with as you
  please; the official tooling will point to any source you specify.

See `/docs/language-spec.md` for the full format, and
`/tools/language-builder` for the utilities that build and validate a set.

---

## BUILDING AND SUBMITTING A LANGUAGE SET

1. **Start from the reference.** Copy an existing pack under
   `tools/language-builder/locale_data/packs/` (the Gray Elvish / `elvish_pack.json`
   set is the model) and rename it for your language.
2. **Fill in the mappings.** Provide your terms for the color and material
   keys. Leave a documented gap rather than guessing — an honest gap is more
   useful than a wrong translation.
3. **Register your language code.** Add it to `LANGS` and `LANG_LABELS` in
   `tools/language-builder/gen_languages.py` (one line each), mapping the code
   to your pack name and a human-readable label.
4. **Build it** with the language-builder utilities and confirm it generates
   without errors against the full Bambu line:
   `python3 tools/language-builder/gen_languages.py --langs <code> --dry-run`
   (no third-party dependencies — pure standard library).
5. **Note your gaps** in the pack so users know what's translated and what
   still falls back to English.
6. **Open a pull request** with the new pack and a one-line description of the
   set (language, scope, and any known gaps).

Translation-improvement PRs follow the same path: change the pack, note what
you fixed, open the PR. Contributions from native or expert speakers — Elvish
very much included — are especially welcome.

See `/docs/support.md` for the pull-request and ticket process.

---

## GROUND RULES

- **Be honest about gaps.** A label that lies about what it says is worse than
  one that admits it's still in English.
- **Don't scale artwork.** Physical label size is hardware truth. Tooling and
  PRs must preserve true print size; never resize a label to "make it fit."
- **Keep it clean.** No tracking, no phone-home, no hidden instruction layers
  in anything you submit. What you see in the file is all there is.
- **One set per PR** where practical. It keeps review honest and history clean.

---

## WHAT'S NOT PUBLIC

This repository is the **public, shippable** distribution of Smith Maker. The
internal Smith Maker source format, the export pipeline, and the
master-generation engine are **not** part of this repo and are not open for
contribution. PRs that attempt to reconstruct, reintroduce,
or depend on that private pipeline will be declined. Everything you need to
build a language set is already here.

---

## LICENSING OF CONTRIBUTIONS

By submitting a contribution you agree it is licensed under this project's
terms (see [`/LICENSING.md`](../LICENSING.md) for the full breakdown):

- **Label artifacts (SVG/PDF, sheets, cut files):** CC BY-NC 4.0
- **Language packs (Gray Elvish + community sets):** CC BY 4.0
- **Python tooling:** Apache 2.0
- **Documentation:** CC BY 4.0

You must have the right to contribute what you submit, and you grant the
project the right to distribute it under the license matching its type above.
Don't submit translations, fonts, or artwork you don't have the rights to.

---

*This is a BadManSoftware project. We have standards. They are just ours.*

*Built at Geonosis. Shipped from Nemo Station.*
