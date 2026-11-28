"""Phase B steps 16-17: per-glyph reference bitmaps from the pangram crops.
 * glyphs = connected components (merged by x-overlap) found by tools/measure_captures.py
 * every bitmap is aligned on its line's baseline and normalised so cap height = CAP_N px (cap = 1.0)
 * frame: baseline - 1.30 cap  ..  baseline + 0.40 cap (fixed for all glyphs), x: ink box +- 0.06 cap
 * files: reference/glyphs/u<HEX>_s<capPx>_<occurrence>.png (8-bit coverage, 255 = ink), reference/glyphs/index.json, overlay_<sheet>.png for manual QA
NOT traced: these are raster crops of a measurement capture, used only to compute IoU/XOR against rendered Synthetix glyphs.
Outlines are never derived from them (CONTRACT_98 originality rule)."""
import os, sys, json
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
import measure_captures as mc
ROOT = mc.ROOT
CAP_N = 128
OUT = os.path.join(ROOT, 'reference/glyphs'); os.makedirs(OUT, exist_ok=True)
caps = json.load(open(os.path.join(ROOT, 'reference/captures/captures.json')))['captures']
index = []
occ = {}
for cap in caps:
    sh = mc.measure_sheet(cap)
    cov = mc.load(os.path.join(ROOT, cap['file']))
    cap_px = sh['vertical']['cap_px']; per_line = sh['vertical']['per_line']
    ov = Image.fromarray((255 - cov * 255).astype(np.uint8), 'L').convert('RGB'); dr = ImageDraw.Draw(ov)
    # baseline per line: flat-letter baseline, else digits 1 2 4 7 / dots
    base = {}
    for li in {g['line'] for g in sh['glyphs']}:
        if li in per_line: base[li] = per_line[li]['baseline']
        else:
            v = [g['bottom'] for g in sh['glyphs'] if g['line'] == li and g['ch'] in '1247.!:' and not g['tick2']]
            if v: base[li] = float(np.median(v))
    for g in sh['glyphs']:
        li = g['line']
        if li not in base or g['tick2']: continue
        b = base[li]; top = b - 1.30 * cap_px; bot = b + 0.40 * cap_px
        gbox = list(g['ibox']); left, right = g['left'], g['right']
        if g['ch'] == '"':                                            # the double quote = two ticks: keep both in one bitmap
            t2 = [h for h in sh['glyphs'] if h['line'] == li and h['tick2']]
            t2 = [h for h in t2 if h['left'] >= g['right'] - 1]
            if t2:
                h = min(t2, key=lambda z: z['left']); gbox[1] = max(gbox[1], h['ibox'][1]); gbox[2] = min(gbox[2], h['ibox'][2]); gbox[3] = max(gbox[3], h['ibox'][3]); right = h['right']
        x0 = left - 0.06 * cap_px; x1 = right + 0.06 * cap_px
        own = np.zeros_like(cov); P = 2                               # mask: only this glyph's own ink (no neighbour slivers)
        own[max(gbox[2] - P, 0):gbox[3] + P + 1, max(gbox[0] - P, 0):gbox[1] + P + 1] = cov[max(gbox[2] - P, 0):gbox[3] + P + 1, max(gbox[0] - P, 0):gbox[1] + P + 1]
        im = Image.fromarray((own * 255).astype(np.uint8), 'L')
        s = CAP_N / cap_px
        crop = im.crop((x0, top, x1, bot)).resize((max(int(round((x1 - x0) * s)), 1), int(round((bot - top) * s))), Image.LANCZOS)
        ch = g['ch']; k = occ[(ch, cap['id'])] = occ.get((ch, cap['id']), 0) + 1; name = 'u%04X_s%d_%d.png' % (ord(ch), round(cap_px), k)
        crop.save(os.path.join(OUT, name), optimize=True)
        index.append(dict(file='reference/glyphs/' + name, ch=ch, codepoint='U+%04X' % ord(ch), sheet=cap['id'], cap_px=cap_px, line=li,
                          baseline_row=int(round(1.30 * CAP_N)), cap_row=int(round(0.30 * CAP_N)), frame_h=crop.size[1], frame_w=crop.size[0],
                          ink_w_over_cap=(right - left) / cap_px, ink_h_over_cap=g['h'] / cap_px, left_over_cap=(g['left'] - x0) / cap_px))
        dr.rectangle([g['left'], g['top'], g['right'], g['bottom']], outline=(220, 0, 0), width=1)
    for li, b in base.items(): dr.line([(0, b), (cov.shape[1], b)], fill=(0, 120, 255), width=1)
    ov.save(os.path.join(OUT, 'overlay_%s.png' % cap['id']), optimize=True)
json.dump(dict(cap_normalised_to_px=CAP_N, note='bitmaps are measurement crops; never traced', glyphs=index), open(os.path.join(OUT, 'index.json'), 'w'), indent=0, ensure_ascii=False)
chars = sorted({i['ch'] for i in index})
print('bitmaps', len(index), 'distinct characters', len(chars), '| sizes', sorted({round(i['cap_px']) for i in index}))
need = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!?%&@#$()/-:;,.'")
print('missing chars:', ''.join(sorted(need - set(chars))) or 'none')
