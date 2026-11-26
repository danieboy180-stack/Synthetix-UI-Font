"""Regression ledger: every V3 glyph vs V4 (all three masters). Existing outlines/advances must be unchanged,
except the explicitly re-centred .tf figure set (advance equalised). Fails (exit 1) on any other difference."""
import sys, os, json
from fontTools.ttLib import TTFont
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TF = {d + '.tf' for d in 'zero one two three four five six seven eight nine'.split()} | {o + '.tf' for o in 'plus minus multiply divide equal greater less'.split()}
def coords(f, g):
    gl = f['glyf'][g]
    if gl.isComposite(): return ('C', tuple((c.glyphName, c.x, c.y, c.flags) for c in gl.components))
    c = gl.coordinates if gl.numberOfContours else []
    return ('S', tuple((int(x), int(y)) for x, y in c), tuple(gl.endPtsOfContours) if gl.numberOfContours else (), tuple(gl.flags) if gl.numberOfContours else ())
def run():
    ledger = {}; bad = 0
    for style in ('Regular', 'Medium', 'SemiBold'):
        a = TTFont(os.path.join(ROOT, 'baseline/v3/SynthetixUI-%s.ttf' % style)); b = TTFont(os.path.join(ROOT, 'fonts/ttf/SynthetixUI-%s.ttf' % style))
        diffs = []; maxdx_tf = 0
        for g in a.getGlyphOrder():
            adv_a, adv_b = a['hmtx'][g][0], b['hmtx'][g][0]
            ca, cb = coords(a, g), coords(b, g)
            if g in TF:
                if ca[0] == 'S':
                    # allowed: a pure x translation (all points identical dx, dy=0), same contour structure, advance == master's
                    # tabular width, ink fits inside the advance with >=10 units of sidebearing on both sides
                    dxs = {bx - ax for (ax, ay), (bx, by) in zip(ca[1], cb[1])}; dys = {by - ay for (ax, ay), (bx, by) in zip(ca[1], cb[1])}
                    xs = [x for x, _ in cb[1]]; lsb, rsb = min(xs), adv_b - max(xs)
                    tab = b['hmtx']['one.tf'][0]
                    ok = len(dxs) <= 1 and dys <= {0} and ca[2:] == cb[2:] and adv_b == tab and min(lsb, rsb) >= 10
                    maxdx_tf = max(maxdx_tf, abs(adv_b - adv_a))
                    if not ok: diffs.append((g, 'tf-change-not-pure-recentre', adv_a, adv_b, lsb, rsb))
                continue
            if ca != cb or adv_a != adv_b or a['hmtx'][g][1] != b['hmtx'][g][1]:
                diffs.append((g, 'outline/advance changed', adv_a, adv_b))
        ledger[style] = dict(v3_glyphs=len(a.getGlyphOrder()), v4_glyphs=len(b.getGlyphOrder()), added=len(b.getGlyphOrder()) - len(a.getGlyphOrder()),
                             unchanged_glyphs=len(a.getGlyphOrder()) - len(diffs) - len(TF), recentred_tf=len(TF), max_tf_advance_delta=maxdx_tf, violations=diffs)
        bad += len(diffs)
        # order preserved (existing glyph ids stable)
        ledger[style]['glyph_ids_stable'] = a.getGlyphOrder() == b.getGlyphOrder()[:len(a.getGlyphOrder())]
        if not ledger[style]['glyph_ids_stable']: bad += 1
    json.dump(ledger, open(os.path.join(ROOT, 'reports/regression_ledger.json'), 'w'), indent=1)
    for k, v in ledger.items(): print(k, {x: v[x] for x in v if x != 'violations'}, 'violations:', len(v['violations']))
    return bad
if __name__ == '__main__': sys.exit(1 if run() else 0)
