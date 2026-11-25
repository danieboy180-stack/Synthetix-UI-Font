"""Hard QA gates for every shipped font (98/100 plan items 27, 28, 61, 62, 75, 77).

Each gate returns (passed, detail).  Writes reports/qa/qa_gates.json.  Exit code 1 if any gate fails.
Gates here prove FILE INTEGRITY.  They do not prove design quality, language correctness or legal status:
those are tracked in RELEASE_READINESS.md and need measurements / people this script cannot supply."""
import os, sys, json, glob
import buildenv
import contract as K
import glyphset
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.basePen import decomposeQuadraticSegment
from fontTools.pens.boundsPen import BoundsPen, ControlBoundsPen
from fontTools.varLib import instancer

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
REQUIRED_TABLES = {'cmap', 'glyf', 'loca', 'head', 'hhea', 'hmtx', 'maxp', 'name', 'OS/2', 'post', 'gasp'}
VF_TABLES = {'fvar', 'gvar', 'STAT', 'HVAR'}


def polylines(gs, name, n=12):
    pen = RecordingPen(); gs[name].draw(pen)
    out = []; cur = []
    for op, args in pen.value:
        if op == 'moveTo': cur = [args[0]]
        elif op == 'lineTo': cur.append(args[0])
        elif op == 'qCurveTo':
            p0 = cur[-1]
            if args[-1] is None: args = args[:-1]
            for (c, e) in decomposeQuadraticSegment(args):
                for i in range(1, n + 1):
                    t = i / n; u = 1 - t
                    cur.append((u * u * p0[0] + 2 * u * t * c[0] + t * t * e[0], u * u * p0[1] + 2 * u * t * c[1] + t * t * e[1]))
                p0 = e
        elif op in ('closePath', 'endPath'):
            if len(cur) > 2 and cur[0] == cur[-1]: cur = cur[:-1]
            if cur: out.append(cur)
            cur = []
    return out


def area(p):
    return sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p))) / 2


def inside(pt, poly):
    x, y = pt; c = False
    for i in range(len(poly)):
        x0, y0 = poly[i]; x1, y1 = poly[(i + 1) % len(poly)]
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0: c = not c
    return c


def _o(a, b, c): return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def crosses(a, b, c, d, eps=1e-6):
    o1, o2, o3, o4 = _o(a, b, c), _o(a, b, d), _o(c, d, a), _o(c, d, b)
    return (o1 * o2 < -eps) and (o3 * o4 < -eps)


def crossing_pair(P, Q, same):
    for i in range(len(P)):
        a, b = P[i], P[(i + 1) % len(P)]
        for j in range(len(Q)):
            if same and (j == i or (j + 1) % len(Q) == i or (i + 1) % len(P) == j): continue
            c, d = Q[j], Q[(j + 1) % len(Q)]
            if crosses(a, b, c, d): return (i, j)
    return None


def check_outlines(font, label):
    gs = font.getGlyphSet(); fails = []
    for name in font.getGlyphOrder():
        if name == '.notdef': continue
        polys = polylines(gs, name)
        if not polys:
            if name != 'space': fails.append((name, 'no outline'))
            continue
        for ci, p in enumerate(polys):
            if abs(area(p)) < K.MIN_CONTOUR_AREA: fails.append((name, f'contour {ci}: area {abs(area(p)):.0f} < {K.MIN_CONTOUR_AREA}'))
            if any(abs(y) > K.MAX_ABS_Y_UNITS for _, y in p): fails.append((name, f'contour {ci}: |y| > {K.MAX_ABS_Y_UNITS}'))
            depth = sum(1 for cj, q in enumerate(polys) if cj != ci and inside(p[0], q))
            want_cw = depth % 2 == 0           # TrueType: outer clockwise (negative area), holes counter-clockwise
            if (area(p) < 0) != want_cw: fails.append((name, f'contour {ci}: wrong winding for nesting depth {depth}'))
            if crossing_pair(p, p, True): fails.append((name, f'contour {ci}: self-intersection'))
        for i in range(len(polys)):
            for j in range(i + 1, len(polys)):
                if crossing_pair(polys[i], polys[j], False): fails.append((name, f'contours {i}/{j} intersect'))
        bp, cp = BoundsPen(gs), ControlBoundsPen(gs)
        gs[name].draw(bp); gs[name].draw(cp)
        if bp.bounds and cp.bounds:
            over = max(abs(a - b) for a, b in zip(bp.bounds, cp.bounds))
            if over > K.MISSING_EXTREMA_TOLERANCE: fails.append((name, f'missing extrema: control box exceeds true bounds by {over:.1f}'))
    return not fails, fails[:20]


def check_cmap(font):
    cm = font.getBestCmap(); fails = []
    for name, uni, *_ in glyphset.R:
        if uni and cm.get(uni) != name: fails.append(f'U+{uni:04X} -> {cm.get(uni)} (want {name})')
    fails += [f'U+{u:04X} maps to .notdef' for u, n in cm.items() if n == '.notdef']
    return not fails, fails[:20]


def check_tables(font, is_vf):
    need = REQUIRED_TABLES | (VF_TABLES if is_vf else set())
    miss = sorted(need - set(font.keys()))
    return not miss, miss


def check_metrics(font, all_bounds):
    m = K.VMETRICS; o = font['OS/2']; h = font['hhea']; fails = []
    if (h.ascent, h.descent, h.lineGap) != (m['ascender'], m['descender'], m['line_gap']): fails.append('hhea differs from contract')
    if (o.sTypoAscender, o.sTypoDescender, o.sTypoLineGap) != (m['typo_ascender'], m['typo_descender'], m['typo_line_gap']): fails.append('typo metrics differ from contract')
    if (h.ascent, h.descent, h.lineGap) != (o.sTypoAscender, o.sTypoDescender, o.sTypoLineGap): fails.append('hhea != typo')
    if not (o.fsSelection & (1 << 7)): fails.append('USE_TYPO_METRICS not set')
    if o.version < 4: fails.append(f'OS/2 version {o.version} < 4')
    ymax, ymin = all_bounds
    if o.usWinAscent < ymax: fails.append(f'usWinAscent {o.usWinAscent} < glyph yMax {ymax}')
    if o.usWinDescent < -ymin: fails.append(f'usWinDescent {o.usWinDescent} < glyph |yMin| {-ymin}')
    gl = font['glyf']; hm = font['hmtx']
    for n in font.getGlyphOrder():
        g = gl[n]; adv, lsb = hm[n]
        if g.numberOfContours:
            g.recalcBounds(gl)
            if lsb != g.xMin: fails.append(f'{n}: lsb {lsb} != xMin {g.xMin}')
            if not (K.ADVANCE_RANGE[0] <= adv <= K.ADVANCE_RANGE[1]) and n != '.notdef': fails.append(f'{n}: advance {adv} outside {K.ADVANCE_RANGE}')
    return not fails, fails[:20]


def glyph_bounds(font):
    gl = font['glyf']; ymax, ymin = -9999, 9999
    for n in font.getGlyphOrder():
        g = gl[n]
        if g.numberOfContours:
            g.recalcBounds(gl); ymax = max(ymax, g.yMax); ymin = min(ymin, g.yMin)
    return ymax, ymin


def check_names(font, style, is_vf):
    nm = font['name']; g = lambda i: nm.getDebugName(i); fails = []
    if g(1) is None or g(2) is None: return False, ['name IDs 1/2 missing']
    if g(2) not in ('Regular', 'Bold', 'Italic', 'Bold Italic'): fails.append(f'ID 2 is "{g(2)}" (must be a RIBBI style)')
    if style in ('Light', 'Medium', 'SemiBold') and not is_vf:
        if g(16) != K.FAMILY or g(17) != style: fails.append(f'IDs 16/17 should be "{K.FAMILY}"/"{style}", got {g(16)}/{g(17)}')
    ps = g(6) or ''
    if ' ' in ps or len(ps) > 63: fails.append(f'bad PostScript name "{ps}"')
    if not g(3): fails.append('unique ID missing')
    for i in (1, 3, 4, 5, 6):
        if any(s in (g(i) or '') for s in K.PROTO_STRINGS): fails.append(f'ID {i} contains a proto/experimental marker')
    if style == 'W400' or 'W3' in ps or 'W5' in ps: fails.append('placeholder style name (W###)')
    return not fails, fails


def check_vf(font):
    fails = []
    ax = font['fvar'].axes
    if [a.axisTag for a in ax] != ['wght']: fails.append('axis list is not exactly [wght]')
    else:
        a = ax[0]
        if (a.minValue, a.defaultValue, a.maxValue) != (min(K.MASTER_WEIGHTS), K.AXIS_DEFAULT, max(K.MASTER_WEIGHTS)):
            fails.append(f'axis range {a.minValue}/{a.defaultValue}/{a.maxValue}')
    inst = {int(i.coordinates['wght']): font['name'].getDebugName(i.subfamilyNameID) for i in font['fvar'].instances}
    want = {w: K.WEIGHT_NAMES[w] for w in K.PUBLIC_WEIGHTS}
    if inst != want: fails.append(f'named instances {inst} != {want}')
    st = font['STAT'].table
    if not st.AxisValueArray or st.AxisValueCount != len(K.PUBLIC_WEIGHTS): fails.append('STAT axis values missing/incomplete')
    return not fails, fails


def parity(vf_path, statics):
    """VF at a public weight vs the shipped static of that weight (should be identical outlines)."""
    fails = []
    for w, path in statics.items():
        inst = instancer.instantiateVariableFont(TTFont(vf_path), {'wght': w}, inplace=False)
        st = TTFont(path)
        a, b = inst.getGlyphSet(), st.getGlyphSet()
        for n in st.getGlyphOrder():
            if n == '.notdef': continue
            ba, bb = BoundsPen(a), BoundsPen(b)
            a[n].draw(ba); b[n].draw(bb)
            if (ba.bounds is None) != (bb.bounds is None): fails.append(f'{w} {n}: one side empty'); continue
            if ba.bounds and max(abs(x - y) for x, y in zip(ba.bounds, bb.bounds)) > K.MASTER_PARITY_BBOX_MAX_UNITS:
                fails.append(f'{w} {n}: bbox differs from static')
    return not fails, fails[:20]


def check_boolean_engine():
    """Independent raster check of the custom overlap-removal engine on every VF master (plan item 26).
    The V5 engine was never validated; this gate found the Y defect at wght 300 (17.8 % mismatch)."""
    import fontbuild
    worst = []
    for w in K.MASTER_WEIGHTS:
        fontbuild.make_master('A', w, strict=False, validate=True)
        for name, calls in fontbuild.BOOL_VALIDATION.items():
            for m, tot in calls:
                frac = m / max(tot, 1)
                if frac > K.BOOL_MISMATCH_MAX_FRACTION: worst.append(f'{w} {name}: {m}/{tot} = {frac:.3f}')
    return not worst, worst[:20]


def main():
    results = {}
    def gate(name, fn, *a):
        ok, detail = fn(*a); results[name] = {'pass': bool(ok), 'detail': detail}
        print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else f'  {detail[:3]}'))
    statics = {w: f'{BASE}/fonts/ttf/StackraSans-{K.WEIGHT_NAMES[w]}.ttf' for w in K.PUBLIC_WEIGHTS}
    vfp = f'{BASE}/fonts/variable/StackraSans-VF.ttf'
    missing = [p for p in list(statics.values()) + [vfp] if not os.path.exists(p)]
    if missing:
        print('QA FAILED: files missing (run varbuild.py and export_family.py):', missing, file=sys.stderr); return 2
    fonts = {f'static-{K.WEIGHT_NAMES[w]}': (TTFont(p), K.WEIGHT_NAMES[w], False) for w, p in statics.items()}
    fonts['variable'] = (TTFont(vfp), 'Regular', True)
    for label, (f, style, is_vf) in fonts.items():
        gate(f'{label}: required tables', check_tables, f, is_vf)
        gate(f'{label}: cmap complete', check_cmap, f)
        gate(f'{label}: outlines (winding, intersections, extrema, area)', check_outlines, f, label)
        gate(f'{label}: metrics coherent', check_metrics, f, glyph_bounds(f))
        gate(f'{label}: names', check_names, f, style, is_vf)
    gate('variable: axis, instances, STAT', check_vf, fonts['variable'][0])
    gate('variable vs statics at public weights', parity, vfp, statics)
    gate('boolean engine raster validation (all masters)', check_boolean_engine)
    os.makedirs(f'{BASE}/reports/qa', exist_ok=True)
    json.dump(results, open(f'{BASE}/reports/qa/qa_gates.json', 'w'), indent=1)
    bad = [k for k, v in results.items() if not v['pass']]
    print(f'{len(results) - len(bad)}/{len(results)} gates pass')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
