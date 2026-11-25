"""Confusable-pair similarity (Jaccard of ink bitmaps at 12/14/16 px; lower = more distinct).
Registered maxima @14px live in contract.CONFUSABLE_MAX_14PX (I/l<=0.60, l/1<=0.30, O/0<=0.45, rn/m<=0.40, cl/d<=0.45).
Needs fonts/proto/Stackra-<dir>-400.ttf  (python fontbuild.py A 400).

V6: the registered pairs are now GATED (exit code 1 when any exceeds its maximum) and the report states which
layout engine rendered the bitmaps.  This is a bitmap-overlap proxy, not a human legibility test (plan item 41/81)."""
import os, sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, features
import buildenv
import contract as K

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PAIRS = [('I', 'l'), ('l', '1'), ('I', '1'), ('O', '0'), ('B', '8'), ('S', '5'), ('rn', 'm'), ('cl', 'd'), ('vv', 'w'), ('G', 'C'), ('A', '4')]
ENGINE = ImageFont.Layout.RAQM if features.check('raqm') else ImageFont.Layout.BASIC


def bmp(path, txt, px, ss=4):
    f = ImageFont.truetype(path, px * ss, layout_engine=ENGINE)
    img = Image.new('L', (px * ss * 4, px * ss * 2), 0); d = ImageDraw.Draw(img)
    d.text((px * ss // 2, px * ss // 4), txt, font=f, fill=255)
    img = img.resize((px * 4, px * 2), Image.LANCZOS)
    a = np.array(img) > 110
    ys, xs = np.where(a)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def jacc(a, b):
    h = max(a.shape[0], b.shape[0]); w = max(a.shape[1], b.shape[1])
    A = np.zeros((h, w), bool); B = np.zeros((h, w), bool)
    A[h - a.shape[0]:, :a.shape[1]] = a; B[h - b.shape[0]:, :b.shape[1]] = b   # baseline/left aligned
    return (A & B).sum() / max((A | B).sum(), 1)


def run(path, sizes=(12, 14, 16)):
    return {''.join(p): {s: round(float(jacc(bmp(path, p[0], s), bmp(path, p[1], s))), 3) for s in sizes} for p in PAIRS}


if __name__ == '__main__':
    out = {d: run(f'{BASE}/fonts/proto/Stackra-{d}-400.ttf') for d in sys.argv[1:]}
    os.makedirs(f'{BASE}/reports/qa', exist_ok=True)
    gate = {}
    for d, res in out.items():
        for pair, limit in K.CONFUSABLE_MAX_14PX.items():
            gate[f'{d}:{pair}'] = {'value': res[pair][14], 'max': limit, 'pass': res[pair][14] <= limit}
    json.dump({'engine': 'raqm' if ENGINE == ImageFont.Layout.RAQM else 'basic (RAQM unavailable)', 'results': out, 'gate': gate},
              open(f'{BASE}/reports/qa/confusables_proto.json', 'w'), indent=1)
    print('layout engine:', 'raqm' if ENGINE == ImageFont.Layout.RAQM else 'basic')
    print('pair   ' + '  '.join(f'{d}@14' for d in out))
    for p in PAIRS:
        k = ''.join(p); print(f'{k:6s} ' + '   '.join(f"{out[d][k][14]:.2f}" for d in out))
    print('mean@14', {d: round(sum(out[d][k][14] for k in out[d]) / len(out[d]), 3) for d in out})
    bad = {k: v for k, v in gate.items() if not v['pass']}
    for k, v in bad.items(): print(f'GATE FAIL {k}: {v["value"]} > {v["max"]}')
    sys.exit(1 if bad else 0)
