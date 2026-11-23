"""Interpolation test: variable-font instances vs directly built weights (outline bounds / signed area / advance).
Registered tolerance (PROCEDURE_REVIEW s6): intermediates area <= 2 %, bbox <= 2 units."""
import os, json
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.areaPen import AreaPen
import fontbuild

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
VF = f'{BASE}/fonts/variable/StackraSans-VF.ttf'
os.makedirs(f'{BASE}/fonts/proto', exist_ok=True)


def stats(font, n):
    gs = font.getGlyphSet(); bp = BoundsPen(gs); ap = AreaPen(gs); gs[n].draw(bp); gs[n].draw(ap)
    return bp.bounds, abs(ap.value), gs[n].width


out = {}
for w in (300, 350, 400, 450, 500):
    inst = instancer.instantiateVariableFont(TTFont(VF), {'wght': w}, inplace=False)
    c, gl, log = fontbuild.make_master('A', w)
    p = f'{BASE}/fonts/proto/direct-{w}.ttf'; fontbuild.build_ttf(p, gl, c, family='Direct', style=str(w), weight=w)
    d = TTFont(p); worst_b = (0, ''); worst_a = (0, ''); worst_adv = (0, '')
    for n in gl:
        if not gl[n]['contours']: continue
        (b1, a1, w1), (b2, a2, w2) = stats(inst, n), stats(d, n)
        if b1 is None or b2 is None: continue
        db = max(abs(x - y) for x, y in zip(b1, b2)); da = abs(a1 - a2) / max(a2, 1); dw = abs(w1 - w2)
        if db > worst_b[0]: worst_b = (round(db, 1), n)
        if da > worst_a[0]: worst_a = (round(da, 4), n)
        if dw > worst_adv[0]: worst_adv = (dw, n)
    out[w] = {'max_bbox_dev_units': worst_b, 'max_area_rel_dev': worst_a, 'max_advance_dev': worst_adv}
os.makedirs(f'{BASE}/reports/qa', exist_ok=True)
json.dump(out, open(f'{BASE}/reports/qa/interp_vs_direct.json', 'w'), indent=1)
for w, v in out.items(): print(w, v)
