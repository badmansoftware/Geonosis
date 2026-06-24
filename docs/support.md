# Support, Pull Requests & Tickets

### A Nemo Station / BadManSoftware Resource

How to get help, report a problem, or get a contribution merged. Read
[`contributing.md`](contributing.md) first if you're submitting a language set —
this doc is the process around it.

---

## OPENING A TICKET (ISSUE)

Use a GitHub issue for: a label that prints or cuts wrong, a tool that errors,
a translation that's flat wrong, or a documentation gap.

Include:

- **What you expected** vs. **what happened.**
- The **filament type and color** (or the exact label / file involved).
- For tooling: the **command you ran** and the **full error output**.
- For print/cut issues: your **media** (standard paper vs. Bambu-sized sheet)
  and confirmation you printed at **100% (not auto-fit)** and **calibrated the
  camera** before cutting. (Yes, again. See the README field notes.)

A good ticket is reproducible. A ticket that says "it's broken" gets the same
answer you'd give your wife: try unplugging and replugging it.

---

## OPENING A PULL REQUEST

For language sets and translation fixes, follow the steps in
[`contributing.md`](contributing.md). In general:

- **One logical change per PR.** A new language set, a translation fix, or a
  tooling fix — not all three at once. It keeps review honest and history clean.
- **Describe it in one line:** what the set/fix is, its scope, and any known
  gaps.
- **Confirm it builds.** A pack must generate cleanly against the full Bambu
  line; a tooling change must not break the other utilities.
- **Stay inside the public boundary.** PRs that try to reconstruct or depend on
  the private Smith Maker pipeline will be declined — see
  [`contributing.md`](contributing.md#whats-not-public).

---

## WHAT TO EXPECT

- Language sets use **maintainer review** before merge — direct edits to
  curated packs aren't auto-accepted.
- This is a community project run on operational time, not a paid support desk.
  Clear, reproducible reports get handled faster. Vague ones wait.
- Translation contributions from native or expert speakers — Elvish very much
  included — move to the front of the line.

---

## COMMERCIAL & TRADEMARK QUESTIONS

Licensing of the labels is **CC BY-NC 4.0** — commercial use is a separate
grant. Commercial licenses for label artifacts are available from
**BadManSoftware**; see [`/LICENSING.md`](../LICENSING.md) for the full
breakdown and the Bambu trademark notice. Trademark/branding questions are the
user's responsibility and are not answered through issues.

---

*This is a BadManSoftware project. We have standards. They are just ours.*

*Built at Geonosis. Shipped from Nemo Station.*
