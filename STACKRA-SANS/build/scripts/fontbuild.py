"""Build UFO + TTF for one master (design direction, weight).

V6 hardening (98/100 plan items 26-28, 61, 62, 73):
  * a glyph-drawing exception, or an empty outline on a glyph that must have ink, is FATAL (strict=True, the default);
    all failures are collected first so the report is complete, then BuildError is raised (non-zero exit).
  * the independent raster check of the Boolean engine can be switched on (STACKRA_VALIDATE_BOOL=1 / validate=True);
    its per-call results are kept in BOOL_VALIDATION for the QA gates.
  * name table follows RIBBI rules (IDs 1/2/16/17), vertical metrics are coherent (hhea == typo, USE_TYPO_METRICS),
    gasp is present, timestamps are deterministic (buildenv: SOURCE_DATE_EPOCH).
"""
import os, sys, math, json, time
from types import SimpleNamespace
import buildenv                                   # pins SOURCE_DATE_EPOCH before fontTools reads it
import contract as K
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.ufoLib import UFOWriter
from fontTools.ttLib import newTable
import geom
import boolop
from geom import bbox, translate, s0, s1
from glyphs_lc import Ctx
import glyphset

UPM = 1000
EMPTY_OK = frozenset({'space'})                    # the only glyph allowed to have no outline
BOOL_VALIDATION = {}                               # glyph -> [(mismatched_cells, ink_cells), ...] of the last make_master


class BuildError(RuntimeError):
    """Raised when a master cannot be built to release standard."""


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


def make_master(d, w, XH=515, only=None, strict=True, validate=None):
    """Returns (ctx, glyphs, log).  log maps glyph -> failure text.  strict=True raises BuildError if log is non-empty."""
    if validate is None:
        validate = os.environ.get('STACKRA_VALIDATE_BOOL') == '1'
    boolop.VALIDATE = bool(validate)
    BOOL_VALIDATION.clear()
    c = Ctx(d, w, XH)
    out = {}; log = {}
    geom.ERR_LOG['max'] = 0
    for name, uni, fn, lcl, rcl in glyphset.R:
        if only and name not in only: continue
        boolop.QA_LOG.clear()
        try:
            cs = fn(c)
        except Exception as e:
            log[name] = 'ERR ' + repr(e); cs = []
        if validate and boolop.QA_LOG:
            BOOL_VALIDATION[name] = [tuple(q) for q in boolop.QA_LOG]
        if not cs:
            if name not in EMPTY_OK and name not in log:
                log[name] = 'EMPTY outline on a glyph that must have ink'
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
    if strict and log:
        lines = [f'  {n}: {m}' for n, m in sorted(log.items())]
        raise BuildError(f'master {d}/{w}: {len(log)} glyph(s) failed:\n' + '\n'.join(lines))
    return c, out, log


def write_ufo(path, d, w, glyphs, c, family=K.FAMILY, style='Regular'):
    import shutil
    if os.path.exists(path): shutil.rmtree(path)
    wr = UFOWriter(path, formatVersion=3)
    info = SimpleNamespace(familyName=family, styleName=style, unitsPerEm=UPM, ascender=K.VMETRICS['ascender'],
                           descender=K.VMETRICS['descender'], capHeight=c.CAP, xHeight=c.XH, italicAngle=0,
                           versionMajor=K.FONT_VERSION_MAJOR, versionMinor=K.FONT_VERSION_MINOR,
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


def name_strings(family, style, weight):
    """RIBBI rule: IDs 1/2 are family + Regular/Bold only; every other style moves into the family name (ID 1) and
    is repeated as typographic family/subfamily (IDs 16/17)."""
    ribbi = style in ('Regular', 'Bold')
    ps = f'{family.replace(" ", "")}-{style}'
    ns = {'uniqueFontIdentifier': f'{family}-{style}-{K.UNIQUE_ID_SUFFIX}', 'fullName': f'{family} {style}',
          'psName': ps, 'version': K.VERSION_STRING}
    if ribbi:
        ns.update(familyName=family, styleName=style)
    else:
        ns.update(familyName=f'{family} {style}', styleName='Regular', typographicFamily=family, typographicSubfamily=style)
    return ns


def fs_selection(weight):
    return (1 << 7) | ((1 << 5) if weight >= 700 else (1 << 6))     # USE_TYPO_METRICS + BOLD or REGULAR


def setup_metrics_tables(fb, c, weight, win_ascent=None, win_descent=None):
    m = K.VMETRICS
    fb.setupHorizontalHeader(ascent=m['ascender'], descent=m['descender'], lineGap=m['line_gap'])
    fb.setupOS2(version=4, sTypoAscender=m['typo_ascender'], sTypoDescender=m['typo_descender'], sTypoLineGap=m['typo_line_gap'],
                usWinAscent=win_ascent or m['win_ascent'], usWinDescent=win_descent or m['win_descent'],
                sxHeight=c.XH, sCapHeight=c.CAP, usWeightClass=weight, fsType=0, achVendID='STKR',
                fsSelection=fs_selection(weight))
    fb.font['OS/2'].recalcUnicodeRanges(fb.font)     # ulUnicodeRange from the real cmap (code-page bits stay unset: no Latin-1 claim)
    fb.setupPost(keepGlyphNames=True)
    gasp = newTable('gasp'); gasp.version = 1; gasp.gaspRange = {0xFFFF: 0x000F}   # gftools fix-nonhinting default
    fb.font['gasp'] = gasp
    fb.updateHead(fontRevision=K.FONT_VERSION_MAJOR + K.FONT_VERSION_MINOR / 10.0)
    if weight >= 700:
        fb.font['head'].macStyle |= 1


def build_ttf(path, glyphs, c, family=K.FAMILY, style='Regular', weight=400):
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
    fb.setupNameTable(name_strings(family, style, weight))
    setup_metrics_tables(fb, c, weight)
    fb.save(path)


if __name__ == '__main__':
    d = sys.argv[1] if len(sys.argv) > 1 else 'A'; w = int(sys.argv[2]) if len(sys.argv) > 2 else 400
    t = time.time()
    try:
        c, g, log = make_master(d, w)
    except BuildError as e:
        print('BUILD FAILED:', e, file=sys.stderr); sys.exit(2)
    print('built', len(g), 'glyphs in', round(time.time() - t, 1), 's; errors:', log, 'fit-err', round(geom.ERR_LOG['max'], 2))
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    os.makedirs(f'{base}/fonts/proto', exist_ok=True)
    build_ttf(f'{base}/fonts/proto/Stackra-{d}-{w}.ttf', g, c, family=f'Stackra Proto {d}', style='Regular', weight=w)
    print('ttf ok')
