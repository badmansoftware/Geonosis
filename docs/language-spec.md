# Language Set Specification

### A Nemo Station / BadManSoftware Resource

A **language set** maps Bambu filament **material types** and **color names**
to your chosen terms or symbols. That's the whole job. Real language,
constructed language, emoji, or secret code — if it maps, it ships.

This document describes the pack format. For the *how-to* and submission
process, see [`contributing.md`](contributing.md).

---

## WHERE PACKS LIVE

```
tools/language-builder/locale_data/packs/
  elvish_pack.json      ← Gray Elvish, the reference implementation
  emoji_pack.json
  es_standard.json
  de_standard.json
  ...                   ← one *.json per language set
```

Start by copying the pack closest to what you're building (Gray Elvish is the
worked example) and renaming it.

---

## FILE SHAPE

A pack file is a single JSON object:

```json
{
  "packs": [ { ...one pack... } ],
  "schema": "<schema marker — leave as-is from the file you copied>"
}
```

Each entry inside `packs[].entries` is one **material type**, and carries the
color translations for that material:

```json
{
  "semantic_key": "filament.abs",      // stable identifier — DO NOT translate
  "display_text": "ABS",               // the material name as shown on the label
  "short_text":   "ABS",               // compact form for tight label fields
  "color_text_map": {                  // color key -> your translated term
    "black":  "Morn",
    "blue":   "Luine",
    "red":    "Carn",
    "white":  "Nim"
  }
}
```

### Field rules

| Field | Translate? | Notes |
|---|---|---|
| `semantic_key` | **No** | Stable join key (e.g. `filament.abs`). Identical across every language. Changing it breaks the mapping. |
| `display_text` | Yes | The material name as it appears on the label. |
| `short_text` | Yes | A compact variant for narrow fields. May equal `display_text`. |
| `color_text_map` | Yes (values only) | Keys (`black`, `azure`, `bambu_green`, …) are stable color identifiers — translate the **values**, never the keys. |

### Pack metadata

A pack also carries identifying metadata copied from the reference:
`language`, `version`, `maintainers`, `source`, and a `contribution_policy`.
Fill in `language` and `maintainers` for your set; keep the structure intact.

---

## RULES THAT MATTER

- **Stable keys are stable.** `semantic_key` and the keys of `color_text_map`
  are join identifiers shared across all sets. Translate values, never keys.
- **Honest gaps beat wrong guesses.** If you don't have a term, leave the
  English fallback and document it. A label that lies is worse than one that
  admits it's incomplete.
- **Cover the line, or say what you skipped.** Gray Elvish covers the full
  Bambu filament line with documented gaps. Match that bar or note the scope.
- **No scaling, no tracking, no hidden layers** — applies to anything the
  tooling emits from your pack. (See the repo guardrails.)

---

## BUILD & VALIDATE

Use the utilities in `tools/language-builder/` to generate and check a set
against the full Bambu line before submitting. A pack that doesn't build
cleanly isn't ready for a PR.

---

*Built at Geonosis. Shipped from Nemo Station.*
