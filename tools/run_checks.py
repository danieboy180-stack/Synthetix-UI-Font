"""run_checks.py - V4 verification suite. Writes reports/checks_v4.json. Exit code 1 if any HARD check here fails.

Honest scope: these are our own checks (fontTools + Chromium). They are NOT Font Bakery, NOT Firefox/WebKit, NOT device tests.
Gates that need those are reported by tools/contract_check.py as NOT MEASURED.
"""
import sys, os, json, io, unicodedata, itertools
import numpy as np
from PIL import Image
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from playwright.sync_api import sync_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
FD = os.path.join(ROOT, 'fonts')
STYLES = [('Regular', 400), ('Medium', 500), ('SemiBold', 600)]
DIG = 'zero one two three four five six seven eight nine'.split()
RES = {}


def rng(a, b): return list(range(a, b + 1))
SETS = {
    'latin1_A0_FF': rng(0xA0, 0xFF),
    'latin_ext_A_100_17F_minus_long_s': [c for c in rng(0x100, 0x17F) if c != 0x17F],
    'ascii': rng(0x20, 0x7E),
    'hausa_yoruba_igbo': [0x323, 0x181, 0x253, 0x18A, 0x257, 0x198, 0x199, 0x1B3, 0x1B4, 0x1EB8, 0x1EB9, 0x1ECC, 0x1ECD, 0x1E62, 0x1E63, 0x1ECA, 0x1ECB, 0x1EE4, 0x1EE5,
                          0x190, 0x25B, 0x186, 0x254, 0x14A, 0x14B, 0x1F8, 0x1F9, 0x1E3E, 0x1E3F, 0x1E44, 0x1E45, 0x2BC, 0x300, 0x301, 0x302, 0x303, 0x304, 0x306, 0x307, 0x308, 0x30C],
    'ui_symbols_tier3': [0x2713, 0x2116, 0xB1, 0xD7, 0xF7, 0x2260, 0x2264, 0x2265, 0x2248, 0x2212, 0x221E, 0xBD, 0xBC, 0xBE, 0x20B5, 0x20B9, 0x20A6, 0x2190, 0x2191, 0x2192, 0x2193, 0x2044],
    'figures_sups_subs': [0xB2, 0xB3, 0xB9] + rng(0x2070, 0x2079)[0:1] + rng(0x2074, 0x2079) + rng(0x2080, 0x2089),
    'punct_currency': [0x2010, 0x2011, 0x2012, 0x2013, 0x2014, 0x2015, 0x2018, 0x2019, 0x201C, 0x201D, 0x2022, 0x2026, 0x20AC, 0x24, 0xA2, 0xA3, 0xA5, 0xA4],
}
KNOWN_GAPS = {0x17F: 'ſ long s (historic; not drawn)', 0x192: 'ƒ florin (not drawn)'}


def check_coverage():
    out = {}
    for style, _ in STYLES:
        f = TTFont(os.path.join(FD, 'ttf/SynthetixUI-%s.ttf' % style)); cm = f.getBestCmap(); gl = f['glyf']; r = {}
        for k, cps in SETS.items():
            miss = [c for c in cps if c not in cm]; r[k] = dict(n=len(cps), missing=['U+%04X' % c for c in miss])
        # every mapped glyph other than spaces/controls must have an outline or be a composite
        empty = [(hex(c), g) for c, g in cm.items() if c > 0x20 and c not in (0xA0, 0xAD) and not (0x2000 <= c <= 0x200F) and 0x2028 > c and g != '.notdef' and gl[g].numberOfContours == 0]
        r['mapped_but_empty_outline'] = empty[:20]
        r['notdef_mapped'] = [hex(c) for c, g in cm.items() if g == '.notdef']
        out[style] = r
    ok = all(not v['missing'] for s in out.values() for k, v in s.items() if isinstance(v, dict) and 'missing' in v) and all(not s['notdef_mapped'] for s in out.values())
    RES['coverage'] = dict(passed=bool(ok), known_gaps_outside_scope={('U+%04X' % k): v for k, v in KNOWN_GAPS.items()}, detail=out)
    return ok


def tabular_static():
    r = {}; ok = True
    for style, _ in STYLES:
        f = TTFont(os.path.join(FD, 'ttf/SynthetixUI-%s.ttf' % style)); a = {d: f['hmtx'][d + '.tf'][0] for d in DIG}
        a2 = {d: f['hmtx'][d + '.tf.slash'][0] for d in ['zero']}
        r[style] = dict(advances=sorted(set(a.values())), equal=len(set(a.values())) == 1 and a2['zero'] == list(a.values())[0])
        ok &= r[style]['equal']
    vf = TTFont(os.path.join(FD, 'variable/SynthetixUI[wght].ttf')); rv = {}
    for w in (400, 425, 450, 500, 550, 575, 600):
        inst = instancer.instantiateVariableFont(TTFont(os.path.join(FD, 'variable/SynthetixUI[wght].ttf')), {'wght': w})
        advs = sorted({inst['hmtx'][d + '.tf'][0] for d in DIG}); rv[w] = advs; ok &= len(advs) == 1
    RES['tabular'] = dict(passed=bool(ok), static=r, variable_instances=rv)
    return ok


def outlines(font, g):
    gs = font.getGlyphSet(); from fontTools.pens.recordingPen import DecomposingRecordingPen
    rp = DecomposingRecordingPen(gs); gs[g].draw(rp)
    return [pt for op, args in rp.value for pt in args if pt is not None]


def variable_parity():
    res = {}; ok = True
    for style, w in STYLES:
        inst = instancer.instantiateVariableFont(TTFont(os.path.join(FD, 'variable/SynthetixUI[wght].ttf')), {'wght': w})
        st = TTFont(os.path.join(FD, 'ttf/SynthetixUI-%s.ttf' % style)); mx = 0; adv_bad = 0; pts_bad = 0
        for g in st.getGlyphOrder():
            if inst['hmtx'][g][0] != st['hmtx'][g][0]: adv_bad += 1
            a, b = outlines(st, g), outlines(inst, g)
            if len(a) != len(b): pts_bad += 1; continue
            if a: mx = max(mx, max(max(abs(p[0] - q[0]), abs(p[1] - q[1])) for p, q in zip(a, b)))
        res[style] = dict(max_coordinate_delta_units=mx, advance_mismatches=adv_bad, structure_mismatches=pts_bad); ok &= (mx <= 1 and adv_bad == 0 and pts_bad == 0)
    # intermediate monotonicity (500->600 axis between masters): glyph 'n' advance and 'H' stem widths should lie between masters
    inter = {}
    base = {s: TTFont(os.path.join(FD, 'ttf/SynthetixUI-%s.ttf' % s))['hmtx']['n'][0] for s, _ in STYLES}
    for w in (450, 550):
        inst = instancer.instantiateVariableFont(TTFont(os.path.join(FD, 'variable/SynthetixUI[wght].ttf')), {'wght': w}); inter[w] = inst['hmtx']['n'][0]
    mono = base['Regular'] <= inter[450] <= base['Medium'] <= inter[550] <= base['SemiBold']
    res['intermediate_n_advance'] = dict(masters=base, interpolated=inter, monotonic=bool(mono)); ok &= bool(mono)
    RES['variable_parity'] = dict(passed=bool(ok), tolerance_units=1, detail=res)
    return ok


def check_metadata():
    problems = []; info = {}
    files = [('ttf/SynthetixUI-%s.ttf' % s) for s, _ in STYLES] + ['variable/SynthetixUI[wght].ttf']
    for fn in files:
        f = TTFont(os.path.join(FD, fn)); o = f['OS/2']; h = f['head']; hh = f['hhea']; n = f['name']; cm = f.getBestCmap(); i = {}
        i['fsType'] = o.fsType; i['upm'] = h.unitsPerEm; i['vendor'] = o.achVendID; i['version_name5'] = str(n.getName(5, 3, 1, 0x409)); i['fontRevision'] = h.fontRevision
        i['bbox'] = [h.xMin, h.yMin, h.xMax, h.yMax]; i['win'] = (o.usWinAscent, o.usWinDescent); i['hhea'] = (hh.ascent, hh.descent, hh.lineGap); i['typo'] = (o.sTypoAscender, o.sTypoDescender, o.sTypoLineGap)
        if o.fsType != 0: problems.append((fn, 'fsType != 0'))
        if h.yMax > o.usWinAscent or -h.yMin > o.usWinDescent: problems.append((fn, 'bbox clipped by win metrics'))
        if not (o.fsSelection & 128): problems.append((fn, 'USE_TYPO_METRICS off'))
        if (hh.ascent, hh.descent) != (o.sTypoAscender, o.sTypoDescender): problems.append((fn, 'hhea/typo mismatch'))
        for nid in (0, 1, 2, 3, 4, 5, 6, 13, 14):
            if not n.getName(nid, 3, 1, 0x409): problems.append((fn, 'name %d missing' % nid))
        if 'Instrument Sans Project Authors' not in str(n.getName(0, 3, 1, 0x409)): problems.append((fn, 'upstream copyright missing'))
        if 'SIL Open Font License' not in str(n.getName(13, 3, 1, 0x409)): problems.append((fn, 'OFL text missing'))
        names = f.getGlyphOrder()
        if len(set(names)) != len(names): problems.append((fn, 'duplicate glyph names'))
        if f['maxp'].numGlyphs != len(names): problems.append((fn, 'maxp mismatch'))
        if 'fvar' in f:
            fv = f['fvar']; i['axes'] = [(a.axisTag, a.minValue, a.defaultValue, a.maxValue) for a in fv.axes]; i['instances'] = len(fv.instances)
            if 'STAT' not in f: problems.append((fn, 'STAT missing'))
            if 'gvar' not in f or 'HVAR' not in f: problems.append((fn, 'gvar/HVAR missing'))
        info[fn] = i
    RES['metadata_checks'] = dict(passed=not problems, problems=problems, info=info,
                                  note='Own checks only (subset of what Font Bakery covers). Font Bakery itself could not be run: not installed, no network.')
    return not problems


# ----------------------------------------------------------------------------- Chromium
import tempfile
def load(pg, html, wait=400):
    """Load html from a real file:// page (about:blank/set_content cannot load file:// fonts) and wait for fonts."""
    d = tempfile.mkdtemp(); path = os.path.join(d, 't.html'); open(path, 'w').write(html)
    pg.goto('file://' + path); pg.evaluate("document.fonts.ready.then(()=>1)"); pg.wait_for_timeout(wait)
    return pg


def face_css(fam, path, weight=400, fmt=None):
    return '@font-face{font-family:"%s";src:url("file://%s");font-weight:%s}' % (fam, path, weight)


def widths(pg, ids): return {i: pg.evaluate("(i)=>document.getElementById(i).getBoundingClientRect().width", i) for i in ids}


def chromium_tests():
    T = {}
    F = lambda p: os.path.join(FD, p)
    pangram = "Sphinx of black quartz, judge my vow. Ẹ káàbọ̀ Ọ̀gbẹ́ni ɓɗƙƴ ₦1,250.00"
    css = ''.join(face_css('S%s%d' % (k, w), F('%s/SynthetixUI-%s.%s' % (k, s, k)), w) for k in ('ttf', 'woff', 'woff2') for s, w in STYLES)
    css += face_css('SXVF', F('variable/SynthetixUI[wght].ttf'), '400 600') + face_css('SXVF2', F('variable/SynthetixUI[wght].woff2'), '400 600')
    spans = ''.join('<span id="%s%s" style="font-family:S%s%d;font-weight:%d;font-size:100px">%s</span><br>' % (k, s, k, w, w, pangram) for k in ('ttf', 'woff', 'woff2') for s, w in STYLES)
    spans += ''.join('<span id="vf%d" style="font-family:SXVF;font-weight:%d;font-size:100px">%s</span><br>' % (w, w, pangram) for _, w in STYLES)
    spans += ''.join('<span id="vfw%d" style="font-family:SXVF2;font-weight:%d;font-size:100px">%s</span><br>' % (w, w, pangram) for _, w in STYLES)
    html = '<!doctype html><meta charset=utf-8><style>%s span{white-space:pre;font-kerning:normal}</style>%s' % (css, spans)
    with sync_playwright() as p:
        b = p.chromium.launch(args=['--font-render-hinting=none', '--enable-font-subpixel-positioning']); ctx = b.new_context(device_scale_factor=1)
        pg = ctx.new_page(); load(pg, html, 800)
        T['faces_loaded'] = pg.evaluate("Array.from(document.fonts).map(f=>f.family+':'+f.status)")
        ids = [k + s for k in ('ttf', 'woff', 'woff2') for s, _ in STYLES] + ['vf%d' % w for _, w in STYLES] + ['vfw%d' % w for _, w in STYLES]
        W = widths(pg, ids); T['widths_100px'] = W
        T['format_parity_max_delta_px'] = max(max(abs(W['ttf' + s] - W['woff' + s]), abs(W['ttf' + s] - W['woff2' + s])) for s, _ in STYLES)
        T['variable_vs_static_max_delta_px'] = max(max(abs(W['ttf' + s] - W['vf%d' % w]), abs(W['ttf' + s] - W['vfw%d' % w])) for s, w in STYLES)
        # weight mapping / no synthetic bold (static family with 3 faces)
        load(pg, '<!doctype html><meta charset=utf-8><style>%s .t{font-family:"Sttf400","Sttf500","Sttf600";}</style>' % css +
                       '<style>@font-face{font-family:SXS;src:url("file://%s");font-weight:400}@font-face{font-family:SXS;src:url("file://%s");font-weight:500}@font-face{font-family:SXS;src:url("file://%s");font-weight:600}</style>' %
                       (F('ttf/SynthetixUI-Regular.ttf'), F('ttf/SynthetixUI-Medium.ttf'), F('ttf/SynthetixUI-SemiBold.ttf')) +
                       ''.join('<span id="w%d" style="font-family:SXS;font-weight:%d;font-size:100px;white-space:pre">Account management 0123456789</span><br>' % (w, w) for w in (300, 400, 500, 600, 700, 900)) +
                       ''.join('<span id="n%d" style="font-family:SXS;font-weight:%d;font-size:100px;white-space:pre;font-synthesis:none">Account management 0123456789</span><br>' % (w, w) for w in (700, 900)))
        Ww = widths(pg, ['w300', 'w400', 'w500', 'w600', 'w700', 'w900', 'n700', 'n900'])
        T['weights'] = Ww; T['no_synthetic_bold'] = bool(abs(Ww['w700'] - Ww['w600']) < 0.01 and abs(Ww['w900'] - Ww['w600']) < 0.01 and abs(Ww['w300'] - Ww['w400']) < 0.01 and Ww['w400'] < Ww['w500'] < Ww['w600'])
        T['font_synthesis_none_same'] = bool(abs(Ww['n700'] - Ww['w700']) < 0.01)
        # environment parity: DPR, zoom, dark, forced colours, text size (CSS widths must not change)
        base_html = '<!doctype html><meta charset=utf-8><style>@font-face{font-family:SXS;src:url("file://%s");font-weight:400}span{font-family:SXS;font-size:20px;white-space:pre}</style><span id=a>%s</span>' % (F('ttf/SynthetixUI-Regular.ttf'), pangram)
        env = {}
        for name, kw in {'dpr1': dict(device_scale_factor=1), 'dpr2': dict(device_scale_factor=2), 'dpr3': dict(device_scale_factor=3), 'dark': dict(color_scheme='dark'),
                         'forced_colors': dict(forced_colors='active'), 'reduced_motion': dict(reduced_motion='reduce')}.items():
            c2 = b.new_context(**kw); q = c2.new_page(); load(q, base_html, 500); env[name] = q.evaluate("document.getElementById('a').getBoundingClientRect().width"); c2.close()
        q = ctx.new_page(); load(q, base_html, 400); q.evaluate("document.body.style.zoom=2"); env['zoom200_css_width_div2'] = q.evaluate("document.getElementById('a').getBoundingClientRect().width") / 2
        q.evaluate("document.body.style.zoom=1; document.getElementById('a').style.fontSize='40px'"); env['textsize200_div2'] = q.evaluate("document.getElementById('a').getBoundingClientRect().width") / 2
        T['environment_widths'] = env; T['environment_max_delta_px'] = max(env.values()) - min(env.values())
        # OpenType features behave (rendered widths / pixels)
        FE = lambda ff, txt: '<span style="font-feature-settings:%s">%s</span>' % (ff, txt)
        load(pg, '<!doctype html><meta charset=utf-8><style>@font-face{font-family:SXS;src:url("file://%s");font-weight:400}span{font-family:SXS;font-size:60px;white-space:pre;font-kerning:normal;display:inline-block}</style>' % F('ttf/SynthetixUI-Regular.ttf') +
                       ''.join('<div><span id="%s" style="font-feature-settings:%s">%s</span></div>' % (i, ff, t) for i, ff, t in [
                           ('tn0', "'tnum'", '0000000000'), ('tn1', "'tnum'", '1111111111'), ('tn8', "'tnum'", '8888888888'), ('tn9', "'tnum'", '1,234,567.89'), ('tn9b', "'tnum'", '9,999,999.99'),
                           ('pn0', "'pnum'", '0000000000'), ('pn1', "'pnum'", '1111111111'),
                           ('kern1', "'kern' 1", 'AVATAR To Wa Yo'), ('kern0', "'kern' 0", 'AVATAR To Wa Yo'),
                           ('fr0', "normal", '1/2 3/4'), ('fr1', "'frac'", '1/2 3/4'),
                           ('ncur1', "'tnum'", '₦1,250.00'), ('ncur2', "'tnum'", '₦9,999.99')]))
        fw = widths(pg, ['tn0', 'tn1', 'tn8', 'tn9', 'tn9b', 'pn0', 'pn1', 'kern1', 'kern0', 'fr0', 'fr1', 'ncur1', 'ncur2'])
        T['feature_widths'] = fw
        T['tnum_digit_strings_equal'] = bool(abs(fw['tn0'] - fw['tn1']) < 0.01 and abs(fw['tn0'] - fw['tn8']) < 0.01)
        T['tnum_money_columns_align'] = bool(abs(fw['tn9'] - fw['tn9b']) < 0.01 and abs(fw['ncur1'] - fw['ncur2']) < 0.01)
        T['pnum_differs_from_tnum'] = bool(abs(fw['pn0'] - fw['pn1']) > 5)
        T['kerning_active'] = bool(fw['kern1'] < fw['kern0'] - 1)
        T['frac_changes_layout'] = bool(abs(fw['fr0'] - fw['fr1']) > 1)
        b.close()
    ok = (T['format_parity_max_delta_px'] < 0.01 and T['variable_vs_static_max_delta_px'] < 0.05 and T['no_synthetic_bold'] and T['font_synthesis_none_same'] and T['environment_max_delta_px'] < 0.01
          and T['tnum_digit_strings_equal'] and T['tnum_money_columns_align'] and T['pnum_differs_from_tnum'] and T['kerning_active'] and T['frac_changes_layout']
          and all(s.endswith('loaded') for s in T['faces_loaded']))
    T['passed'] = bool(ok); T['engine'] = 'Chromium only (Firefox/WebKit not installed in the build sandbox)'
    RES['chromium'] = T
    return ok


def language_shaping():
    """Decomposed / precomposed / reversed-mark-order text must render pixel-identically (marks attach through GPOS the same way
    precomposed glyphs were built). Checks each Hausa/Yoruba/Igbo letter + tone combination, in all three static weights and the VF."""
    letters = 'EeOoSsIiUuMmNnɛɔ'
    tones = ['', '\u0300', '\u0301', '\u0304']
    cases = {}
    for ch in 'EeOoSsIiUu':
        for t in tones:
            nfd = unicodedata.normalize('NFD', ch + '\u0323' + t); nfc = unicodedata.normalize('NFC', ch + '\u0323' + t)
            rev = ch + t + '\u0323' if t else ch + '\u0323'
            cases['%s+dot+%s' % (ch, t.encode('unicode_escape').decode() or 'none')] = (nfc, nfd, rev)
    for ch in 'MmNn':
        for t in ['\u0300', '\u0301', '\u0307']:
            cases['%s+%s' % (ch, t.encode('unicode_escape').decode())] = (unicodedata.normalize('NFC', ch + t), ch + t, ch + t)
    for ch in 'ɛɔƐƆ':
        for t in ['\u0323', '\u0300', '\u0301']:
            cases['%s+%s' % (ch, t.encode('unicode_escape').decode())] = (ch + t, ch + t, ch + t)
    fails = []; n = 0; loaded = []
    names = list(cases)
    with sync_playwright() as p:
        b = p.chromium.launch(args=['--font-render-hinting=none']); pg = b.new_page(viewport={'width': 600, 'height': 400})
        for fam, path, wt in [('R', 'ttf/SynthetixUI-Regular.ttf', 400), ('S', 'ttf/SynthetixUI-SemiBold.ttf', 600), ('V', 'variable/SynthetixUI[wght].ttf', 500)]:
            face = '@font-face{font-family:F;src:url("file://%s");font-weight:100 900}' % os.path.join(FD, path)
            body = ''.join('<div>%s</div>' % ('<span id="c%d_%d">%s</span>' % (i, k, form)) for i, nm in enumerate(names) for k, form in enumerate(cases[nm]))
            load(pg, '<!doctype html><meta charset=utf-8><style>%s body{margin:0;background:#fff}span{font-family:F;font-weight:%d;font-size:160px;line-height:260px;display:inline-block;padding:0 40px;white-space:pre}div{height:262px}</style>%s' % (face, wt, body), 600)
            loaded.append((fam, pg.evaluate("Array.from(document.fonts).map(f=>f.status)")))
            for i, nm in enumerate(names):
                imgs = [np.asarray(Image.open(io.BytesIO(pg.locator('#c%d_%d' % (i, k)).screenshot())).convert('L')).astype(int) for k in range(3)]
                n += 1
                for k in (1, 2):
                    a_, c_ = imgs[0], imgs[k]
                    if a_.shape != c_.shape: fails.append((fam, nm, 'size-mismatch', k, a_.shape, c_.shape)); continue
                    d = int((np.abs(a_ - c_) > 60).sum())
                    if d > 40: fails.append((fam, nm, 'pixel-diff', k, d))
        b.close()
    if any(st != ['loaded'] for _, st in loaded): fails.append(('font-not-loaded', loaded))
    RES['language_shaping'] = dict(passed=not fails, comparisons=n, fonts_loaded=loaded, failures=fails[:40], method='NFC vs NFD vs reversed-mark-order render parity in Chromium at 160px, each form in its own block at an integer origin (threshold 40 px)')
    return not fails


if __name__ == '__main__':
    which = sys.argv[1:] or ['coverage', 'tabular', 'parity', 'metadata', 'chromium', 'shaping']
    fn = dict(coverage=check_coverage, tabular=tabular_static, parity=variable_parity, metadata=check_metadata, chromium=chromium_tests, shaping=language_shaping)
    status = {}
    for k in which:
        try: status[k] = bool(fn[k]())
        except Exception as e:
            import traceback; traceback.print_exc(); status[k] = False; RES['error_' + k] = repr(e)
        print(k, 'PASS' if status[k] else 'FAIL', flush=True)
    path = os.path.join(ROOT, 'reports', 'checks_v4.json')
    old = json.load(open(path)) if os.path.exists(path) else {}
    old.update(RES); old['status'] = {**old.get('status', {}), **status}
    json.dump(old, open(path, 'w'), indent=1, default=str)
    sys.exit(0 if all(status.values()) else 1)
