#!/usr/bin/env python3
"""
build_fork.py - build the "Synthetix UI" fork of Instrument Sans (SIL OFL 1.1).

What it does (all deterministic, no network):
  1. Builds an interpolating variable font from Instrument Sans Regular (400) and Bold (700).
  2. Cuts three static weights calibrated to the measured stem/cap ratios:
       Regular  = wght 420   (stem/cap 0.116 vs target 0.117)
       SemiBold = wght 500   (0.143 vs 0.143)
       Bold     = wght 610   (0.178 vs 0.179)
  3. Applies measured proportion edits (tune_glyphs.py): per-letter widths, ascender/descender/dot heights.
  4. Bakes weight-dependent tracking into the advance widths (units from fork_params.json).
  5. Renames the family to "Synthetix UI" and sets weight classes 400 / 600 / 700.
  6. Writes TTF + WOFF (zlib; WOFF2 needs the optional 'brotli' package).

  pip install fonttools
  python build_fork.py --regular InstrumentSans-Regular.ttf --bold InstrumentSans-Bold.ttf --out ../fonts
Get the inputs from https://github.com/Instrument/instrument-sans (OFL). The OFL text and
copyright lines are preserved in the output name table; ship OFL.txt next to the fonts.
Not affiliated with Pinterest. Contains no Pinterest font data.
"""
import argparse, json, os, tempfile
from fontTools.ttLib import TTFont
from fontTools.designspaceLib import DesignSpaceDocument, AxisDescriptor, SourceDescriptor
from fontTools import varLib
from fontTools.varLib import instancer
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tune_glyphs

HERE = os.path.dirname(os.path.abspath(__file__))


def build_vf(regular, bold, tmp):
    ds = DesignSpaceDocument()
    ax = AxisDescriptor(); ax.name = "Weight"; ax.tag = "wght"
    ax.minimum, ax.default, ax.maximum = 400, 400, 700
    ds.addAxis(ax)
    for path, loc in ((regular, 400), (bold, 700)):
        s = SourceDescriptor(); s.path = os.path.abspath(path); s.location = {"Weight": loc}; s.name = f"m{loc}"
        ds.addSource(s)
    p = os.path.join(tmp, "is.designspace"); ds.write(p)
    vf, _, _ = varLib.build(p)
    return vf


def bake_tracking(font, units):
    hmtx = font["hmtx"]; upm = font["head"].unitsPerEm
    cmap = font.getBestCmap()
    spaces = {g for cp, g in cmap.items() if cp in (0x20, 0xA0) or 0x2000 <= cp <= 0x200B or cp in (0x202F, 0x205F, 0x3000)}
    n = 0
    for g in font.getGlyphOrder():
        adv, lsb = hmtx[g]
        if adv == 0 or g in spaces:
            continue
        hmtx[g] = (max(0, adv + units), lsb); n += 1
    advs = [a for a, _ in hmtx.metrics.values() if a > 0]
    font["hhea"].advanceWidthMax = max(advs)
    font["OS/2"].xAvgCharWidth = round(sum(advs) / len(advs))
    return n


def set_names(font, family, style, weight_class):
    ribbi = style in ("Regular", "Bold")
    n = font["name"]
    for i in (1, 2, 3, 4, 6, 16, 17, 21, 22, 25):
        n.removeNames(nameID=i)
    full = f"{family} {style}"; ps = f"{family.replace(' ', '')}-{style}"
    rec = {1: family if ribbi else f"{family} {style}", 2: style if ribbi else "Regular",
           3: f"{family};1.000;{ps}", 4: full, 6: ps,
           5: "Version 1.000; modified from Instrument Sans 1.000",
           10: "Modified from Instrument Sans (SIL OFL 1.1): interpolated weights, baked tracking. "
               "Not affiliated with Pinterest."}
    if not ribbi:
        rec[16] = family; rec[17] = style
    for i, v in rec.items():
        n.removeNames(nameID=i)
        n.setName(v, i, 3, 1, 0x409); n.setName(v, i, 1, 0, 0)
    os2 = font["OS/2"]; os2.usWeightClass = weight_class
    fs = os2.fsSelection & ~(0b1100001)          # clear italic, bold, regular
    fs |= 0b100000 if style == "Bold" else 0b1000000
    os2.fsSelection = fs
    font["head"].macStyle = 1 if style == "Bold" else 0
    if "STAT" in font:
        del font["STAT"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--regular", required=True); ap.add_argument("--bold", required=True)
    ap.add_argument("--params", default=os.path.join(HERE, "fork_params.json"))
    ap.add_argument("--out", default=os.path.join(HERE, "..", "fonts"))
    ap.add_argument("--no-tracking", action="store_true", help="write edited but untracked weights (Unbaked-<Style>.ttf) for browser_fit.py fit")
    a = ap.parse_args()
    P = json.load(open(a.params)); os.makedirs(a.out, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        vf = build_vf(a.regular, a.bold, tmp)
        vp = os.path.join(tmp, "vf.ttf"); vf.save(vp)
        for inst in P["instances"]:
            f = instancer.instantiateVariableFont(TTFont(vp), {"wght": inst["wght"]}, inplace=False)
            tune_glyphs.apply_edits(f, P["edits"], mode="center")
            if a.no_tracking:
                f.save(os.path.join(a.out, f"Unbaked-{inst['style']}.ttf")); continue
            units = round(inst["track_em"] * f["head"].unitsPerEm)
            n = bake_tracking(f, units)
            set_names(f, P["family"], inst["style"], inst["weightClass"])
            base = os.path.join(a.out, f"SynthetixUI-{inst['style']}")
            f.save(base + ".ttf")
            g = TTFont(base + ".ttf"); g.flavor = "woff"; g.save(base + ".woff")
            print(f"{inst['style']:9s} wght {inst['wght']} -> class {inst['weightClass']}, tracking {units:+d}/1000 em on {n} glyphs -> {base}.ttf/.woff")


if __name__ == "__main__":
    main()
