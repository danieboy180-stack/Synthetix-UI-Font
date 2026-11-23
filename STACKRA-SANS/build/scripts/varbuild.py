import os, sys, json
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.cu2qu.cu2qu import curves_to_quadratic
from fontTools.designspaceLib import DesignSpaceDocument, SourceDescriptor, AxisDescriptor
from fontTools import varLib
import geom, fontbuild, harmonize
from geom import s0, rev_contour, bbox
from compat import canon

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def build_masters(weights):
    M = {}; fit = {}
    for w in weights:
        geom.ERR_LOG['max'] = 0
        c, g, log = fontbuild.make_master('A', w)
        for k, v in g.items(): v['contours'] = [rev_contour(x) for x in canon(v['contours'])]
        M[w] = (c, g); fit[w] = round(geom.ERR_LOG['max'], 2)
    return M, fit


def topology_report(M, ws):
    ref = M[ws[0]][1]; bad = {}
    for n in ref:
        counts = {w: len(M[w][1][n]['contours']) for w in ws}
        if len(set(counts.values())) > 1: bad[n] = counts
    return bad


def make_ttf_from_segments(path, order, adv, contours_by_glyph, c, weight, family, style, uni):
    """contours_by_glyph[name] = list of contours (segments with identical structure across masters)."""
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(order); fb.setupCharacterMap({u: n for n, u in uni.items() if u})
    tt = {}
    for n in order:
        pen = TTGlyphPen(None)
        for ctr in contours_by_glyph.get(n, []):
            pen.moveTo(s0(ctr[0]))
            for s in ctr:
                if s[0] == 'L': pen.lineTo(s[2])
                else:
                    pen.qCurveTo(*s[2:])   # s already quadratic spline pts
            pen.closePath()
        tt[n] = pen.glyph()
    fb.setupGlyf(tt)
    glyf = fb.font['glyf']; metrics = {}
    for n in order:
        g = glyf[n]; g.recalcBounds(glyf)
        metrics[n] = (adv[n], g.xMin if g.numberOfContours else 0)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=950, descent=-250, lineGap=0)
    fb.setupNameTable({'familyName': family, 'styleName': style, 'uniqueFontIdentifier': f'{family}-{style}-0.5.0-dev',
                       'fullName': f'{family} {style}', 'psName': f'{family.replace(" ","")}-{style}', 'version': 'Version 0.500'})
    fb.setupOS2(sTypoAscender=780, sTypoDescender=-220, sTypoLineGap=200, usWinAscent=1000, usWinDescent=280,
                sxHeight=c.XH, sCapHeight=c.CAP, usWeightClass=weight, fsType=0, achVendID='STKR', fsSelection=(1 << 6))
    fb.setupPost(keepGlyphNames=True)
    fb.save(path)


def build_vf(weights, out_dir):
    M, fit = build_masters(weights)
    bad = topology_report(M, weights)
    order = ['.notdef'] + list(M[weights[0]][1].keys())
    names = order[1:]
    harm = {w: {} for w in weights}; failed = []
    for n in names:
        per = [M[w][1][n]['contours'] for w in weights]
        if all(len(p) == 0 for p in per):
            for w in weights: harm[w][n] = []
            continue
        h = harmonize.harmonize(per)
        if h is None: failed.append(n); continue
        for i, w in enumerate(weights): harm[w][n] = h[i]
    for w in weights: harm[w]['.notdef'] = [rev_contour(x) for x in fontbuild.notdef(M[w][0])]
    if failed: return dict(ok=False, topology_bad=bad, harmonize_failed=failed, fit=fit)
    # quadratic conversion with identical structure across masters
    quad = {w: {} for w in weights}
    for n in order:
        nC = len(harm[weights[0]][n])
        for w in weights: quad[w][n] = []
        for ci in range(nC):
            nS = len(harm[weights[0]][n][ci])
            cols = {w: [] for w in weights}
            for si in range(nS):
                segs = [harm[w][n][ci][si] for w in weights]
                if segs[0][0] == 'L':
                    for w, s in zip(weights, segs): cols[w].append(s)
                else:
                    curves = [[s[1], s[2], s[3], s[4]] for s in segs]
                    splines = curves_to_quadratic(curves, [1.0] * len(curves))
                    if splines is None:
                        return dict(ok=False, topology_bad=bad, cu2qu_failed=[n, ci, si], fit=fit)
                    for w, sp in zip(weights, splines):
                        cols[w].append(('Q',) + tuple(tuple(p) for p in sp))
            for w in weights: quad[w][n].append(cols[w])
    uni = {n: M[weights[0]][1][n]['uni'] for n in names}
    os.makedirs(out_dir, exist_ok=True)
    ds = DesignSpaceDocument()
    ax = AxisDescriptor(); ax.name = 'Weight'; ax.tag = 'wght'; ax.minimum = min(weights); ax.default = 400; ax.maximum = max(weights)
    ds.addAxis(ax)
    for w in weights:
        adv = {'.notdef': 520}; adv.update({n: M[w][1][n]['adv'] for n in names})
        p = f'{out_dir}/master-{w}.ttf'
        make_ttf_from_segments(p, order, adv, quad[w], M[w][0], w, 'Stackra Sans', f'W{w}', uni)
        sd = SourceDescriptor(); sd.path = p; sd.name = f'master{w}'; sd.location = {'Weight': w}
        if w == 400: sd.copyInfo = True
        ds.addSource(sd)
    dsp = f'{out_dir}/Stackra.designspace'; ds.write(dsp)
    vf, _, _ = varLib.build(dsp)
    vpath = f'{BASE}/fonts/variable/StackraSans-VF.ttf'
    os.makedirs(os.path.dirname(vpath), exist_ok=True)
    vf.save(vpath)
    return dict(ok=True, topology_bad=bad, fit=fit, path=vpath, weights=weights)


if __name__ == '__main__':
    ws = [int(x) for x in sys.argv[1:]] or [300, 400, 500]
    r = build_vf(ws, f'{BASE}/build/vf_masters')
    print(json.dumps(r, indent=1)[:2500])
