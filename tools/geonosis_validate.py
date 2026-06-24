#!/usr/bin/env python3
"""
geonosis_validate.py — run the Geonosis validation gate (GEONOSIS_SPEC.md §7)
and export dimensionally-true PDFs (cairosvg, Tier 1).

This does NOT design anything new — it mechanically checks the gate the spec
already defines, and emits PDFs whose MediaBox is asserted against the SVG mm
size. Source files are never modified.

Gate (per file):
  1. zero-trace: grep -ci "provenance|data-source|data-origin|internal-only"
     == 0   (case-insensitive, whole-file)
  2. root width/height end in 'mm'; viewBox ratio matches width:height
  3. no <metadata>, <script>, or display:none instruction groups
  4. (labels only) renders pixel-identical at 300dpi to the source artwork
  5. PDF MediaBox matches the SVG mm size within tol (default 0.05mm)

Usage:
  python3 tools/geonosis_validate.py gate    OUT.svg [--expect WxH]
  python3 tools/geonosis_validate.py pixel    SRC.svg OUT.svg [--dpi 300]
  python3 tools/geonosis_validate.py pdf      OUT.svg OUT.pdf [--expect WxH]
"""
import argparse, re, sys, math
from pathlib import Path

PT_PER_MM = 72.0 / 25.4
ZERO_TRACE_RE = re.compile(r"provenance|data-source|data-origin|internal-only", re.IGNORECASE)


def zero_trace(path: Path):
    """Return count of forbidden marker lines (spec §7.1 == 0)."""
    n = 0
    data = path.read_text(errors="replace")
    for line in data.splitlines():
        if ZERO_TRACE_RE.search(line):
            n += 1
    return n


def _parse_svg_root(path: Path):
    """Parse SVG root, tolerating leading whitespace before the XML declaration
    (sources are never modified, so the parser absorbs it)."""
    from lxml import etree
    data = path.read_bytes().lstrip()
    return etree.fromstring(data)


def read_root_dims(path: Path):
    """Parse root width/height/viewBox. Returns dict."""
    root = _parse_svg_root(path)
    return {
        "width": root.get("width"),
        "height": root.get("height"),
        "viewBox": root.get("viewBox"),
        "root": root,
    }


def check_mm(path: Path):
    """Spec §7.2: width/height end in mm; viewBox ratio matches width:height.
    Returns (ok, (w_mm,h_mm), messages)."""
    d = read_root_dims(path)
    msgs = []
    w, h, vb = d["width"], d["height"], d["viewBox"]
    ok = True
    if not (w and w.endswith("mm") and h and h.endswith("mm")):
        ok = False
        msgs.append(f"width/height not mm: {w} x {h}")
        return ok, (None, None), msgs
    w_mm = float(w[:-2]); h_mm = float(h[:-2])
    if vb:
        vx, vy, vw, vh = (float(v) for v in re.split(r"[ ,]+", vb.strip()))
        # ratio match: vw:vh must equal w:h
        if not math.isclose(vw / vh, w_mm / h_mm, rel_tol=1e-4):
            ok = False
            msgs.append(f"viewBox ratio {vw}x{vh} != size ratio {w_mm}x{h_mm}")
    else:
        ok = False
        msgs.append("no viewBox")
    return ok, (w_mm, h_mm), msgs


def check_clean(path: Path):
    """Spec §7.3: no <metadata>, <script>, display:none groups."""
    SVG = "http://www.w3.org/2000/svg"
    root = _parse_svg_root(path)
    bad = []
    if root.findall(f".//{{{SVG}}}metadata"):
        bad.append("<metadata>")
    if root.findall(f".//{{{SVG}}}script"):
        bad.append("<script>")
    for el in root.iter():
        if isinstance(el.tag, str):
            style = (el.get("style") or "").replace(" ", "").lower()
            if "display:none" in style:
                bad.append("display:none")
                break
    return (len(bad) == 0), bad


def render_png(svg_path: Path, dpi: int):
    import cairosvg
    return cairosvg.svg2png(url=str(svg_path), dpi=dpi)


def pixel_identical(src: Path, out: Path, dpi=300):
    """Spec §7.4: exported label renders pixel-identical to source artwork.
    Renders both at dpi; compares. Returns (ok, max_channel_diff, size_note)."""
    from PIL import Image, ImageChops
    import io
    a = Image.open(io.BytesIO(render_png(src, dpi))).convert("RGBA")
    b = Image.open(io.BytesIO(render_png(out, dpi))).convert("RGBA")
    if a.size != b.size:
        return False, None, f"raster size differs {a.size} vs {b.size}"
    diff = ImageChops.difference(a, b)
    bbox = diff.getbbox()
    if bbox is None:
        return True, 0, f"identical at {a.size[0]}x{a.size[1]}px"
    extrema = diff.getextrema()  # per-channel (min,max)
    maxdiff = max(hi for _, hi in extrema)
    return (maxdiff == 0), maxdiff, f"diff bbox {bbox} maxchan {maxdiff}"


def svg_to_pdf(svg: Path, pdf: Path, tool: str = "inkscape", text_to_path: bool = True):
    """Export SVG -> PDF.

    Default tool is Inkscape with the proven export flags
    (TEXT_SCALING_SOLUTION_COMPLETE.md):
      --export-area-page          page == SVG mm canvas (MediaBox stays true)
      --export-dpi=72             1:1 mapping of viewBox units to mm (72pt/in / 25.4)
      --export-text-to-path       text outlined -> exact visual match, no font
                                  substitution, no mm font-size misscaling

    cairosvg is the fallback ONLY: it misrenders mm-based font-size values
    (e.g. font-size="1.70mm") and substitutes fonts, which is the defect this
    default fixes.
    """
    import shutil, subprocess
    pdf.parent.mkdir(parents=True, exist_ok=True)
    if tool == "inkscape":
        binpath = shutil.which("inkscape")
        if not binpath:
            raise SystemExit("inkscape not found on PATH (use --pdf-tool cairosvg to override, NOT recommended for labels)")
        cmd = [binpath, str(svg), "--export-type=pdf",
               f"--export-filename={pdf}", "--export-area-page",
               "--export-dpi=72"]
        if text_to_path:
            cmd.append("--export-text-to-path")
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise SystemExit(f"inkscape export failed: {res.stderr.strip() or res.stdout.strip()}")
    elif tool == "cairosvg":
        import cairosvg
        cairosvg.svg2pdf(url=str(svg), write_to=str(pdf))
    else:
        raise SystemExit(f"unknown pdf tool: {tool}")


def pdf_mediabox_mm(pdf: Path):
    from pypdf import PdfReader
    box = PdfReader(str(pdf)).pages[0].mediabox
    w_pt = float(box.width); h_pt = float(box.height)
    return w_pt / PT_PER_MM, h_pt / PT_PER_MM


def assert_pdf_size(pdf: Path, w_mm, h_mm, tol=0.05):
    mw, mh = pdf_mediabox_mm(pdf)
    ok = abs(mw - w_mm) <= tol and abs(mh - h_mm) <= tol
    return ok, (mw, mh)


def parse_wh(s):
    m = re.match(r"^([0-9.]+)x([0-9.]+)$", s)
    if not m:
        raise argparse.ArgumentTypeError("expected WxH")
    return float(m.group(1)), float(m.group(2))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gate"); g.add_argument("svg"); g.add_argument("--expect", type=parse_wh)
    p = sub.add_parser("pixel"); p.add_argument("src"); p.add_argument("out"); p.add_argument("--dpi", type=int, default=300)
    d = sub.add_parser("pdf"); d.add_argument("svg"); d.add_argument("pdf"); d.add_argument("--expect", type=parse_wh)
    d.add_argument("--pdf-tool", choices=["inkscape", "cairosvg"], default="inkscape",
                   help="PDF exporter (default: inkscape; cairosvg misrenders mm font sizes)")
    d.add_argument("--no-text-to-path", action="store_true",
                   help="keep text as text in the PDF (inkscape only; risks font substitution)")
    args = ap.parse_args()

    if args.cmd == "gate":
        svg = Path(args.svg); fails = []
        zt = zero_trace(svg)
        raw0 = svg.read_bytes()[:1]
        if raw0 not in (b"<",):
            print("  leading-ws: FAIL (file must start with <?xml, not whitespace)")
            fails.append("leading-whitespace")
        print(f"  zero-trace: {zt} {'OK' if zt == 0 else 'FAIL'}")
        if zt: fails.append("zero-trace")
        ok_mm, (w, h), msgs = check_mm(svg)
        print(f"  mm-dims:    {w}x{h}mm {'OK' if ok_mm else 'FAIL ' + ';'.join(msgs)}")
        if not ok_mm: fails.append("mm-dims")
        ok_clean, bad = check_clean(svg)
        print(f"  clean:      {'OK' if ok_clean else 'FAIL ' + ','.join(bad)}")
        if not ok_clean: fails.append("clean")
        if args.expect:
            ew, eh = args.expect
            ok_e = abs(ew - (w or -9)) <= 0.05 and abs(eh - (h or -9)) <= 0.05
            print(f"  expect:     {ew}x{eh}mm {'OK' if ok_e else 'FAIL got ' + str((w, h))}")
            if not ok_e: fails.append("expect")
        print("  GATE", "PASS" if not fails else "FAIL " + ",".join(fails))
        sys.exit(1 if fails else 0)

    if args.cmd == "pixel":
        ok, maxd, note = pixel_identical(Path(args.src), Path(args.out), args.dpi)
        print(f"  pixel@{args.dpi}dpi: {'IDENTICAL' if ok else 'DIFF'} ({note})")
        sys.exit(0 if ok else 1)

    if args.cmd == "pdf":
        svg = Path(args.svg); pdf = Path(args.pdf)
        svg_to_pdf(svg, pdf, tool=args.pdf_tool, text_to_path=not args.no_text_to_path)
        w = h = None
        if args.expect:
            w, h = args.expect
        else:
            _, (w, h), _ = check_mm(svg)
        ok, (mw, mh) = assert_pdf_size(pdf, w, h)
        print(f"  pdf MediaBox: {mw:.3f}x{mh:.3f}mm (expect {w}x{h}) {'OK' if ok else 'FAIL'}")
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()