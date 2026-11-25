"""Dense interpolation gate (98/100 plan items 54, 55).

Samples the wght axis every contract.DENSE_AXIS_STEP units, instantiates the shipped VF at each sample and compares
every glyph with a DIRECT build of the same weight:  signed-area deviation, bounding-box deviation, advance deviation.
Thresholds come from contract.py (registered; never relaxed after a failed result).
Exit code 1 if any glyph at any sample exceeds a threshold.  Writes reports/qa/interp_dense.json."""
import os, sys, json
import buildenv
import contract as K
import fontbuild, geom
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.boundsPen import BoundsPen

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def direct_metrics(g):
    cs = g['contours']
    if not cs: return 0.0, None
    a = sum(geom.area(c) for c in cs)
    return abs(a), geom.bbox(cs)


def run(vf_path=None, step=K.DENSE_AXIS_STEP, lo=None, hi=None, verbose=True):
    vf_path = vf_path or f'{BASE}/fonts/variable/StackraSans-VF.ttf'
    vf0 = TTFont(vf_path)
    axis = vf0['fvar'].axes[0]
    lo = int(axis.minValue) if lo is None else lo; hi = int(axis.maxValue) if hi is None else hi
    results = {}; failures = []
    for w in range(lo, hi + 1, step):
        inst = instancer.instantiateVariableFont(TTFont(vf_path), {'wght': w}, inplace=False)
        gs = inst.getGlyphSet(); hmtx = inst['hmtx']
        c, g, _ = fontbuild.make_master('A', w, strict=False)
        worst = {'area': (0.0, None), 'bbox': (0.0, None), 'adv': (0.0, None)}
        for n, gd in g.items():
            if n == '.notdef' or not gd['contours']: continue
            area_d, bb_d = direct_metrics(gd)
            ap = AreaPen(gs); gs[n].draw(ap); area_v = abs(ap.value)
            bp = BoundsPen(gs); gs[n].draw(bp); bb_v = bp.bounds
            da = abs(area_v - area_d) / max(area_d, 1)
            db = max(abs(a - b) for a, b in zip(bb_v, bb_d)) if bb_v else 999
            dv = abs(hmtx[n][0] - gd['adv'])
            for key, val in (('area', da), ('bbox', db), ('adv', dv)):
                if val > worst[key][0]: worst[key] = (val, n)
            if da > K.INTERP_AREA_MAX or db > K.INTERP_BBOX_MAX_UNITS or dv > K.INTERP_ADVANCE_MAX_UNITS:
                failures.append({'wght': w, 'glyph': n, 'area_dev': round(da, 4), 'bbox_dev': round(db, 2), 'adv_dev': dv})
        results[w] = {k: (round(v[0], 4), v[1]) for k, v in worst.items()}
        if verbose:
            print(f'wght {w}: worst area {results[w]["area"]}, bbox {results[w]["bbox"]}, advance {results[w]["adv"]}')
    os.makedirs(f'{BASE}/reports/qa', exist_ok=True)
    out = {'step': step, 'thresholds': {'area': K.INTERP_AREA_MAX, 'bbox_units': K.INTERP_BBOX_MAX_UNITS,
                                         'advance_units': K.INTERP_ADVANCE_MAX_UNITS},
           'samples': results, 'failures': failures, 'pass': not failures}
    json.dump(out, open(f'{BASE}/reports/qa/interp_dense.json', 'w'), indent=1)
    return out


if __name__ == '__main__':
    out = run()
    print('interpolation gate:', 'PASS' if out['pass'] else f'FAIL ({len(out["failures"])} glyph/weight failures)')
    for f in out['failures'][:40]: print('  ', f)
    sys.exit(0 if out['pass'] else 1)
