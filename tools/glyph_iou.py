"""Phase B steps 21-23 (PROVISIONAL method, see reports/AMENDMENTS.md proposal D): per-glyph shape IoU of a font vs the reference bitmaps.
Alignment (fixed before looking at results): vertical = baseline row; horizontal = ink-left edge (so sidebearings are NOT scored here;
widths are scored by the width gate). Both masks thresholded at 50% coverage, cap normalised to 128 px (cap = 1.0).
IoU = |ref AND font| / |ref OR font|. Per glyph = mean over the occurrences/sizes in reference/glyphs/index.json.
Also writes XOR heatmaps (red = font has ink the reference lacks, blue = reference ink the font lacks) to reports/diffs/.
usage: python tools/glyph_iou.py [font.ttf]    -> reports/session1/glyph_iou.json, reports/diffs/<codepoint>.png, reports/diffs/RANKING.md"""
import os, sys, json
import numpy as np
from PIL import Image, ImageFont, ImageDraw
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
FONT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'fonts/ttf/SynthetixUI-Regular.ttf')
idx = json.load(open(os.path.join(ROOT, 'reference/glyphs/index.json')))
CAP_N = idx['cap_normalised_to_px']; EM = CAP_N / 0.70
font = ImageFont.truetype(FONT, size=EM, layout_engine=ImageFont.Layout.BASIC)

def render(ch, shape, ref_left, base_row):
    H, W = shape
    im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
    d.text((ref_left, base_row), ch, font=font, fill=255, anchor='ls')
    a = np.array(im).astype(float) / 255
    ys, xs = np.where(a >= 0.5)
    if len(xs) == 0: return a
    shift = ref_left - xs.min()                       # align ink-left edges
    im2 = Image.new('L', (W, H), 0); ImageDraw.Draw(im2).text((ref_left + shift, base_row), ch, font=font, fill=255, anchor='ls')
    return np.array(im2).astype(float) / 255

rows = {}; heat_done = set()
os.makedirs(os.path.join(ROOT, 'reports/diffs'), exist_ok=True)
for it in idx['glyphs']:
    ref = np.array(Image.open(os.path.join(ROOT, it['file'])).convert('L')).astype(float) / 255
    ys, xs = np.where(ref >= 0.5)
    if len(xs) == 0: continue
    fnt = render(it['ch'], ref.shape, int(xs.min()), it['baseline_row'])
    A, B = ref >= 0.5, fnt >= 0.5
    iou = (A & B).sum() / max((A | B).sum(), 1)
    best = iou                                                         # secondary bound: best horizontal shift (+-0.10 cap), never vertical
    for sh in range(-13, 14):
        Bs = np.roll(B, sh, axis=1)
        if sh > 0: Bs[:, :sh] = False
        elif sh < 0: Bs[:, sh:] = False
        best = max(best, (A & Bs).sum() / max((A | Bs).sum(), 1))
    rows.setdefault(it['ch'], []).append(dict(iou=float(iou), iou_shift=float(best), sheet=it['sheet'], file=it['file'], extra=float((B & ~A).sum() / max(A.sum(), 1)), missing=float((A & ~B).sum() / max(A.sum(), 1))))
    if it['sheet'] == 'B' and it['ch'] not in heat_done:
        heat_done.add(it['ch'])
        heat = np.full(ref.shape + (3,), 255, np.uint8); heat[A & B] = (60, 60, 60); heat[B & ~A] = (230, 40, 40); heat[A & ~B] = (40, 90, 235)
        Image.fromarray(heat).save(os.path.join(ROOT, 'reports/diffs/u%04X.png' % ord(it['ch'])), optimize=True)
res = {ch: dict(iou_mean=float(np.mean([r['iou'] for r in v])), iou_best_shift_mean=float(np.mean([r['iou_shift'] for r in v])), iou_min=float(np.min([r['iou'] for r in v])), n=len(v),
                extra_ink=float(np.mean([r['extra'] for r in v])), missing_ink=float(np.mean([r['missing'] for r in v]))) for ch, v in rows.items()}
letters = [c for c in res if c.isalpha()]
lv = np.array([res[c]['iou_mean'] for c in letters]); av = np.array([r['iou_mean'] for r in res.values()])
lvs = np.array([res[c]['iou_best_shift_mean'] for c in letters])
summary = dict(font=os.path.relpath(FONT, ROOT), method='provisional: baseline + ink-left alignment, 50% threshold, cap=128px',
               letters=dict(n=len(lv), median=float(np.median(lv)), min=float(lv.min()), below_0_88=int((lv < .88).sum()), below_0_85=int((lv < .85).sum()), best_shift_median=float(np.median(lvs)), best_shift_below_0_88=int((lvs < .88).sum())),
               all_glyphs=dict(n=len(av), median=float(np.median(av)), below_0_88=int((av < .88).sum())))
json.dump(dict(summary=summary, glyphs=res), open(os.path.join(ROOT, 'reports/session1/glyph_iou.json'), 'w'), indent=1)
rank = sorted(res.items(), key=lambda kv: kv[1]['iou_mean'])
with open(os.path.join(ROOT, 'reports/diffs/RANKING.md'), 'w') as f:
    f.write('# Glyph IoU ranking (PROVISIONAL method, lowest first)\n\nheatmaps: red = extra ink in Synthetix, blue = ink missing vs reference, file reports/diffs/u<HEX>.png (sheet B, cap 49 px)\n\n| rank | glyph | IoU (ink-left) | IoU best-shift | IoU min | extra ink | missing ink |\n|---|---|---|---|---|---|---|\n')
    for i, (c, v) in enumerate(rank, 1):
        f.write('| %d | `%s` U+%04X | %.3f | %.3f | %.3f | %.3f | %.3f |\n' % (i, c, ord(c), v['iou_mean'], v['iou_best_shift_mean'], v['iou_min'], v['extra_ink'], v['missing_ink']))
print(json.dumps(summary, indent=1)); print('worst 12:', [(c, round(v['iou_mean'], 2)) for c, v in rank[:12]])
