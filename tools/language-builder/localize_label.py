#!/usr/bin/env python3
"""
localize_label.py — produce a localized copy of a Geonosis label by swapping
ONLY its two language-bearing text nodes (material name + colour name).

Doctrine (Geonosis guardrails):
  * Artwork is never scaled or redrawn. This tool performs string substitution
    on <text> node CONTENT only — every path, image, coordinate and font-size
    is left byte-for-byte intact (heal_long_names.py-style surgical edit).
  * For the English pack the resolved strings equal the on-label strings, so a
    localized English label is byte-identical to its master (a true no-op —
    the smoke-test invariant).
  * Source disagreements are REPORTED, never fixed: if the on-label material or
    colour text is not present in english_standard (e.g. label "TPU 90A" vs
    pack "TPU 90"), the node is left untouched and recorded as `unmatched`.
  * Untranslated target terms (target == English) are recorded as `gaps`, not
    silently accepted — Phase 3 writes these into each language's GAPS.md.

It does NOT widen overflow: if a substituted colour name is wider than the
master's, that is flagged (`overflow_risk`) for heal_long_names to resolve,
never auto-scaled here.

Usage:
  python3 localize_label.py LABEL.svg --pack elvish_pack -o OUT_DIR
  python3 localize_label.py LABELS_DIR --pack fr_standard -o OUT_DIR [--report r.json]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from locale_adapter import LocaleAdapter  # noqa: E402

TEXT_NODE_RE = re.compile(r"<text(?P<attrs>[^>]*)>(?P<content>[^<]*)</text>")
TEXT_FULL_RE = re.compile(r"<text(?P<attrs>[^>]*)>(?P<content>[^<]*)</text>")
FONT_SIZE_RE = re.compile(r'font-size="([0-9.]+)mm"')
# the sanctioned localization keys baked into each label: semantic_key + colour_key
TYPEKEY_RE = re.compile(r'<text([^>]*\bdata-type-key="([^"]*)"[^>]*)>([^<]*)</text>')
COLORKEY_RE = re.compile(r'<text([^>]*\bdata-color-key="([^"]*)"[^>]*)>([^<]*)</text>')


def name_slot_content(svg_text: str) -> str | None:
    """The material-name slot is the bold (`font-weight="700"`) text node with
    the largest font-size — robust across families (spool's name is start-
    anchored, box's has no explicit anchor; the tiny AMS badges are also bold
    but small). Used only to name an unmatched material in the report."""
    best, best_fs = None, -1.0
    for m in TEXT_FULL_RE.finditer(svg_text):
        attrs = m.group("attrs")
        if 'font-weight="700"' not in attrs:
            continue
        fs = FONT_SIZE_RE.search(attrs)
        fs_v = float(fs.group(1)) if fs else 0.0
        if fs_v > best_fs:
            best, best_fs = m.group("content").strip(), fs_v
    return best
ROOT_W_RE = re.compile(r'<svg[^>]*\bwidth="([0-9.]+)mm"')

# Colour-name sizing follows the GOLDEN, via tools/healing/name_sizing.json:
# the colour name is NOT letter-fit with textLength; instead its font-size steps
# DOWN through tiers so it fits at natural width (the golden's method). The spec
# gives per-tier max name lengths. Box keeps a single fallback (it shipped with
# upstream sizing and matched the golden, so no per-tier data was needed).
import json as _json
_SPEC_PATH = Path(__file__).resolve().parents[1] / "healing" / "name_sizing.json"
try:
    _SPEC = _json.loads(_SPEC_PATH.read_text())
except Exception:
    _SPEC = {}


# All colour-name sizing values come from tools/healing/name_sizing.json (data,
# not hardcoded) so the golden-error fixes are editable/removable there. Falls
# back to sane defaults if the spec is missing.
_SP_CFG = (((_SPEC.get("families") or {}).get("spool") or {}).get("color_name")) or {}
_SPOOL_FIELD_MM = _SP_CFG.get("field_width_mm", 23.0)   # usable width (x=12.50 -> ~35.5)
_ADV = _SP_CFG.get("advance_per_latin_unit", 1.4)       # effective per-unit advance (mm fonts render wide)
_COMPACT_FS = f"{(_SP_CFG.get('over_length') or {}).get('compact_font_mm', 0.9):g}mm"


def _wunits(text: str) -> float:
    """Width in 'Latin character' units. CJK / full-width glyphs are ~2x wide,
    so a char-count rule mis-sizes them — count them as 2."""
    u = 0.0
    for ch in text:
        o = ord(ch)
        wide = (0x1100 <= o <= 0x115F or 0x2E80 <= o <= 0xA4CF or
                0xAC00 <= o <= 0xD7A3 or 0xF900 <= o <= 0xFAFF or
                0xFE30 <= o <= 0xFE4F or 0xFF00 <= o <= 0xFF60 or 0xFFE0 <= o <= 0xFFE6)
        u += 2.0 if wide else 1.0
    return u


def _est_mm(text: str, font_mm: float) -> float:
    return _wunits(text) * font_mm * _ADV


def _size_color(name: str, label_w: int):
    """Golden-style colour-name sizing, length/width aware (CJK counted 2x).
    Returns (font_mm_str, use_textLength, healed) or None when no spec.
      - pick the largest golden tier whose estimated WIDTH fits the field;
      - if even the smallest tier overflows, keep the smallest font and
        letter-compress with textLength (the 'healing' fit) — flagged healed=True
        so the gap is recorded (tweaker can shorten / truncate the name)."""
    fam = "spool" if label_w == 45 else None
    cfg = (((_SPEC.get("families") or {}).get(fam) or {}).get("color_name")) if fam else None
    if not cfg:
        return None
    tiers = [t["font_mm"] for t in (cfg.get("tier_max_name_chars") or [])] or [1.30, 1.15, 1.00]
    for f in tiers:                       # largest -> smallest
        if _est_mm(name, f) <= _SPOOL_FIELD_MM:
            return (f"{f:g}mm", False, False)
    # over-length even at the smallest tier: drop to the compact font and
    # letter-compress with textLength (the heal_long_names fit) — flagged.
    return (_COMPACT_FS, True, True)


def _label_w(svg_text: str) -> int:
    m = ROOT_W_RE.search(svg_text)
    return round(float(m.group(1))) if m else 45


def _set_attr(attrs: str, name: str, value: str) -> str:
    if re.search(rf'\s{name}="[^"]*"', attrs):
        return re.sub(rf'\s{name}="[^"]*"', f' {name}="{value}"', attrs)
    return attrs + f' {name}="{value}"'


class Localizer:
    def __init__(self, adapter: LocaleAdapter):
        self.a = adapter
        # english reverse maps, built once from english_standard
        self.material_by_en: dict[str, str] = {}     # display_text -> semantic_key
        self.color_by_en: dict[tuple[str, str], str] = {}  # (semantic_key, en_color) -> color_key
        for e in adapter.entries("english_standard"):
            sk = str(e.get("semantic_key") or "").strip()
            disp = str(e.get("display_text") or "").strip()
            if sk and disp:
                self.material_by_en.setdefault(disp, sk)
            for ck, cv in (e.get("color_text_map") or {}).items():
                cv = str(cv or "").strip()
                if sk and cv:
                    self.color_by_en[(sk, cv)] = str(ck).strip().lower()

    def localize(self, svg_text: str, pack: str) -> dict:
        nodes = [(m.group("content").strip(), m) for m in TEXT_NODE_RE.finditer(svg_text)]
        contents = [c for c, _ in nodes]

        # PREFERRED: the sanctioned data-type-key / data-color-key attributes give
        # the semantic_key + colour_key directly, so this works from ANY language
        # (re-localizable) and is immune to text mismatches (e.g. "TPU 90A").
        tk = TYPEKEY_RE.search(svg_text)
        ck = COLORKEY_RE.search(svg_text)
        material_en = semantic_key = color_en = color_key = None
        if tk:
            semantic_key, material_en = tk.group(2), tk.group(3).strip()
        if ck:
            color_key, color_en = ck.group(2), ck.group(3).strip()

        # FALLBACK (no keys present): identify by exact english text match.
        if semantic_key is None:
            material_en = next((c for c in contents if c in self.material_by_en), None)
            semantic_key = self.material_by_en.get(material_en) if material_en else None
        if color_key is None and semantic_key:
            for c in contents:
                if c != material_en and (semantic_key, c) in self.color_by_en:
                    color_en, color_key = c, self.color_by_en[(semantic_key, c)]
                    break

        rep = {"pack": pack, "semantic_key": semantic_key,
               "material_en": material_en, "color_en": color_en, "color_key": color_key,
               "unmatched": [], "subs": [], "gaps": [], "overflow_risk": []}
        if material_en is None:
            rep["unmatched"].append("material:" + (name_slot_content(svg_text) or "<none>"))
        if semantic_key and color_en is None:
            rep["unmatched"].append("color (no english colour matched this material)")

        out = svg_text
        label_w = _label_w(svg_text)
        # 3. substitute material then colour (single occurrence each). The
        #    material slot already carries textLength upstream, so it only needs
        #    a content swap; the colour slot's font-size steps down per the
        #    golden tier rule (tools/healing/name_sizing.json) so a long localized
        #    name fits at natural width — NO textLength, never scaled.
        if semantic_key and material_en is not None:
            tgt = self.a.resolve_text(semantic_key=semantic_key, presentation_pack=pack)
            out = self._sub_node(out, material_en, tgt, rep, kind="material")
        if semantic_key and color_key is not None and color_en is not None:
            tgt = self.a.resolve_color_text(semantic_key=semantic_key, color_key=color_key,
                                            presentation_pack=pack)
            out = self._sub_node(out, color_en, tgt, rep, kind="color", label_w=label_w)
        rep["changed"] = (out != svg_text)
        return rep | {"_svg": out}

    def _sub_node(self, svg, old, new, rep, kind, label_w=None):
        if not new:
            rep["unmatched"].append(f"{kind}:empty-resolution")
            return svg
        if new == old:
            # Output stayed English. For materials this is expected — product
            # codes (ABS, PETG, TPU 90A) are identical in every language, not a
            # gap. For colours it IS a gap: a specific Bambu colour name that
            # the target pack left untranslated (recorded for GAPS.md).
            if kind == "color" and self.a.language_of(rep["pack"]) not in ("en", ""):
                rep["gaps"].append(f"{kind}:{old}")
            return svg
        rep["subs"].append({"kind": kind, "from": old, "to": new})

        # locate the exact text node holding `old`
        pat = re.compile(r"<text(?P<attrs>[^>]*)>" + re.escape(old) + r"</text>")
        m = pat.search(svg)
        if not m:
            rep["unmatched"].append(f"{kind}:node-not-found")
            return svg
        attrs = m.group("attrs")

        # colour-name sizing (reference tiers, width/CJK aware). Fits by stepping
        # the font down; if the name is too long even at the smallest tier, keep
        # that font and letter-compress with textLength and flag it (recorded so
        # a tweaker can shorten or truncate the translation).
        if kind == "color" and label_w is not None:
            sized = _size_color(new, label_w)
            if sized:
                font, use_tl, healed = sized
                attrs = _set_attr(attrs, "font-size", font)
                if use_tl:
                    attrs = _set_attr(attrs, "textLength", f"{_SPOOL_FIELD_MM:.2f}")
                    attrs = _set_attr(attrs, "lengthAdjust", "spacingAndGlyphs")
                else:
                    attrs = re.sub(r'\s+textLength="[^"]*"', "", attrs)
                    attrs = re.sub(r'\s+lengthAdjust="[^"]*"', "", attrs)
                if healed:
                    rep["overflow_risk"].append({"kind": kind, "to": new, "font": font, "compressed": True})
        return svg[:m.start()] + f"<text{attrs}>{new}</text>" + svg[m.end():]


def main():
    ap = argparse.ArgumentParser(description="Localize Geonosis label text nodes (no artwork change).")
    ap.add_argument("input", help="label .svg or a directory of labels")
    ap.add_argument("--pack", required=True, help="presentation pack (e.g. english_standard, elvish_pack, fr_standard)")
    ap.add_argument("-o", "--out", required=True, help="output directory")
    ap.add_argument("--report", help="write a JSON report to this path")
    args = ap.parse_args()

    adapter = LocaleAdapter()
    if args.pack not in adapter.pack_names():
        sys.exit(f"unknown pack '{args.pack}'. available: {', '.join(adapter.pack_names())}")
    loc = Localizer(adapter)

    src = Path(args.input)
    files = sorted(src.rglob("*.svg")) if src.is_dir() else [src]
    out_dir = Path(args.out)
    rel_root = src if src.is_dir() else src.parent

    reports = []
    for f in files:
        rep = loc.localize(f.read_text(encoding="utf-8"), args.pack)
        svg = rep.pop("_svg")
        dest = out_dir / f.relative_to(rel_root)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(svg, encoding="utf-8")
        rep["file"] = str(f.name)
        reports.append(rep)

    n_changed = sum(1 for r in reports if r["changed"])
    n_unmatched = sum(1 for r in reports if r["unmatched"])
    n_gaps = sum(len(r["gaps"]) for r in reports)
    n_overflow = sum(len(r["overflow_risk"]) for r in reports)
    summary = {"pack": args.pack, "files": len(reports), "changed": n_changed,
               "files_with_unmatched": n_unmatched, "gap_terms": n_gaps,
               "overflow_flags": n_overflow, "reports": reports}
    if args.report:
        Path(args.report).write_text(json.dumps(summary, indent=2))
    print(json.dumps({k: v for k, v in summary.items() if k != "reports"}, indent=2))


if __name__ == "__main__":
    main()
