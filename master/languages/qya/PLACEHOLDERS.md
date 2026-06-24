# Placeholder terms — Elvish (Gray Dialect) (`qya` / pack `elvish_pack`)

These terms are **present in `elvish_pack.json`** (so the labels render in-dialect
rather than silently falling back to English), but they are **constructed
placeholders, NOT maintainer-verified translations**. They do not appear in
`GAPS.md` because that file only records terms *absent* from the pack; this file
is the companion record required by Geonosis doctrine for pack-present
placeholders. Replace with verified terms during the later golden/locale
reconciliation, then delete the corresponding rows here.

Construction follows the pack's own established fallback convention — an
unverified modifier is Elvish-ized by appending `ë` to the English root (cf.
existing `tangerine_yellow → "Tangerineë Malen"`, `olive → "Oliveë"`).

## PLA Pure (added 2026-06-20, MakerWorld hot-fix)

| semantic_key / color_key | English | Elvish (this pack) | Status |
|--|--|--|--|
| `filament.pla_pure` (line name) | PLA Pure | **PLA Poicë** | placeholder (`poica` = Q. "clean/pure"; form unverified) |
| `pure_white` | Pure White | **Poicë Nim** | placeholder (`nim` = "white" is verified; modifier unverified) |
| `absolute_black` | Absolute Black | **Absoluteë Morn** | placeholder (`morn` = "black" is verified; modifier English-ë) |
| `milky_pink` | Milky Pink | **Milkyë Sereg** | placeholder (`sereg` = "pink" is verified; modifier English-ë) |
| `apricot` | Apricot | **Apricotë** | placeholder (English-ë, cf. `Oliveë`) |
| `baby_blue` | Baby Blue | Babië Luine | **VERIFIED** — pre-existing pack term, reused (not a placeholder) |

**True-translated vs placeholder for the 5 Pure labels:**
- `pla_pure__17600` (Baby Blue) — color name **true-translated** (line name placeholder).
- `pla_pure__17100/17101/17200/17300` — color name **placeholder** (line name placeholder).