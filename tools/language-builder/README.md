# language-builder — Geonosis localized label text

Standalone port of the language tool from the upstream locale pipeline. Runs
against `master/` with **no** internal package coupling and **no** network
calls.

## What was ported vs left behind
**Ported (the language tool):**
- `locale_adapter.py` — zero-dependency resolver (semantic_key [+ color_key] →
  localized string, english_standard fallback). Cleaned of the embedded
  internal snapshot import; now reads a plain `locale_data/` dir.
- `localize_label.py` — applies the resolver to a Geonosis label by swapping
  ONLY the material-name and colour-name `<text>` nodes. Artwork untouched.
- `locale_data/` — the 15 presentation packs + `translation_rules.json`.

**Left behind (not the language tool):** the web UI (`index.html`,
`script.js`, `styles.css`), release packaging, the `deep-translator`
machine-translation pipeline + cache (already-translated packs are shipped
as data), and the raw `spool_master_flattened_v1.json` provenance export.

## Locales (15 packs)
`english_standard` (en, baseline) · `emoji_pack` (emoji) ·
`elvish_pack` (qya, **Gray Elvish**) · 12 machine-translated `*_standard`:
ar de es fr it ja ko nl pl pt ru zh.

## Doctrine (matches the Geonosis guardrails)
- **No artwork change, ever.** `localize_label.py` is a content-only string
  substitution on two text nodes — every path/image/coordinate/font-size is
  preserved byte-for-byte. English localization is a verified no-op
  (byte-identical, pixel-identical @300dpi — the smoke-test invariant).
- **Report, never fix.** If the on-label text is absent from
  `english_standard` (e.g. label "TPU 90A" vs pack "TPU 90"), the node is
  left untouched and recorded as `unmatched`. Untranslated target terms
  (target == English) are recorded as `gaps` for the language's `GAPS.md`.
- **No overflow widening.** A substituted colour name wider than the master is
  flagged `overflow_risk` for `tools/heal_long_names.py`, never auto-scaled.

## Usage
```bash
# resolve checks
python3 tools/language-builder/locale_adapter.py

# localize one label or a tree
python3 tools/language-builder/localize_label.py \
    master/spool/print_true/labels --pack elvish_pack \
    -o master/languages/qya/spool/print_true/labels --report /tmp/qya.json
```
Output must still pass `tools/geonosis_validate.py gate` (Phase 3 runs it on
every generated file).

## Known source findings (Phase 3 to resolve, not auto-fixed)
- `filament.tpu_90`: pack display "TPU 90" ≠ label "TPU 90A".
- color key `cystal_blue` "Cystal Blue" (typo) ≠ label "Crystal Blue".
- Gray Elvish (`elvish_pack`) translates material names but most specific
  Bambu colour names fall back to English → gaps.
