"""Step 7: compile sources/*.ufo with ufo2ft and compare every glyph to the shipped TTF.
Compares coordinates, on/off-curve flags, contour ends, advance, LSB-independent composites. Layout tables
are compared separately (decompiled text). Writes reports/session1/ufo_roundtrip.json. Exit 1 on any outline mismatch."""
import os, sys, json, hashlib
from fontTools.ttLib import newTable
import ufoLib2, ufo2ft
from fontTools.ttLib import TTFont
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
def overlap_flag(font, name):
    g = font['glyf'][name]
    return tuple(bool(getattr(c,'flags',0) & 0x0400) for c in g.components) if g.isComposite() else ()
def glyph_sig(font, name):
    gs = font['glyf']; g = gs[name]
    adv = font['hmtx'][name][0]
    if g.isComposite():
        comps = [(c.glyphName, c.x, c.y, getattr(c,'flags',0) & ~0x0C00) for c in g.components]  # mask SCALED_COMPONENT_OFFSET + OVERLAP_COMPOUND (hint bit, counted separately)
        return ('comp', adv, comps)
    if g.numberOfContours == 0:
        return ('empty', adv)
    coords, ends, flags = g.getCoordinates(gs)
    return ('simple', adv, tuple(map(tuple, coords)), tuple(ends), tuple(f & 1 for f in flags))
out = {}
bad_total = 0
for style in ['Regular', 'Medium', 'SemiBold']:
    ref = TTFont(os.path.join(ROOT, 'fonts/ttf/SynthetixUI-%s.ttf' % style))
    ufo = ufoLib2.Font.open(os.path.join(ROOT, 'sources/SynthetixUI-%s.ufo' % style))
    try:
        new = ufo2ft.compileTTF(ufo, removeOverlaps=False, flattenComponents=False, reverseDirection=False, inplace=False)
        for tag in ('GDEF', 'GSUB', 'GPOS'):   # graft the raw layout snapshots (see tools/ttf_to_ufo.py)
            t = newTable(tag); t.data = open(os.path.join(ROOT, 'sources/layout/%s/%s.bin' % (style, tag)), 'rb').read(); new[tag] = t
    except Exception as e:
        out[style] = {'compile_error': repr(e)[:300]}; bad_total += 1; continue
    names = ref.getGlyphOrder()
    missing = [n for n in names if n not in new.getGlyphOrder()]
    order_same = ref.getGlyphOrder() == new.getGlyphOrder()
    mism = {'advance': [], 'outline': [], 'kind': []}
    for n in names:
        if n in missing: continue
        a, b = glyph_sig(ref, n), glyph_sig(new, n)
        if a == b:
            if overlap_flag(ref, n) != overlap_flag(new, n): mism.setdefault('overlap_flag_only', []).append(n)
            continue
        if a[0] != b[0]: mism['kind'].append(n)
        elif a[1] != b[1]: mism['advance'].append(n)
        else: mism['outline'].append(n)
    out[style] = dict(glyphs=len(names), glyph_order_identical=order_same, missing=missing,
                      identical=len(names) - len(missing) - sum(len(v) for k, v in mism.items() if k != 'overlap_flag_only'),
                      advance_mismatch=mism['advance'][:40], outline_mismatch=mism['outline'][:40], kind_mismatch=mism['kind'][:40],
                      n_advance=len(mism['advance']), n_outline=len(mism['outline']), n_kind=len(mism['kind']), n_overlap_flag_only=len(mism.get('overlap_flag_only', [])),
                      upm=(ref['head'].unitsPerEm, new['head'].unitsPerEm),
                      layout_bytes_identical={t: bool(ref.reader[t] == new[t].data) for t in ('GDEF', 'GSUB', 'GPOS')},
                      tables_missing_vs_shipped=sorted(set(ref.keys()) - set(new.keys()) - {'GlyphOrder'}),
                      tables_extra_vs_shipped=sorted(set(new.keys()) - set(ref.keys()) - {'GlyphOrder'}))
    bad_total += len(missing) + sum(len(v) for k, v in mism.items() if k != 'overlap_flag_only')
    print(style, {k: v for k, v in out[style].items() if k not in ('advance_mismatch','outline_mismatch','kind_mismatch','missing')})
os.makedirs(os.path.join(ROOT, 'reports/session1'), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, 'reports/session1/ufo_roundtrip.json'), 'w'), indent=1)
sys.exit(1 if bad_total else 0)
