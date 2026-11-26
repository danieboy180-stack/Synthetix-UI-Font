"""Advance-width parity across browser engines (plan Stage 11). Run:  python tools/engine_parity.py chromium [firefox webkit]
Writes reports/engine_parity_<engine>.json; with >1 engine also prints the max cross-engine width delta (ink may differ, advances must not).
In the build sandbox only Chromium exists; CI (.github/workflows/ci.yml) runs all three."""
import sys, os, json, tempfile
from playwright.sync_api import sync_playwright
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
STR = ["Sphinx of black quartz, judge my vow.", "0123456789 ₦1,250.00 ½ ¼ ¾ x² H₂O", "Ẹ káàbọ̀ Ọ̀gbẹ́ni Ṣọlá ị́ ụ́ ɓɗƙƴ ƁƊƘƳ Ɛɛ Ɔɔ", "AVATAR To Wa Yo Te rn m"]
def widths(engine, p):
    b = getattr(p, engine).launch(); out = {}
    for fmt, files in {'ttf': 'ttf/SynthetixUI-%s.ttf', 'woff2': 'woff2/SynthetixUI-%s.woff2'}.items():
        for sty, w in (('Regular', 400), ('Medium', 500), ('SemiBold', 600)):
            for size in (12, 16, 24, 100):
                css = '@font-face{font-family:F;src:url("file://%s")}span{font-family:F;font-size:%dpx;white-space:pre;font-kerning:normal}' % (os.path.join(ROOT, 'fonts', files % sty), size)
                html = '<!doctype html><meta charset=utf-8><style>%s</style>%s' % (css, ''.join('<div><span id="s%d">%s</span></div>' % (i, s) for i, s in enumerate(STR)))
                d = tempfile.mkdtemp(); path = os.path.join(d, 't.html'); open(path, 'w').write(html)
                pg = b.new_page(); pg.goto('file://' + path); pg.evaluate("document.fonts.ready.then(()=>1)"); pg.wait_for_timeout(150)
                assert pg.evaluate("Array.from(document.fonts).every(f=>f.status==='loaded')"), (engine, fmt, sty)
                for i in range(len(STR)): out['%s %s %dpx s%d' % (fmt, sty, size, i)] = pg.evaluate("document.getElementById('s%d').getBoundingClientRect().width" % i)
                pg.close()
    b.close(); return out
if __name__ == '__main__':
    engines = sys.argv[1:] or ['chromium']; res = {}
    with sync_playwright() as p:
        for e in engines:
            res[e] = widths(e, p); json.dump(res[e], open(os.path.join(ROOT, 'reports/engine_parity_%s.json' % e), 'w'), indent=1)
    if len(engines) > 1:
        keys = res[engines[0]]; worst = max(abs(res[a][k] - res[engines[0]][k]) for a in engines[1:] for k in keys)
        print('max cross-engine advance delta (px):', worst); sys.exit(0 if worst < 0.5 else 1)
    print('engines run:', engines, '| keys', len(res[engines[0]]))
