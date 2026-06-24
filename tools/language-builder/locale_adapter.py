#!/usr/bin/env python3
"""
locale_adapter.py — standalone localized-text resolver for Geonosis labels.

Ported from the upstream locale pipeline adapter (LocaleAdapter). Stripped of
the embedded internal snapshot coupling: it now
reads presentation packs from a plain `locale_data/` directory in this tool,
with NO external package imports (stdlib only).

Data layout (locale_data/):
  presentation_packs.json     # english_standard (+ emoji_pack) source
  packs/<pack>.json           # generated/* machine translations + curated/*

Resolution: a (semantic_key [, color_key]) pair -> the display string for a
requested presentation_pack, falling back to english_standard, then to a
caller-supplied fallback. The factory's color vocabulary is the slugified
Bambu colour name (e.g. "Jade White" -> color_key "jade_white").
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

DATA_ROOT = Path(__file__).resolve().parent / "locale_data"


def slugify_color(name: str) -> str:
    """Bambu colour name -> color_key, matching the presentation-pack keys.
    'Jade White' -> 'jade_white', 'Navy Blue' -> 'navy_blue'."""
    s = str(name or "").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


class LocaleAdapter:
    """Resolve localized label text from presentation-pack documents."""

    def __init__(self, data_root: Path | None = None) -> None:
        self.data_root = Path(data_root) if data_root else DATA_ROOT
        self._packs = self._load_packs()

    def _load_packs(self) -> dict[str, dict[str, Any]]:
        payloads: list[dict[str, Any]] = []
        root_doc = self.data_root / "presentation_packs.json"
        if root_doc.exists():
            payloads.append(json.loads(root_doc.read_text(encoding="utf-8")))
        packs_dir = self.data_root / "packs"
        if packs_dir.exists():
            for path in sorted(packs_dir.rglob("*.json")):
                payloads.append(json.loads(path.read_text(encoding="utf-8")))

        packs: dict[str, dict[str, Any]] = {}
        for payload in payloads:
            for pack in payload.get("packs", []):
                if isinstance(pack, dict):
                    key = str(pack.get("presentation_pack") or "").strip()
                    if key:
                        packs[key] = dict(pack)
        return packs

    # -- introspection -----------------------------------------------------
    def pack_names(self) -> list[str]:
        return sorted(self._packs)

    def language_of(self, presentation_pack: str) -> str:
        return str(self._packs.get(presentation_pack, {}).get("language") or "")

    def entries(self, presentation_pack: str) -> list[dict[str, Any]]:
        return list(self._packs.get(presentation_pack, {}).get("entries", []))

    # -- resolution --------------------------------------------------------
    def _matching(self, presentation_pack: str, semantic_key: str) -> list[dict[str, Any]]:
        pack = self._packs.get(presentation_pack, {})
        return [dict(e) for e in pack.get("entries", [])
                if isinstance(e, dict) and str(e.get("semantic_key") or "").strip() == semantic_key]

    @staticmethod
    def _select(entries: list[dict[str, Any]], variant: str) -> dict[str, Any] | None:
        variant = str(variant or "default").strip()
        if variant and variant != "default":
            for row in entries:
                if str(row.get("variant") or "").strip() == variant:
                    return row
        return entries[0] if entries else None

    @staticmethod
    def _packs_to_try(requested: str) -> list[str]:
        pack = str(requested or "").strip() or "english_standard"
        return ["english_standard"] if pack == "english_standard" else [pack, "english_standard"]

    def resolve_text(self, *, semantic_key: str, presentation_pack: str = "english_standard",
                     presentation_variant: str = "default", fallback_text: str = "") -> str:
        key = str(semantic_key or "").strip()
        if not key:
            return str(fallback_text or "")
        for pack in self._packs_to_try(presentation_pack):
            entry = self._select(self._matching(pack, key), presentation_variant)
            value = str((entry or {}).get("display_text") or "").strip()
            if value:
                return value
        return str(fallback_text or key)

    def resolve_color_text(self, *, semantic_key: str, color_key: str,
                           presentation_pack: str = "english_standard",
                           presentation_variant: str = "default", fallback_text: str = "") -> str:
        key = str(semantic_key or "").strip()
        color = str(color_key or "").strip().lower()
        if not key:
            return str(fallback_text or "")
        for pack in self._packs_to_try(presentation_pack):
            entry = self._select(self._matching(pack, key), presentation_variant)
            cmap_raw = (entry or {}).get("color_text_map")
            if isinstance(cmap_raw, dict):
                for mk, mv in cmap_raw.items():
                    if str(mk or "").strip().lower() == color:
                        v = str(mv or "").strip()
                        if v:
                            return v
        return str(fallback_text or color_key)


def build_default_adapter() -> LocaleAdapter:
    return LocaleAdapter(DATA_ROOT)


if __name__ == "__main__":
    a = build_default_adapter()
    print("packs:", a.pack_names())
    print("en  pla_basic        :", a.resolve_text(semantic_key="filament.pla_basic"))
    print("qya pla_basic        :", a.resolve_text(semantic_key="filament.pla_basic", presentation_pack="elvish_pack"))
    print("en  pla_basic/jade   :", a.resolve_color_text(semantic_key="filament.pla_basic", color_key="jade_white"))
    print("qya pla_basic/jade   :", a.resolve_color_text(semantic_key="filament.pla_basic", color_key="jade_white", presentation_pack="elvish_pack"))
