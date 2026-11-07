#!/usr/bin/env python3
"""
audit_baseline.py - structural audit of a Synthetix UI release (V4 Stage 0 baseline freeze).

Measures only what a font file can prove (no reference bitmaps needed):
names/licence, vertical metrics and clipping, tables, GSUB/GPOS features, tabular-figure
widths, coverage lists, .notdef, stylistic alternates vs base glyphs, weight/italic flags,
and hardcoded absolute paths in scripts.

  pip install fonttools
  python tools/v4/audit_baseline.py --fonts <dir with .ttf> --tools <scripts dir> --out audit.json

Deterministic: no timestamps, sorted keys. Same inputs give byte-identical JSON.
Not measured here: shaping/mark stacking, Font Bakery checks, cross-engine rendering.
"""
import argparse, glob, hashlib, json, os, re, sys
from fontTools.ttLib import TTFont

# Lists are the audit's own (the plan names categories, not exact code points). "arrows" = U+2190-2193.
PRI_AFRICAN = {
    "combining": [0x0300, 0x0301, 0x0304, 0x0323],
    "hausa": [0x0181, 0x0253, 0x018A, 0x0257, 0x0198, 0x0199, 0x01B3, 0x01B4, 0x02BC],
    "yoruba_igbo": [0x1EB8, 0x1EB9, 0x1ECC, 0x1ECD, 0x1E62, 0x1E63, 0x1ECA, 0x1ECB, 0x1EE4, 0x1EE5, 0x1E44, 0x1E45],
    "open_vowels_eng": [0x0190, 0x025B, 0x0186, 0x0254, 0x014A, 0x014B],
}
UI_SYMBOLS = [0x20A6, 0x20B5, 0x20B9, 0x2713, 0x2116, 0x00B1, 0x00D7, 0x00F7, 0x2260, 0x2264, 0x2265,
              0x2248, 0x2212, 0x221E, 0x00BD, 0x00BC, 0x00BE, 0x2190, 0x2191, 0x2192, 0x2193]
ALTERNATES = {"Q": "Q.ss09", "J": "J.ss08", "K": "K.ss04", "R": "R.ss05", "G": "G.ss07", "a": "a.ss02", "y": "y.ss03"}
PATH_PAT = re.compile(r"(/home/[A-Za-z0-9_.-]+[^\s'\"),]*|/mnt/[A-Za-z0-9_.-]+[^\s'\"),]*|/tmp/[^\s'\"),]+|C:\\\\[^\s'\"),]+)")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def cp(c):
    return "U+%04X" % c


def subtables(lookup):
    for st in lookup.SubTable:
        yield st.ExtSubTable if hasattr(st, "ExtSubTable") else st


def feature_lookups(table, tag):
    out = []
    for fr in table.table.FeatureList.FeatureRecord:
        if fr.FeatureTag == tag:
            out.extend(fr.Feature.LookupListIndex)
    return sorted(set(out))


def single_subst_map(font, tag):
    if "GSUB" not in font:
        return {}
    gsub = font["GSUB"]
    m = {}
    for li in feature_lookups(gsub, tag):
        for st in subtables(gsub.table.LookupList.Lookup[li]):
            if hasattr(st, "mapping"):
                m.update(st.mapping)
    return m


def glyph_bounds(font):
    glyf = font["glyf"]
    b = {}
    for gn in font.getGlyphOrder():
        g = glyf[gn]
        if g.numberOfContours == 0:
            continue
        g.recalcBounds(glyf)
        b[gn] = (g.xMin, g.yMin, g.xMax, g.yMax)
    return b


def audit_font(path):
    f = TTFont(path)
    cmap = f.getBestCmap()
    order = f.getGlyphOrder()
    hmtx = f["hmtx"].metrics
    os2, head, hhea = f["OS/2"], f["head"], f["hhea"]
    bounds = glyph_bounds(f)
    r = {"file": os.path.basename(path), "sha256": sha256(path), "bytes": os.path.getsize(path)}

    names = {}
    for i in (0, 1, 2, 4, 5, 6, 13, 14, 16, 17):
        n = f["name"].getName(i, 3, 1, 0x409)
        names[str(i)] = n.toUnicode() if n else None
    r["names"] = names
    r["upm"] = head.unitsPerEm
    r["fontRevision"] = round(head.fontRevision, 3)
    r["glyphs"] = len(order)
    r["codepoints"] = len(cmap)
    r["tables"] = sorted(f.keys())
    r["os2"] = {"usWeightClass": os2.usWeightClass, "fsType": os2.fsType, "fsSelection": os2.fsSelection,
                "achVendID": os2.achVendID, "sTypoAscender": os2.sTypoAscender, "sTypoDescender": os2.sTypoDescender,
                "sTypoLineGap": os2.sTypoLineGap, "usWinAscent": os2.usWinAscent, "usWinDescent": os2.usWinDescent,
                "sCapHeight": getattr(os2, "sCapHeight", None), "sxHeight": getattr(os2, "sxHeight", None)}
    r["hhea"] = {"ascent": hhea.ascent, "descent": hhea.descent, "lineGap": hhea.lineGap}
    ymax = max(v[3] for v in bounds.values()); ymin = min(v[1] for v in bounds.values())
    top = sorted(g for g, v in bounds.items() if v[3] == ymax); low = sorted(g for g, v in bounds.items() if v[1] == ymin)
    r["glyph_extent"] = {"yMax": ymax, "yMin": ymin, "yMax_glyphs": top[:4], "yMin_glyphs": low[:4],
                         "win_clip_top": ymax > os2.usWinAscent, "win_clip_bottom": -ymin > os2.usWinDescent}
    r["italic"] = {"fsSelection_italic": bool(os2.fsSelection & 1), "italicAngle": f["post"].italicAngle,
                   "macStyle": head.macStyle}
    r["variable_tables"] = {t: (t in f) for t in ("fvar", "avar", "STAT", "gvar", "HVAR")}
    r["hinting_tables"] = {t: (t in f) for t in ("fpgm", "prep", "cvt ", "gasp")}

    feats = {}
    for tb in ("GSUB", "GPOS"):
        if tb in f and f[tb].table.FeatureList:
            feats[tb] = sorted({fr.FeatureTag for fr in f[tb].table.FeatureList.FeatureRecord})
    r["features"] = feats
    r["feature_check"] = {t: (t in feats.get("GSUB", [])) for t in ("tnum", "pnum", "lnum", "onum", "frac", "zero", "case", "liga")}

    # Tabular figures
    digits = [cmap[c] for c in range(0x30, 0x3A) if c in cmap]
    tnum = single_subst_map(f, "tnum")
    tn_digits = [tnum.get(g, g) for g in digits]
    adv = [hmtx[g][0] for g in tn_digits]
    naira = cmap.get(0x20A6)
    r["tabular"] = {"default_digit_advances": [hmtx[g][0] for g in digits],
                    "tnum_digit_advances": adv, "tnum_spread": (max(adv) - min(adv)) if adv else None,
                    "tnum_exactly_equal": len(set(adv)) == 1 if adv else False,
                    "tnum_substitutions": len(tnum),
                    "naira_present": naira is not None,
                    "naira_in_tnum": (naira in tnum) if naira else False,
                    "naira_advance": hmtx[naira][0] if naira else None}

    # Coverage
    def cov(cps):
        miss = [c for c in cps if c not in cmap]
        return {"tested": len(cps), "present": len(cps) - len(miss), "missing": [cp(c) for c in miss]}
    r["coverage"] = {"pri_african": {k: cov(v) for k, v in PRI_AFRICAN.items()}, "ui_symbols": cov(UI_SYMBOLS)}
    allpa = [c for v in PRI_AFRICAN.values() for c in v]
    r["coverage"]["pri_african_total"] = cov(allpa)
    nd = f["glyf"][".notdef"] if ".notdef" in order else None
    r["notdef"] = {"present": ".notdef" in order, "index0": order[0] == ".notdef",
                   "has_outline": bool(nd is not None and nd.numberOfContours != 0)}

    # Alternates vs base (are V3 edits applied consistently to alternates?)
    ss = sorted(g for g in order if re.search(r"\.ss\d\d$", g))
    alts = {}
    for base_ch, alt in ALTERNATES.items():
        bn = cmap.get(ord(base_ch))
        if alt not in order or bn not in bounds or alt not in bounds:
            alts[alt] = {"present": alt in order}
            continue
        bb, ab = bounds[bn], bounds[alt]
        alts[alt] = {"present": True, "base": bn,
                     "adv_base": hmtx[bn][0], "adv_alt": hmtx[alt][0],
                     "ink_w_base": bb[2] - bb[0], "ink_w_alt": ab[2] - ab[0],
                     "yMin_base": bb[1], "yMin_alt": ab[1], "yMax_base": bb[3], "yMax_alt": ab[3]}
    r["alternates"] = {"ss_glyph_count": len(ss), "named_seven": alts}

    # Kerning size
    kp = 0
    if "GPOS" in f:
        gpos = f["GPOS"]
        for li in feature_lookups(gpos, "kern"):
            for st in subtables(gpos.table.LookupList.Lookup[li]):
                if getattr(st, "Format", None) == 1 and hasattr(st, "PairSet"):
                    kp += sum(len(ps.PairValueRecord) for ps in st.PairSet)  # format 2 class cells not counted
    r["kern_explicit_pairs"] = kp
    return r


def grep_paths(tools_dir):
    hits = {}
    for p in sorted(glob.glob(os.path.join(tools_dir, "**", "*.py"), recursive=True)):
        txt = open(p, encoding="utf-8", errors="replace").read()
        found = sorted(set(m.group(0) for m in PATH_PAT.finditer(txt)))
        if found:
            hits[os.path.relpath(p, tools_dir).replace(os.sep, "/")] = found
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fonts", required=True); ap.add_argument("--tools"); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ttfs = sorted(glob.glob(os.path.join(a.fonts, "*.ttf")))
    if not ttfs:
        sys.exit("no .ttf in " + a.fonts)
    out = {"fonts": [audit_font(p) for p in ttfs]}
    if a.tools:
        h = grep_paths(a.tools)
        out["hardcoded_paths"] = {"files_with_hits": len(h), "hits": h}
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, sort_keys=True, ensure_ascii=True, separators=(",", ":")); fh.write("\n")
    print("wrote", a.out)


if __name__ == "__main__":
    main()
