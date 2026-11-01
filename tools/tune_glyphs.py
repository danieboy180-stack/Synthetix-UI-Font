#!/usr/bin/env python3
"""
tune_glyphs.py - measurement-driven proportion edits for the Synthetix UI fork.

Everything here is a *proportion* edit derived from the pangram screenshots (consistent across three
display sizes). No outline is traced or copied: glyphs are scaled/stretched; advances are untouched.

  width_scale  : per-letter horizontal scale about the ink centre, advance unchanged ('left' mode kept for reference;
                 it scored worse on held-out spacing)
  vertical     : ascender raise, descender shorten, i/j dot lift (fractions of cap height)
Edit table lives in fork_params.json under "edits".
"""
from fontTools.ttLib import TTFont


def _contours(gl):
    ends, start = gl.endPtsOfContours, 0
    for e in ends:
        yield start, e + 1
        start = e + 1


def scale_width(font, name, h, mode="center"):
    """mode 'center': scale about the ink centre, advance unchanged (side-bearings absorb the change);
       mode 'left'  : scale about the left edge, advance follows the ink width."""
    glyf, hmtx = font["glyf"], font["hmtx"]
    gl = glyf[name]
    if gl.isComposite() or gl.numberOfContours == 0:
        return None
    gl.recalcBounds(glyf)
    x0, x1 = gl.xMin, gl.xMax
    pivot = (x0 + x1) / 2 if mode == "center" else x0
    for i, (x, y) in enumerate(gl.coordinates):
        gl.coordinates[i] = (round(pivot + (x - pivot) * h), y)
    gl.recalcBounds(glyf)
    adv, lsb = hmtx[name]
    if mode == "left":
        hmtx[name] = (adv + round((h - 1) * (x1 - x0)), gl.xMin)
    else:
        hmtx[name] = (adv, gl.xMin)
    return 0 if mode == "center" else (h - 1) * (x1 - x0)   # shift of ink centre, used to re-centre accents


def stretch_above(font, name, knot, delta):
    """Stretch everything above `knot` so the glyph top rises by `delta` (ascender raise)."""
    glyf = font["glyf"]; gl = glyf[name]
    gl.recalcBounds(glyf); top = gl.yMax
    k = (top + delta - knot) / (top - knot)
    for i, (x, y) in enumerate(gl.coordinates):
        if y > knot:
            gl.coordinates[i] = (x, round(knot + (y - knot) * k))
    gl.recalcBounds(glyf)


def base_of(font, name):
    gl = font["glyf"][name]
    return gl.components[0].glyphName if gl.isComposite() else name


def lift_dots(font, name, knot, delta):
    """Rigidly lift the dot of i/j (a composite: dotless base + combining dot) or any contour wholly above `knot`."""
    glyf = font["glyf"]; gl = glyf[name]
    if gl.isComposite():
        for c in gl.components[1:]:
            c.y += delta
        return
    for a, b in _contours(gl):
        if min(gl.coordinates[p][1] for p in range(a, b)) > knot:
            for p in range(a, b):
                x, y = gl.coordinates[p]; gl.coordinates[p] = (x, y + delta)
    gl.recalcBounds(glyf)


def shorten_below(font, name, knot, delta):
    """Compress everything below `knot` (negative y) so the glyph bottom rises by `delta`."""
    glyf = font["glyf"]; gl = glyf[name]
    gl.recalcBounds(glyf); bot = gl.yMin
    k = (bot + delta - knot) / (bot - knot)
    for i, (x, y) in enumerate(gl.coordinates):
        if y < knot:
            gl.coordinates[i] = (x, round(knot + (y - knot) * k))
    gl.recalcBounds(glyf)


def fix_composites(font, widened):
    """Accented composites: follow the base glyph's new advance and re-centre marks."""
    glyf, hmtx = font["glyf"], font["hmtx"]
    for name in font.getGlyphOrder():
        gl = glyf[name]
        if not gl.isComposite():
            continue
        base = gl.components[0].glyphName
        if base in widened:
            for c in gl.components[1:]:
                c.x += round(widened[base] / 2)
            hmtx[name] = (hmtx[base][0], hmtx[name][1])


def apply_edits(font, edits, mode="center"):
    """edits: dict from fork_params.json['edits']; returns number of glyphs changed."""
    cap = font["OS/2"].sCapHeight; xh = font["OS/2"].sxHeight; n = 0
    widened = {}
    for g, h in edits["width_scale"].items():
        d = scale_width(font, g, h, mode)
        if d is not None:
            widened[g] = d; n += 1
    fix_composites(font, widened)
    v = edits["vertical"]
    for g in v["ascender_raise"]["glyphs"]:
        stretch_above(font, g, xh + 20, round(v["ascender_raise"]["cap"] * cap)); n += 1
    for g in v["dot_lift"]["glyphs"]:
        lift_dots(font, g, xh + 20, round(v["dot_lift"]["cap"] * cap)); n += 1
    for g, c in v["descender_shorten"].items():
        shorten_below(font, base_of(font, g), -30, round(c * cap)); n += 1
    return n
