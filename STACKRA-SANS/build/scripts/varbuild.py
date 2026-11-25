"""Build the variable font from point-compatible masters.

V6 hardening (98/100 plan items 26-28, 54-58, 62, 78):
  * topology is checked at CONTOUR level before harmonisation (count, direction, correspondence) and at SEGMENT level
    after it (count, types, direction); any issue fails the build (non-zero exit) and is written to
    reports/build_reports/topology_report.json
  * glyph failures are fatal (fontbuild.BuildError)
  * default master carries the final VF names (the V5 VF was named 'Stackra Sans W400')
  * named instances + STAT axis labels are declared in the designspace
  * coherent vertical metrics, gasp, deterministic timestamps come from fontbuild/buildenv
"""
import os, sys, json
import buildenv
import contract as K
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.cu2qu.cu2qu import curves_to_quadratic
from fontTools.designspaceLib import (DesignSpaceDocument, SourceDescriptor, AxisDescriptor, AxisLabelDescriptor,
                                      InstanceDescriptor)
from fontTools import varLib
import geom, fontbuild, harmonize
from geom import s0, rev_contour, bbox, area
from compat import canon

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
REPORT_DIR = f'{BASE}/reports/build_reports'


def build_masters(weights, strict=True):
    M = {}; fit = {}
    for w in weights:
        geom.ERR_LOG['max'] = 0
        c, g, log = fontbuild.make_master('A', w, strict=strict)
        for k, v in g.items(): v['contours'] = [rev_contour(x) for x in canon(v['contours'])]
        M[w] = (c, g); fit[w] = round(geom.ERR_LOG['max'], 2)
    return M, fit


def _center(c):
    b = bbox([c]); return ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)


def topology_report(M, ws):
    """Pre-harmonisation contour-level report: {glyph: [issue, ...]} (empty dict == compatible)."""
    ref = M[ws[0]][1]; bad = {}
    for n in ref:
        issues = []
        rc = ref[n]['contours']
        for w in ws[1:]:
            cc = M[w][1][n]['contours']
            if len(cc) != len(rc):
                issues.append({'weight': w, 'issue': 'contour_count', 'reference': len(rc), 'got': len(cc)}); continue
            for ci, (a, b) in enumerate(zip(rc, cc)):
                if (area(a) > 0) != (area(b) > 0):
                    issues.append({'weight': w, 'contour': ci, 'issue': 'direction'})
                ca, cb = _center(a), _center(b)
                shift = ((ca[0] - cb[0]) ** 2 + (ca[1] - cb[1]) ** 2) ** 0.5
                if shift > K.CONTOUR_CORRESPONDENCE_MAX_SHIFT:
                    issues.append({'weight': w, 'contour': ci, 'issue': 'correspondence_shift', 'units': round(shift, 1)})
                ratio = abs(area(b)) / max(abs(area(a)), 1)
                if not (K.CONTOUR_CORRESPONDENCE_AREA_RATIO[0] <= ratio <= K.CONTOUR_CORRESPONDENCE_AREA_RATIO[1]):
                    issues.append({'weight': w, 'contour': ci, 'issue': 'correspondence_area_ratio', 'ratio': round(ratio, 2)})
        if issues: bad[n] = issues
    return bad


def point_compat_report(harm, weights, names):
    """Post-harmonisation segment-level report: what varLib actually needs."""
    bad = {}
    for n in names:
        issues = []
        ref = harm[weights[0]][n]
        for w in weights[1:]:
            cur = harm[w][n]
            if len(cur) != len(ref):
                issues.append({'weight': w, 'issue': 'contour_count', 'reference': len(ref), 'got': len(cur)}); continue
            for ci, (a, b) in enumerate(zip(ref, cur)):
                if len(a) != len(b):
                    issues.append({'weight': w, 'contour': ci, 'issue': 'segment_count', 'reference': len(a), 'got': len(b)}); continue
                ta = [s[0] for s in a]; tb = [s[0] for s in b]
                if ta != tb:
                    issues.append({'weight': w, 'contour': ci, 'issue': 'segment_types',
                                   'at': [i for i, (x, y) in enumerate(zip(ta, tb)) if x != y]})
                if (area(a) > 0) != (area(b) > 0):
                    issues.append({'weight': w, 'contour': ci, 'issue': 'direction'})
        if issues: bad[n] = issues
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
    fb.setupNameTable(fontbuild.name_strings(family, style, weight))
    fontbuild.setup_metrics_tables(fb, c, weight)
    fb.save(path)


def _fail(r, out_dir):
    os.makedirs(REPORT_DIR, exist_ok=True)
    json.dump(r, open(f'{REPORT_DIR}/topology_report.json', 'w'), indent=1)
    return r


def build_vf(weights, out_dir):
    M, fit = build_masters(weights)
    bad = topology_report(M, weights)
    if bad:
        return _fail(dict(ok=False, stage='contour_topology', topology_bad=bad, fit=fit), out_dir)
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
    if failed:
        return _fail(dict(ok=False, stage='harmonize', harmonize_failed=failed, fit=fit), out_dir)
    pbad = point_compat_report(harm, weights, order)
    if pbad:
        return _fail(dict(ok=False, stage='point_topology', topology_bad=pbad, fit=fit), out_dir)
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
                        return _fail(dict(ok=False, stage='cu2qu', cu2qu_failed=[n, ci, si], fit=fit), out_dir)
                    for w, sp in zip(weights, splines):
                        cols[w].append(('Q',) + tuple(tuple(p) for p in sp))
            for w in weights: quad[w][n].append(cols[w])
    uni = {n: M[weights[0]][1][n]['uni'] for n in names}
    os.makedirs(out_dir, exist_ok=True)
    ds = DesignSpaceDocument()
    ax = AxisDescriptor(); ax.name = 'Weight'; ax.tag = 'wght'; ax.minimum = min(weights); ax.default = K.AXIS_DEFAULT; ax.maximum = max(weights)
    ax.axisLabels = [AxisLabelDescriptor(name=K.WEIGHT_NAMES[w], userValue=w, elidable=(w == K.AXIS_DEFAULT))
                     for w in sorted(K.WEIGHT_NAMES) if w in weights]
    ds.addAxis(ax)
    for w in weights:
        adv = {'.notdef': 520}; adv.update({n: M[w][1][n]['adv'] for n in names})
        p = f'{out_dir}/master-{w}.ttf'
        style = K.WEIGHT_NAMES.get(w, f'W{w}')
        make_ttf_from_segments(p, order, adv, quad[w], M[w][0], w, K.FAMILY, style, uni)
        sd = SourceDescriptor(); sd.path = p; sd.name = f'master{w}'; sd.location = {'Weight': w}
        if w == K.AXIS_DEFAULT: sd.copyInfo = True
        ds.addSource(sd)
    for w in sorted(K.WEIGHT_NAMES):
        if w in weights:
            inst = InstanceDescriptor(); inst.familyName = K.FAMILY; inst.styleName = K.WEIGHT_NAMES[w]
            inst.name = f'instance{w}'; inst.location = {'Weight': w}
            ds.addInstance(inst)
    dsp = f'{out_dir}/Stackra.designspace'; ds.write(dsp)
    vf, _, _ = varLib.build(dsp)
    from fontTools.otlLib.builder import buildStatTable      # full STAT: axis values + elided fallback (item 58)
    buildStatTable(vf, [dict(tag='wght', name='Weight', ordering=0,
                             values=[dict(value=w, name=K.WEIGHT_NAMES[w], flags=(0x2 if w == K.AXIS_DEFAULT else 0))
                                     for w in sorted(K.WEIGHT_NAMES) if w in weights])],
                   elidedFallbackName=K.WEIGHT_NAMES[K.AXIS_DEFAULT])
    vpath = f'{BASE}/fonts/variable/StackraSans-VF.ttf'
    os.makedirs(os.path.dirname(vpath), exist_ok=True)
    vf.save(vpath)
    os.makedirs(REPORT_DIR, exist_ok=True)
    json.dump(dict(ok=True, stage='done', weights=list(weights), fit=fit, topology_bad={}), open(f'{REPORT_DIR}/topology_report.json', 'w'), indent=1)
    return dict(ok=True, topology_bad=bad, fit=fit, path=vpath, weights=weights)


if __name__ == '__main__':
    ws = [int(x) for x in sys.argv[1:]] or list(K.MASTER_WEIGHTS)
    try:
        r = build_vf(ws, f'{BASE}/build/vf_masters')
    except fontbuild.BuildError as e:
        print('BUILD FAILED:', e, file=sys.stderr); sys.exit(2)
    print(json.dumps(r, indent=1)[:2500])
    sys.exit(0 if r.get('ok') else 1)
