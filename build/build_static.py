"""build_static.py - V4 static masters from the frozen V3 baseline binaries (deterministic).

Declarative steps (each is a function applied identically to every master):
  1 dotbelow mark   2 Latin gap composites   3 Pri-African (Hausa/Yoruba/Igbo) letters   4 numerals
  5 UI symbols      6 layout (GSUB features, ccmp, kerning/anchor inheritance)   7 metadata   8 save
Existing V3 glyph outlines/advances are never edited (regression ledger proves it); only the .tf figure set is re-centred
to an exactly equal advance.
"""
import sys, os, json, math, calendar, datetime, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fonteditor import *
from fonteditor import _r, _arc_segs
from fontTools.ttLib import TTFont
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.ttLib.tables import otTables as ot

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
CFG = json.load(open(os.path.join(ROOT, 'build', 'config.json')))
MAC = 2082844800


def epoch_value():
    e = int(os.environ.get('SOURCE_DATE_EPOCH', CFG['source_date_epoch']))
    return e + MAC


# ----------------------------------------------------------------------------- parameters
def params(m):
    h = m.runs_x('H', 150, 1)[0]; tv = h[1] - h[0] + 1
    eb = m.bounds('E'); xe = round(eb[0] + 0.75 * (eb[2] - eb[0]))
    ry = m.runs_y('E', xe, 1); th = ry[-1][1] - ry[-1][0] + 1
    return dict(tv=tv, th=th, cap=700, xh=500, asc=729)


def anchor_tables(m):
    st = m.mark_base_subtable()
    bases = {g: r for g, r in zip(st.BaseCoverage.glyphs, st.BaseArray.BaseRecord)}
    marks = {g: (r.Class, (r.MarkAnchor.XCoordinate, r.MarkAnchor.YCoordinate)) for g, r in zip(st.MarkCoverage.glyphs, st.MarkArray.MarkRecord)}
    return bases, marks


def base_anchor(m, base, cls, bases):
    rec = bases.get(base)
    if rec is not None and rec.BaseAnchor[cls] is not None:
        a = rec.BaseAnchor[cls]; return a.XCoordinate, a.YCoordinate
    b = m.bounds(base)                       # fallback: ink centre at the relevant edge (documented in the register)
    if cls == 0:
        top = 700 if b[3] >= 600 else 496
        runs = m.runs_x(base, top - 40, 1) or [(b[0], b[2])]
        return (runs[0][0] + runs[-1][1]) / 2, top
    return (b[0] + b[2]) / 2, 0


def place_mark(m, base, mark, cls):
    """Offset (dx,dy) that places `mark` on `base` exactly as GPOS mark-to-base would."""
    bases, marks = anchor_tables(m)
    bx, by = base_anchor(m, base, cls, bases); mk = marks[mark][1]
    return bx - mk[0], by - mk[1]


def stack(m, name, cp, base, mark, cls, dx_extra=0, dy_extra=0, base_adv=None):
    dx, dy = place_mark(m, base, mark, cls)
    m.composite(name, [(base, 0, 0), (mark, dx + dx_extra, dy + dy_extra)], base_adv or m.adv(base), (cp,) if cp else (), parent=base)


# ----------------------------------------------------------------------------- 1. dot below mark
def step_dotbelow(m, P):
    dot = m.outline('dotaccent')
    rp = xform(dot, (1, 0, 0, 1, 0, -757))          # dot top at y=-56 (same gap as comma below)
    m.from_rp('uni0323', rp, 0, (0x0323,))
    m.add_mark_to_class('uni0323', 1, (105, 0))      # bottom class: reuses every existing bottom anchor
    # i/j tittle rule: i + dotbelow + top mark must still drop the tittle
    st = m.font['GSUB'].table.LookupList.Lookup[2].SubTable[0]; st = getattr(st, 'ExtSubTable', st)
    st.LookAheadClassDef.classDefs['uni0323'] = 2


# ----------------------------------------------------------------------------- 2. Latin gap composites
def step_latin(m, P):
    A = m.cmap()
    n = lambda ch: m.gname(ch)
    # circumflex / breve / tilde letters (Latin Extended-A gaps)
    for up, lo, mark, cp_u, cp_l in [('C', 'c', 'uni0302', 0x108, 0x109), ('G', 'g', 'uni0302', 0x11C, 0x11D), ('H', None, 'uni0302', 0x124, None),
                                     ('S', 's', 'uni0302', 0x15C, 0x15D), ('E', 'e', 'uni0306', 0x114, 0x115), ('I', 'dotlessi', 'uni0306', 0x12C, 0x12D),
                                     ('O', 'o', 'uni0306', 0x14E, 0x14F), ('I', 'dotlessi', 'tildecomb', 0x128, 0x129), ('U', 'u', 'tildecomb', 0x168, 0x169)]:
        if cp_u not in A: stack(m, 'uni%04X' % cp_u, cp_u, up, mark, 0)
        if lo and cp_l not in A: stack(m, 'uni%04X' % cp_l, cp_l, lo, mark, 0)
    stack(m, 'uni0134', 0x134, 'J', 'uni0302', 0); stack(m, 'uni0135', 0x135, 'uni0237', 'uni0302', 0)
    # h with circumflex over the ascender stem
    xs = m.runs_x('h', 640, 1)[0]; xc = (xs[0] + xs[1]) / 2; _, ma = anchor_tables(m)[1]['uni0302']
    m.composite('uni0125', [('h', 0, 0), ('uni0302', otRound(xc - ma[0]), 204 + (P['asc'] - P['cap']))], m.adv('h'), (0x125,), parent='h')
    stack(m, 'uni0162', 0x162, 'T', 'uni0327', 1); stack(m, 'uni0163', 0x163, 't', 'uni0327', 1)
    # Ŧ ŧ  (bar through the stem)
    tb = m.bounds('T'); r = m.outline('T'); bar = rect(tb[0] + 40, 300, tb[2] - 40, 300 + P['th'] - 6)
    xs = m.runs_x('T', 400, 1)[0]; xc = (xs[0] + xs[1]) // 2; half = int(P['tv'] * 0.95)
    m.from_rp('uni0166', merge(r, rect(xc - half, 330, xc + half, 330 + P['th'] - 8)), m.adv('T'), (0x166,), parent='T')
    tb = m.bounds('t'); xs = m.runs_x('t', 250, 1)[0]; xc = (xs[0] + xs[1]) // 2
    m.from_rp('uni0167', merge(m.outline('t'), rect(xc - half, 235, xc + half, 235 + P['th'] - 10)), m.adv('t'), (0x167,), parent='t')
    # Ŀ ŀ  ŉ
    pc = 'periodcentered'; pb = m.bounds(pc)
    m.composite('uni013F', [('L', 0, 0), (pc, m.adv('L') - pb[0] - 10, 0)], m.adv('L') + (pb[2] - pb[0]) + 20, (0x13F,), parent='L')
    m.composite('uni0140', [('l', 0, 0), (pc, m.adv('l') - pb[0] - 10, 0)], m.adv('l') + (pb[2] - pb[0]) + 20, (0x140,), parent='l')
    qb = m.bounds('quoteright'); qa = m.adv('quoteright')
    m.composite('uni0149', [('quoteright', 0, 0), ('n', qa - 10, 0)], qa - 10 + m.adv('n'), (0x149,))
    # ĸ (kra): k with the ascender cut to x-height (move the two ascender-top points)
    rp = m.outline('k'); val = []
    for op, args in rp.value:
        val.append((op, tuple(None if a is None else ((a[0], P['xh']) if a[1] >= P['asc'] - 2 else a) for a in args)))
    rp2 = RecordingPen(); rp2.value = val
    m.from_rp('uni0138', rp2, m.adv('k'), (0x138,), parent='k')
    # Latin-1 gaps
    bar_b = m.bounds('bar'); yc = (bar_b[1] + bar_b[3]) // 2
    gap = 110
    m.from_rp('brokenbar', merge(rect(bar_b[0], yc + gap // 2, bar_b[2], bar_b[3]), rect(bar_b[0], bar_b[1], bar_b[2], yc - gap // 2)), m.adv('bar'), (0xA6,))
    mb = m.bounds('minus'); hb = mb[3] - mb[1]; t = int(P['tv'] * 0.95)
    m.from_rp('logicalnot', orient(poly([(mb[0], mb[1]), (mb[0], mb[3]), (mb[2], mb[3]), (mb[2], mb[3] - 230), (mb[2] - t, mb[3] - 230), (mb[2] - t, mb[1])]), True), m.adv('minus'), (0xAC,))
    pb_ = m.bounds('plus'); ph = pb_[3] - pb_[1]; yc = (pb_[1] + pb_[3]) / 2; gp = 70; H = ph + gp + hb
    ybar = yc - H / 2
    m.from_rp('plusminus', merge(xform(m.outline('plus'), (1, 0, 0, 1, 0, otRound(ybar + hb + gp - pb_[1]))), rect(pb_[0], otRound(ybar), pb_[2], otRound(ybar + hb))), m.adv('plus'), (0xB1,))
    mu = m.runs_x('u', 250, 1)[0]
    m.from_rp('uni00B5', merge(m.outline('u'), rect(mu[0], -171, mu[1], 120)), m.adv('u'), (0xB5,), parent='u')
    cx, cy, r0 = 330, 390, 135
    ticks = [stroke_polyline([(cx + (r0 - 20) * math.cos(a), cy + (r0 - 20) * math.sin(a)), (cx + (r0 + 95) * math.cos(a), cy + (r0 + 95) * math.sin(a))], int(P['tv'] * 0.8))
             for a in (math.radians(45), math.radians(135), math.radians(225), math.radians(315))]
    m.from_rp('currency', merge(ring(cx, cy, r0 + 15, r0 + 15, int(P['tv'] * 0.85), int(P['th'] * 0.85)), *ticks), 660, (0xA4,))
    # aliases of existing glyphs (identical encoded characters)
    for cp, g in [(0xAD, 'hyphen'), (0x2010, 'hyphen'), (0x2011, 'hyphen'), (0x2012, 'endash'), (0x2015, 'emdash'), (0x2215, 'slash'), (0x2219, 'periodcentered')]:
        if cp not in m.cmap(): m.map(cp, g)


# ----------------------------------------------------------------------------- 3. Pri-African letters
def flag(xc, T, tv, th, Lh, Rh, Rv):
    cx, cy = xc + Lh, T - th / 2 - Rv
    rp = RecordingPen(); rp.moveTo(_r((xc, T))); rp.lineTo(_r((cx, T)))
    for c, e in _arc_segs(cx, cy, Rh + tv / 2, Rv + th / 2, math.pi / 2, 0): rp.qCurveTo(c, e)
    rp.lineTo(_r((cx + Rh - tv / 2, cy)))
    for c, e in _arc_segs(cx, cy, Rh - tv / 2, Rv - th / 2, 0, math.pi / 2): rp.qCurveTo(c, e)
    rp.lineTo(_r((xc, T - th))); rp.closePath()
    return orient(rp, True)


def hooked(m, P, name, cp, base, xrun, T, side, Lh, Rh, Rv, y_probe, stem_index=0, bump=0.5, lsb_min=30):
    xs = m.runs_x(base, y_probe, 1)[stem_index]; xc = (xs[0] + xs[1]) / 2
    f = flag(xc, T, P['tv'], P['th'], Lh, Rh, Rv)
    adv = m.adv(base); shape = m.outline(base)
    if side == 'left':
        f = xform(f, (-1, 0, 0, 1, otRound(2 * xc), 0), mirror=True)
        both = merge(shape, f); xmin = BoundsPen(None)
        bp = BoundsPen(None); both.replay(bp); d = max(0, lsb_min - bp.bounds[0])
        m.from_rp(name, xform(both, (1, 0, 0, 1, d, 0)), adv + d, (cp,), parent=base)
    else:
        both = merge(shape, f); bp = BoundsPen(None); both.replay(bp); ob = m.bounds(base)
        ext = max(0, bp.bounds[2] - ob[2]); m.from_rp(name, both, adv + otRound(bump * ext), (cp,), parent=base)


def step_african(m, P):
    A = m.cmap(); tv, th = P['tv'], P['th']
    # dot-below precomposed (Yoruba / Igbo / Hausa-adjacent)
    for base, cp in [('E', 0x1EB8), ('e', 0x1EB9), ('O', 0x1ECC), ('o', 0x1ECD), ('S', 0x1E62), ('s', 0x1E63), ('I', 0x1ECA), ('i', 0x1ECB), ('U', 0x1EE4), ('u', 0x1EE5)]:
        stack(m, 'uni%04X' % cp, cp, base, 'uni0323', 1)
    # i-dot variant used when a top tone mark follows (tittle would collide)
    stack(m, 'uni1ECB.dl', None, 'dotlessi', 'uni0323', 1, base_adv=m.adv('i')); m.parent['uni1ECB.dl'] = 'i'; m.anchor_parent['uni1ECB.dl'] = 'dotlessi'
    # tone-marked nasals and dotted n (Yoruba / Igbo)
    stack(m, 'uni01F8', 0x1F8, 'N', 'gravecomb', 0); stack(m, 'uni01F9', 0x1F9, 'n', 'gravecomb', 0)
    stack(m, 'uni1E3E', 0x1E3E, 'M', 'acutecomb', 0); stack(m, 'uni1E3F', 0x1E3F, 'm', 'acutecomb', 0)
    stack(m, 'uni1E44', 0x1E44, 'N', 'uni0307', 0); stack(m, 'uni1E45', 0x1E45, 'n', 'uni0307', 0)
    m.composite('uni02BC', [('quoteright', 0, 0)], m.adv('quoteright'), (0x2BC,))
    # Hausa hooked letters
    cap, asc, xh = P['cap'], P['asc'], P['xh']
    hooked(m, P, 'uni0181', 0x181, 'B', None, cap, 'left', 10, 110, 105, 560)
    hooked(m, P, 'uni018A', 0x18A, 'D', None, cap, 'left', 10, 110, 105, 560)
    hooked(m, P, 'uni0198', 0x198, 'K', None, cap, 'left', 10, 110, 105, 600)
    hooked(m, P, 'uni0253', 0x253, 'b', None, asc, 'right', 10, 120, 110, 640)
    hooked(m, P, 'uni0257', 0x257, 'd', None, asc, 'right', 10, 120, 110, 640, stem_index=-1, bump=0.55)
    hooked(m, P, 'uni0199', 0x199, 'k', None, asc, 'right', 10, 120, 110, 640)
    hooked(m, P, 'uni01B3', 0x1B3, 'Y', None, cap, 'right', 10, 110, 105, 680, stem_index=-1, bump=0.55)
    hooked(m, P, 'uni01B4', 0x1B4, 'y', None, xh, 'right', 10, 95, 80, 470, stem_index=-1, bump=0.55)
    # open E and open O (mirror of C/c) used across West African orthographies
    for nm, cp, base, parent in [('uni0186', 0x186, 'C', 'O'), ('uni0254', 0x254, 'c', 'o')]:
        a = m.adv(base); m.from_rp(nm, xform(m.outline(base), (-1, 0, 0, 1, a, 0), mirror=True), a, (cp,), parent=parent)
    for nm, cp, top, ym, parent in [('uni0190', 0x190, 710, 378, 'O'), ('uni025B', 0x25B, 510, 252, 'o')]:
        ref = 'C' if top > 600 else 'c'; b = m.bounds(ref); wfull = b[2] - b[0]; w = otRound(wfull * (0.84 if top > 600 else 0.9)); lsb = b[0]
        yb = -10; ry_t = (top - th / 2 - ym) / 2; ry_b = (ym - (yb + th / 2)) / 2
        rx = (w - tv) / 2 * 0.98; cx = lsb + tv / 2 + rx
        top_arc = stroke_arc(cx, ym + ry_t, rx, ry_t, 38, 270, tv, th); bot_arc = stroke_arc(cx, ym - ry_b, rx, ry_b, 90, 322, tv, th)
        mid = rect(otRound(cx), otRound(ym - th / 2), otRound(cx + 0.62 * rx), otRound(ym + th / 2))
        m.from_rp(nm, merge(top_arc, bot_arc, mid), m.adv(ref) - (wfull - w), (cp,), parent=parent)


# ----------------------------------------------------------------------------- 4. numerals
DIG = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']


def step_numerals(m, P):
    g = m.glyf; tv, th = P['tv'], P['th']
    ops = ['plus', 'minus', 'multiply', 'divide', 'equal', 'greater', 'less']
    names = [d + '.tf' for d in DIG] + [o + '.tf' for o in ops]
    W = max(m.adv(d + '.tf') for d in DIG)
    for n in names:
        old = m.adv(n); dx = (W - old) / 2
        gl = g[n]
        if gl.isComposite():
            for c in gl.components: c.x += otRound(dx)
        else:
            gl.coordinates.translate((otRound(dx), 0))
        gl.recalcBounds(g); m.hmtx[n] = (W, gl.xMin)
    m.tab_width = W
    # slashed zero (proportional + tabular)
    for src, dst in [('zero', 'zero.slash'), ('zero.tf', 'zero.tf.slash')]:
        b = m.bounds(src); w, h = b[2] - b[0], b[3] - b[1]
        sl = stroke_polyline([(b[0] + 0.24 * w, b[1] + 0.2 * h), (b[2] - 0.24 * w, b[3] - 0.2 * h)], otRound(th * 0.85))
        m.from_rp(dst, merge(m.outline(src), sl), m.adv(src), parent=src)
    # superior / inferior / numerator / denominator figures (scaled + stroke compensated)
    s = 0.62; dxe, dye = (1 - s) * tv * 0.5 * 0.45, (1 - s) * th * 0.5 * 0.45
    sets = {'sups': 295, 'subs': -90, 'numr': 266, 'dnom': 0}
    std_names = {'sups': ['zerosuperior', 'onesuperior', 'twosuperior', 'threesuperior', 'foursuperior', 'fivesuperior', 'sixsuperior', 'sevensuperior', 'eightsuperior', 'ninesuperior'],
                 'subs': [d + 'inferior' for d in DIG]}
    cps = {'sups': {0: 0x2070, 1: 0xB9, 2: 0xB2, 3: 0xB3, **{i: 0x2070 + i for i in range(4, 10)}}, 'subs': {i: 0x2080 + i for i in range(10)}}
    for kind, y0 in sets.items():
        for i, d in enumerate(DIG):
            rp = xform(m.outline(d), (s, 0, 0, s, 0, y0)); rp = embolden(rp, dxe, dye)
            bp = BoundsPen(None); rp.replay(bp); o = m.bounds(d)
            a = otRound(s * m.adv(d) + 2 * dxe)
            nm = std_names[kind][i] if kind in std_names else '%s.%s' % (d, kind)
            cp = cps.get(kind, {}).get(i)
            m.from_rp(nm, xform(rp, (1, 0, 0, 1, otRound(dxe), 0)), a, (cp,) if cp else ())
            m.set_name = getattr(m, 'set_name', {}); m.set_name[(kind, i)] = nm
    # fraction slash (ink overlaps neighbouring figures)
    w = otRound((tv + th) / 2 * 0.85)
    m.from_rp('fraction', stroke_polyline([(-80, -60), (190, 760)], w), 110, (0x2044,))
    m.hmtx['fraction'] = (110, m.glyf['fraction'].xMin)
    def frac(name, cp, nu, de):
        a = m.set_name[('numr', nu)]; d = m.set_name[('dnom', de)]
        m.composite(name, [(a, 0, 0), ('fraction', m.adv(a), 0), (d, m.adv(a) + 110, 0)], m.adv(a) + 110 + m.adv(d), (cp,))
    frac('onequarter', 0xBC, 1, 4); frac('onehalf', 0xBD, 1, 2); frac('threequarters', 0xBE, 3, 4)
    frac('uni2153', 0x2153, 1, 3); frac('uni2154', 0x2154, 2, 3); frac('uni215B', 0x215B, 1, 8)


# ----------------------------------------------------------------------------- 5. UI symbols
def step_symbols(m, P):
    tv, th = P['tv'], P['th']
    m.from_rp('uni2713', stroke_polyline([(60, 300), (225, 120), (590, 660)], otRound(tv * 0.92)), 660, (0x2713,))
    eq = m.bounds('equal'); xc = (eq[0] + eq[2]) / 2
    m.from_rp('uni2260', merge(m.outline('equal'), stroke_polyline([(xc - 85, 70), (xc + 85, 630)], otRound(th * 0.9))), m.adv('equal'), (0x2260,))
    for nm, cp, base in [('lessequal', 0x2264, 'less'), ('greaterequal', 0x2265, 'greater')]:
        b = m.bounds(base); mb = m.bounds('minus'); hb = mb[3] - mb[1]; up = 40
        m.from_rp(nm, merge(xform(m.outline(base), (1, 0, 0, 1, 0, up)), rect(b[0], b[1] + up - 45 - hb, b[2], b[1] + up - 45)), m.adv(base), (cp,))
    tb = m.bounds('asciitilde'); d = (tb[3] - tb[1]) + 55
    m.from_rp('approxequal', merge(xform(m.outline('asciitilde'), (1, 0, 0, 1, 0, otRound(d / 2))), xform(m.outline('asciitilde'), (1, 0, 0, 1, 0, -otRound(d / 2)))), m.adv('asciitilde'), (0x2248,))
    rx, ry = 205, 160; yc = 350
    m.from_rp('infinity', merge(ring(400 - 175, yc, rx, ry, otRound(tv * 0.95), otRound(th * 0.95)), ring(400 + 175, yc, rx, ry, otRound(tv * 0.95), otRound(th * 0.95))), 800, (0x221E,))
    a = m.adv('ordmasculine'); m.composite('uni2116', [('N', 0, 0), ('ordmasculine', m.adv('N') + 20, 0)], m.adv('N') + 20 + a, (0x2116,))
    cb = m.bounds('C'); xc = (cb[0] + cb[2]) // 2; w = otRound(th * 0.9)
    m.from_rp('uni20B5', merge(m.outline('C'), rect(xc - w // 2, -80, xc + w // 2, 780)), m.adv('C'), (0x20B5,))
    # Indian rupee sign: two bars, bowl, diagonal leg
    yt, yb = 700 - th / 2, 330; cy = (yt + yb) / 2; ryb = (yt - yb) / 2
    bars = [rect(55, 700 - th, 545, 700), rect(55, 700 - 2 * th - 78, 545, 700 - th - 78)]
    bowl = stroke_arc(300, cy, 200, ryb, 90, -90, tv, th)
    leg = stroke_polyline([(290, yb + 10), (560, 0)], otRound(tv * 0.95))
    m.from_rp('uni20B9', merge(*bars, bowl, leg), 620, (0x20B9,))



# ----------------------------------------------------------------------------- 5b. opt-in disambiguation set (ss13)
def step_disambig(m, P):
    """ss13: tailed l and serifed I for IDs, codes and OTPs (Il1 / O0 are indistinguishable at 12-14 px by tools/confusables.py)."""
    tv, th = P['tv'], P['th']
    xs = m.runs_x('l', 120, 1)[0]; xc = (xs[0] + xs[1]) / 2
    tail = xform(flag(xc, th, tv, th, 10, 70, 95), (1, 0, 0, -1, 0, th), mirror=True)
    both = merge(m.outline('l'), tail); bp = BoundsPen(None); both.replay(bp)
    m.from_rp('l.ss13', both, max(m.adv('l'), otRound(bp.bounds[2] + (m.adv('l') - m.bounds('l')[2]))), parent='l')
    xs = m.runs_x('I', 350, 1)[0]; xc = (xs[0] + xs[1]) / 2; half = otRound(tv * 1.55); t = otRound(th * 0.8)
    bars = merge(rect(otRound(xc - half), 0, otRound(xc + half), t), rect(otRound(xc - half), P['cap'] - t, otRound(xc + half), P['cap']))
    both = merge(m.outline('I'), bars); bp = BoundsPen(None); both.replay(bp); lsb = 45
    d = lsb - bp.bounds[0]
    m.from_rp('I.ss13', xform(both, (1, 0, 0, 1, d, 0)), otRound(bp.bounds[2] - bp.bounds[0] + 2 * lsb), parent='I')

# ----------------------------------------------------------------------------- 6. layout
FEA = """
languagesystem DFLT dflt;
languagesystem latn dflt;
@dig  = [%(dig)s];
@sups = [%(sups)s];
@subs = [%(subs)s];
@numr = [%(numr)s];
@dnom = [%(dnom)s];
feature lnum { sub @dig by @dig; } lnum;
feature ss13 { sub l by l.ss13; sub I by I.ss13; } ss13;
feature zero { sub zero by zero.slash; sub zero.tf by zero.tf.slash; } zero;
feature sups { sub @dig by @sups; } sups;
feature subs { sub @dig by @subs; } subs;
feature sinf { sub @dig by @subs; } sinf;
feature numr { sub @dig by @numr; } numr;
feature dnom { sub @dig by @dnom; } dnom;
feature frac {
    lookup FRAC_NUM { rsub @dig' [fraction slash @numr] by @numr; } FRAC_NUM;
    lookup FRAC_SL  { sub @numr slash' by fraction; } FRAC_SL;
    lookup FRAC_DEN { sub [fraction @dnom] @dig' by @dnom; } FRAC_DEN;
} frac;
"""


def step_layout(m, P):
    f = m.font; sn = m.set_name
    fea = FEA % dict(dig=' '.join(DIG), sups=' '.join(sn[('sups', i)] for i in range(10)), subs=' '.join(sn[('subs', i)] for i in range(10)),
                     numr=' '.join(sn[('numr', i)] for i in range(10)), dnom=' '.join(sn[('dnom', i)] for i in range(10)))
    sc = TTFont(); sc.setGlyphOrder(f.getGlyphOrder())
    addOpenTypeFeaturesFromString(sc, fea, tables=['GSUB'])
    merge_layout(f, sc, 'GSUB')
    # ss13 spacing: loosen rn / cl / vv (confusable with m / d / w at 12-14 px). Opt-in only; default kerning is untouched.
    sc2 = TTFont(); sc2.setGlyphOrder(f.getGlyphOrder())
    addOpenTypeFeaturesFromString(sc2, 'languagesystem DFLT dflt;\nlanguagesystem latn dflt;\nfeature ss13 { pos r n 40; pos c l 40; pos v v 40; } ss13;\n', tables=['GPOS'])
    merge_layout(f, sc2, 'GPOS')
    gs = f['GSUB'].table
    # tnum/pnum round trip for slashed zero
    for fr in gs.FeatureList.FeatureRecord:
        for li in fr.Feature.LookupListIndex:
            lk = gs.LookupList.Lookup[li]
            for st in lk.SubTable:
                st = getattr(st, 'ExtSubTable', st)
                if lk.LookupType == 1 and fr.FeatureTag == 'tnum' and 'zero' in st.mapping:
                    st.mapping['zero.slash'] = 'zero.tf.slash'
                if lk.LookupType == 1 and fr.FeatureTag == 'pnum' and 'zero.tf' in st.mapping:
                    st.mapping['zero.tf.slash'] = 'zero.slash'
    # tittle collision rule for precomposed ị followed by a top mark
    cc = gs.LookupList.Lookup[2].SubTable[0]; cc = getattr(cc, 'ExtSubTable', cc)
    sub = ot.SingleSubst(); sub.mapping = {'uni1ECB': 'uni1ECB.dl'}; lk = ot.Lookup(); lk.LookupType = 1; lk.LookupFlag = 0; lk.SubTable = [sub]; lk.SubTableCount = 1
    gs.LookupList.Lookup.append(lk); gs.LookupList.LookupCount = len(gs.LookupList.Lookup); li = len(gs.LookupList.Lookup) - 1
    cc.Coverage.glyphs.append('uni1ECB'); cc.InputClassDef.classDefs['uni1ECB'] = 3
    rule = ot.ChainSubClassRule(); rule.Backtrack = []; rule.Input = []; rule.LookAhead = [1]; rec = ot.SubstLookupRecord(); rec.SequenceIndex = 0; rec.LookupListIndex = li
    rule.SubstLookupRecord = [rec]; rule.BacktrackGlyphCount = 0; rule.InputGlyphCount = 1; rule.LookAheadGlyphCount = 1; rule.SubstCount = 1
    cs = ot.ChainSubClassSet(); cs.ChainSubClassRule = [rule]; cs.ChainSubClassRuleCount = 1
    while len(cc.ChainSubClassSet) < 4: cc.ChainSubClassSet.append(None)
    cc.ChainSubClassSet[3] = cs; cc.ChainSubClassSetCount = len(cc.ChainSubClassSet)
    m.finalize()
    for g_ in m.created:
        gl = f['glyf'][g_]
        if not gl.isComposite() and gl.numberOfContours > 1: gl.flags[0] |= 0x40   # OVERLAP_SIMPLE
        gd = f['GDEF'].table.GlyphClassDef.classDefs
        if g_ not in gd: gd[g_] = 1


# ----------------------------------------------------------------------------- 7/8. metadata + save
def step_metadata(m, style, wclass):
    f = m.font; fam = 'Synthetix UI'; ribbi = style == 'Regular'; ver = CFG['font_version']; n = f['name']
    ps = 'SynthetixUI-' + style
    rec = {1: fam if ribbi else '%s %s' % (fam, style), 2: 'Regular', 3: '%s;%s;%s' % (fam, ver, ps), 4: '%s %s' % (fam, style),
           5: 'Version %s; modified from Instrument Sans 1.000' % ver, 6: ps,
           10: 'Modified from Instrument Sans (SIL OFL 1.1): engineered weights, proportions, spacing, Pri-African Latin coverage. Not affiliated with Pinterest.'}
    if not ribbi: rec[16] = fam; rec[17] = style
    for i in (1, 2, 3, 4, 5, 6, 10, 16, 17): n.removeNames(nameID=i)
    for i, v in rec.items():
        n.setName(v, i, 3, 1, 0x409); n.setName(v, i, 1, 0, 0)
    o = f['OS/2']; o.usWeightClass = wclass
    o.usWinAscent = 1000; o.usWinDescent = 340      # V3 defect fixed: comma-below reached -329 (SemiBold) but winDescent was 300 (clipping on Windows)
    f['head'].fontRevision = float(ver); f['head'].created = epoch_value(); f['head'].modified = epoch_value()
    advs = [a for a, _ in f['hmtx'].metrics.values() if a > 0]
    f['hhea'].advanceWidthMax = max(advs); o.xAvgCharWidth = round(sum(advs) / len(advs))
    o.recalcUnicodeRanges(f)
    if 'STAT' in f: del f['STAT']


def build_master(src, style, wclass, out):
    m = Master(src, style); P = params(m)
    step_dotbelow(m, P); step_latin(m, P); step_african(m, P); step_numerals(m, P); step_symbols(m, P); step_disambig(m, P); step_layout(m, P)
    step_metadata(m, style, wclass)
    m.font.save(out)
    return P, m


if __name__ == '__main__':
    base = os.path.join(ROOT, 'baseline', 'v3'); out = os.path.join(ROOT, 'build', 'masters'); os.makedirs(out, exist_ok=True)
    for style, wc in (('Regular', 400), ('Medium', 500), ('SemiBold', 600)):
        P, m = build_master(os.path.join(base, 'SynthetixUI-%s.ttf' % style), style, wc, os.path.join(out, 'SynthetixUI-%s.ttf' % style))
        print(style, P, 'new glyphs', len(m.created), 'tab width', m.tab_width)
