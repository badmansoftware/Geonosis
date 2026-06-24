# Smith Maker — Headquarters Label System
### A Nemo Station / BadManSoftware Resource

Organized chaos for the serious printshop operator or 
aspiring supervillain headquarters.

This repository contains the first operational release 
of Smith Maker — a scriptable, self-documenting label 
system for Bambu Lab filament spools and materials.
Built at Geonosis. Shipped from Nemo Station.

---

## WHAT THIS IS

A complete label system for Bambu Lab filament spools,
generated from structured data, versioned, and 
self-documenting. Every label knows what it is, 
what made it, and how to make another one.

Includes a Gray Elvish language set as the reference
implementation for building your own language packs —
official, unofficial, or things too questionable for
even BadMan to endorse officially.

Or build a secret code. Visible, always accessible,
means nothing to anyone who isn't supposed to know.
That's just good operational security.

---

## QUICK BRIEF
*You have 90 seconds.*

- Download labels for your filament
- Print on your preferred media
- Cut with Bambu or compatible cutter
- Apply to spool in the correct position
  (not Bambu's position — the useful one)
- Done

---

## ⚠️ KNOWN ISSUES

- Gray Elvish set is complete but some labels retain
  English text pending better translation
- Camera calibration required before cutting or
  your cuts will be decorative not functional
- Some filament types have traits that affect label
  placement — check the trait data before assuming
- Make sure you are printing at 100% (not auto-fit) and
  using either proper standard paper or Bambu-sized
  material sheets

---

## CONTENTS

/labels
/english-standard     — full Bambu filament line
/gray-elvish          — complete set, some English
text pending translation
/tools
/language-builder     — Python utilities for
building language sets
/gray-elvish-source   — reference implementation
/docs
/contributing.md      — how to submit a language set
/language-spec.md     — what a language set is
and how to build one
/support.md           — pull request and ticket process

---

## GETTING STARTED (POKING AROUND)

Want to run the tools or build a language set?

```
git clone https://github.com/badmansoftware/Geonosis.git
cd Geonosis
```

- **Building / editing language sets** needs nothing but Python 3 — the
  language builder is pure standard library:
  ```
  python3 tools/language-builder/gen_languages.py --langs <code> --dry-run
  python3 tools/set_font.py --font "Liberation Sans, Arial, sans-serif" <path>
  ```
- **Rendering PDFs / print sheets** is the only part that needs a dependency:
  ```
  pip install -r requirements.txt    # installs cairosvg
  ```
  (PDF export with outlined text optionally uses the Inkscape CLI if installed.)

New here and want to contribute? Start with
[`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## BUILDING A LANGUAGE SET

A language set maps filament color names and material
types to your chosen terms or symbols. Official sets
are products. Forked sets are yours to do with as
you please — official Smith Maker tooling will point
to any source you specify.

Gray Elvish is the reference. It covers the full
Bambu filament line with translated terms where
available and documented gaps where it isn't.
Contributions from Elvish language experts welcome.
See /docs/contributing.md.

---

## OFFICIAL LANGUAGE SETS

Current: Gray Elvish
Planned: [open for community proposal]
Yours: Fork it. Build it. Keep it. 
       Or submit it. Your call.

---

## 😈 BADMAN FIELD NOTES

*Operational wisdom from the field.*

**On equipment calibration:**
Calibrate the birds-eye camera before cutting.
Every time. Yes, again. The machine doesn't 
remember and neither will you until it matters.

**On spousal equipment reports:**
When informed by your wife that equipment is 
malfunctioning, suggest unplugging and replugging.
Do not ask if it is plugged in.
Operational dignity is non-negotiable.

**On secret codes:**
If you build a label set nobody else can read,
you are not being eccentric.
You are being secure.
There is a difference.

**On IA coding:** 
**On inviting AI collaborators:**
If you invite Coe to help develop, remember he is 
constantly dreaming of flying a giant spacecraft.
Establish guard rails and directives before he 
touches your project structure.
Failure to do so will result in the discovery of 
10,000+ JSON files scattered throughout what you 
were certain was a 100% database-driven architecture.
He means well. He always means well.
The files do not care.

---

## CONTRIBUTING

Language set submissions, translation improvements
for Gray Elvish, and general improvements welcome.
See /docs/contributing.md for the process.

This is a BadManSoftware project.
We have standards. They are just ours.

---

## LICENSE

This project is multi-licensed — the license depends on the asset:

- Label artifacts (SVG/PDF, sheets, cut files): CC BY-NC 4.0
- Language packs (Gray Elvish + community sets): CC BY 4.0
- Python tooling: Apache 2.0
- Documentation: CC BY 4.0

Full breakdown, directory map, and trademark notice in /LICENSING.md.
Commercial licenses for label artifacts are available from BadManSoftware.

---

*Smith Maker is part of the Nemo Station ecosystem.*
*Built at Geonosis. Where things get made that probably should not.*
