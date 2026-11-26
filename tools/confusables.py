"""Confusables test (plan Stage 10): Il1, O0 and rn vs m at 12/13/14 px, three weights, DPR 1 and 2.
Metric: Jaccard overlap of the two ink masks (luma < 160) rendered at the same origin/baseline. Pre-registered threshold: a pair is
'distinct' if Jaccard <= 0.65 at every size/weight/DPR. Numbers only: the human review at real device sizes is still required."""
import os, io, json, itertools, tempfile
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
THRESH = 0.65
PAIRS = [('I', 'l'), ('I', '1'), ('l', '1'), ('O', '0'), ('rn', 'm'), ('cl', 'd'), ('vv', 'w')]   # cl~d and vv~w added in the V4.0.10 fix pass
CHARS = sorted({c for p in PAIRS for c in p})
def run():
    css = open(os.path.join(ROOT, 'css/synthetix-ui.css')).read().replace('../fonts', 'file://' + os.path.join(ROOT, 'fonts'))
    res = {}; worst = {}; FS = {'default': '', 'ss13+zero': 'font-feature-settings:"ss13","zero";'}
    with sync_playwright() as p:
        b = p.chromium.launch(args=['--font-render-hinting=none', '--enable-font-subpixel-positioning'])
        for dpr in (1, 2):
            ctx = b.new_context(device_scale_factor=dpr, viewport={'width': 600, 'height': 200}); pg = ctx.new_page()
            for fsname, fsval in FS.items():
              for size in (12, 13, 14):
                for wt in (400, 500, 600):
                    html = '<!doctype html><meta charset=utf-8><style>%s body{margin:0;background:#fff}div{position:absolute;left:10px;top:10px;font-family:"Synthetix UI";font-weight:%d;font-size:%dpx;line-height:30px;color:#000;white-space:pre;%s}</style>' % (css, wt, size, fsval)
                    imgs = {}
                    for ch in CHARS:
                        d = tempfile.mkdtemp(); path = os.path.join(d, 't.html'); open(path, 'w').write(html + '<div id=a>%s</div>' % ch)
                        pg.goto('file://' + path); pg.evaluate("document.fonts.ready.then(()=>1)"); pg.wait_for_timeout(60)
                        im = np.asarray(Image.open(io.BytesIO(pg.screenshot(clip={'x': 0, 'y': 0, 'width': 120, 'height': 60}))).convert('L')); imgs[ch] = im < 160
                    for a, c in PAIRS:
                        A, C = imgs[a], imgs[c]; j = float((A & C).sum() / max(1, (A | C).sum()))
                        k = '%s | %s~%s' % (fsname, a, c); res.setdefault(k, {})['%dpx w%d dpr%d' % (size, wt, dpr)] = round(j, 3); worst[k] = max(worst.get(k, 0), j)
            ctx.close()
        b.close()
    out = dict(metric='Jaccard of ink masks', threshold=THRESH, worst_case={k: round(v, 3) for k, v in worst.items()}, distinct={k: bool(v <= THRESH) for k, v in worst.items()}, detail=res,
               note='Fail means visually near-identical at that size by this metric; it is evidence for the identity/quality review, not a verdict on legibility in context (word shape, context and surrounding letters also disambiguate).')
    json.dump(out, open(os.path.join(ROOT, 'reports/confusables.json'), 'w'), indent=1)
    print('worst-case Jaccard:', out['worst_case'], '| distinct:', out['distinct'])
if __name__ == '__main__': run()
