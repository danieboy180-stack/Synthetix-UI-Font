"""Build UFO + TTF for one master (design direction, weight)."""
import os, sys, math, json, time
from types import SimpleNamespace
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.ufoLib import UFOWriter
import geom
from geom import bbox, translate, s0, s1
from glyphs_lc import Ctx
import glyphset

UPM = 1000
def draw_contours(pen, contours):
    for c in contours:
        pen.moveTo(s0(c[0]))
        for s in c:
            if s[0] == 'L': pen.lineTo(s[2])
            else: pen.curveTo(s[2], s[3], s[4])
        pen.closePath()

def draw_points(pen, contours):
    for c in contours:
        pen.beginPath()
        for s in c:
            if s[0] == 'L': pen.addPoint(s[2], 'line')
            else:
                pen.addPoint(s[2]); pen.addPoint(s[3]); pen.addPoint(s[4], 'curve')
        pen.endPath()

def make_master(d, w, XH=515, only=None):
    c = Ctx(d, w, XH)
    out = {}; log = {}
    geom.ERR_LOG['max'] = 0
    for name, uni, fn, lcl, rcl in glyphset.R:
        if only and name not in only: continue
        try:
            cs = fn(c)
        except Exception as e:
            log[name] = 'ERR ' + repr(e); cs = []
        if not cs:
            out[name] = dict(uni=uni, contours=[], adv=int(round(250 + 0.1 * c.v)), lsb=0)
            continue
        x0, y0, x1, y1 = bbox(cs)
        lsb = glyphset.SB[lcl](c.v); rsb = glyphset.SB[rcl](c.v)
        if name in ('zero','one','two','three','four','five','six','seven','eight','nine'):
            adv_f = (520 + 0.30 * c.v) + 2 * (0.40 * c.v + 20) + 20
            ink = x1 - x0
            lsb_f = (adv_f - ink) / 2
            cs2 = translate(cs, lsb_f - x0)
            out[name] = dict(uni=uni, contours=cs2, adv=int(round(adv_f)), lsb=int(round(lsb_f)))
        else:
            cs2 = translate(cs, lsb - x0)
            out[name] = dict(uni=uni, contours=cs2, adv=int(round(lsb + (x1 - x0) + rsb)), lsb=int(round(lsb)))
        out[name]['contours'] = [[(s[0],) + tuple((round(p[0]), round(p[1])) for p in s[1:]) for s in cc] for cc in out[name]['contours']]
    return c, out, log

def write_ufo(path, d, w, glyphs, c, family='Stackra Sans', style='Regular'):
    import shutil
    if os.path.exists(path): shutil.rmtree(path)
    wr = UFOWriter(path, formatVersion=3)
    info = SimpleNamespace(familyName=family, styleName=style, unitsPerEm=UPM, ascender=950, descender=-250,
                           capHeight=c.CAP, xHeight=c.XH, italicAngle=0, versionMajor=0, versionMinor=5,
                           openTypeOS2WeightClass=w)
    wr.writeInfo(info)
    gs = wr.getGlyphSet()
    order = []
    for name, g in glyphs.items():
        obj = SimpleNamespace(width=g['adv'], unicodes=[g['uni']] if g['uni'] else [], height=0)
        gs.writeGlyph(name, obj, drawPointsFunc=lambda pen, cs=g['contours']: draw_points(pen, cs))
        order.append(name)
    gs.writeContents()
    wr.writeLayerContents()
    wr.writeLib({'public.glyphOrder': order})
    wr.close()

def notdef(c):
    v = c.v
    o = geom.rect(60, 0, 460, 700); i = geom.rect(60 + v * 0.6, v * 0.6, 460 - v * 0.6, 700 - v * 0.6)
    return [o, geom.rev_contour(i)]

def build_ttf(path, glyphs, c, family='Stackra Sans', style='Regular', weight=400):
    order = ['.notdef'] + list(glyphs.keys())
    cmap = {g['uni']: n for n, g in glyphs.items() if g['uni']}
    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    tt = {}; metrics = {}
    nd = notdef(c)
    pen = TTGlyphPen(None); cp = Cu2QuPen(pen, 1.0, reverse_direction=True); draw_contours(cp, nd); tt['.notdef'] = pen.glyph()
    metrics['.notdef'] = (520, 60)
    for n, g in glyphs.items():
        pen = TTGlyphPen(None); cp = Cu2QuPen(pen, 1.0, reverse_direction=True)
        draw_contours(cp, g['contours'])
        tt[n] = pen.glyph()
        metrics[n] = (g['adv'], g['lsb'] if g['contours'] else 0)
    fb.setupGlyf(tt)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=950, descent=-250, lineGap=0)
    fb.setupNameTable({'familyName': family, 'styleName': style, 'uniqueFontIdentifier': f'{family}-{style}-0.5.0-dev',
                       'fullName': f'{family} {style}', 'psName': f'{family.replace(" ","")}-{style}', 'version': 'Version 0.500'})
    fb.setupOS2(sTypoAscender=780, sTypoDescender=-220, sTypoLineGap=200, usWinAscent=1000, usWinDescent=280,
                sxHeight=c.XH, sCapHeight=c.CAP, usWeightClass=weight, fsType=0, achVendID='STKR',
                fsSelection=(1 << 7) | (1 << 6 if style == 'Regular' else 0) | (1 << 5 if style == 'Bold' else 0))
    fb.setupPost(keepGlyphNames=True)
    fb.save(path)

if __name__ == '__main__':
    d = sys.argv[1] if len(sys.argv) > 1 else 'A'; w = int(sys.argv[2]) if len(sys.argv) > 2 else 400
    t = time.time()
    c, g, log = make_master(d, w)
    print('built', len(g), 'glyphs in', round(time.time() - t, 1), 's; errors:', log, 'fit-err', round(geom.ERR_LOG['max'], 2))
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    os.makedirs(f'{base}/fonts/proto', exist_ok=True)
    build_ttf(f'{base}/fonts/proto/Stackra-{d}-{w}.ttf', g, c, family=f'Stackra Proto {d}', style='Regular', weight=w)
    print('ttf ok')
