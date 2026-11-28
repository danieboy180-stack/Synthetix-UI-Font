"""Phase B (partial, steps 13-18): measure the reference pangram crops in reference/captures/ and compare with Synthetix.

Everything is computed from files in the repo (reference/captures/*.png + captures.json + fonts/ttf/*.ttf).
These are SESSION-1 MEASUREMENTS, not scorer output: the frozen scorer (tools/scorer/*) is untouched and nothing here is a score.
Method (same code path for reference and font, so method bias cancels):
  * coverage = (bg - gray) / (bg - ink), sub-pixel edges where coverage crosses 0.5, stems as sum of coverage (area / length)
  * glyph groups = connected components merged when their x-ranges overlap (dots of i j : ; ! ? and the % circles)
  * Synthetix side: HarfBuzz shaping (kerning on) for positions, exact outline bounds for ink boxes, PIL/FreeType raster for stems
  * all lengths are normalised by cap height; errors are reported in px at a 16 px font size (cap = 0.70 em = 11.2 px)

usage: python tools/measure_captures.py [font.ttf]   -> reports/session1/capture_measurements.json + .md
"""
import os, sys, json, math
import numpy as np
from PIL import Image, ImageFont, ImageDraw
from scipy import ndimage as ndi
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
FONT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'fonts/ttf/SynthetixUI-Regular.ttf')
CAP_U = 700.0                     # Synthetix cap height in font units (build config: cap 700, xh 500, asc 729)
PX16_CAP = 16 * CAP_U / 1000.0    # cap height in px at a 16 px font size

# ---------------------------------------------------------------- image side
def load(path):
    a = np.array(Image.open(path).convert('L')).astype(float)
    bg = np.percentile(a, 99); ink = np.percentile(a, 0.5)
    return np.clip((bg - a) / max(bg - ink, 1), 0, 1)

def crossing(p, i_out, i_in):
    """sub-pixel position where profile p crosses 0.5 going from sample i_out (outside, <0.5) to i_in (inside)."""
    a, b = p[i_out], p[i_in]
    if b == a: return float(i_in)
    t = (0.5 - a) / (b - a)
    return i_out + t * (i_in - i_out)

def box_subpixel(cov, x0, x1, y0, y1):
    """sub-pixel ink box inside the integer box (inclusive). Returns left, right, top, bottom edges (px, edge coordinates)."""
    pad = 2
    xs0, xs1 = max(x0 - pad, 0), min(x1 + pad, cov.shape[1] - 1)
    ys0, ys1 = max(y0 - pad, 0), min(y1 + pad, cov.shape[0] - 1)
    sub = cov[ys0:ys1 + 1, xs0:xs1 + 1]
    colmax, rowmax = sub.max(0), sub.max(1)
    def edge(p, first_in, last_in):
        l = crossing(p, first_in - 1, first_in) if first_in > 0 else float(first_in)
        r = crossing(p, last_in + 1, last_in) if last_in < len(p) - 1 else float(last_in + 1)
        return l + 0.5, r + 0.5      # pixel-centre -> edge coordinates
    cx = np.where(colmax >= 0.5)[0]; ry = np.where(rowmax >= 0.5)[0]
    l, r = edge(colmax, cx[0], cx[-1]); t, b = edge(rowmax, ry[0], ry[-1])
    return l + xs0 - 0.5, r + xs0 - 0.5, t + ys0 - 0.5, b + ys0 - 0.5

def line_groups(cov, y0, y1, expected_tokens):
    """connected components in a text line, merged by x-overlap, ordered left to right."""
    band = cov[y0:y1 + 1] >= 0.5
    lab, n = ndi.label(band, structure=np.ones((3, 3)))
    comps = []
    for i, sl in enumerate(ndi.find_objects(lab), 1):
        ys, xs = sl
        comps.append([xs.start, xs.stop - 1, ys.start + y0, ys.stop - 1 + y0])
    comps.sort()
    groups = []
    for c in comps:
        if groups:
            g = groups[-1]; ov = min(g[1], c[1]) - max(g[0], c[0]) + 1
            if ov > 0.4 * min(g[1] - g[0] + 1, c[1] - c[0] + 1):
                g[0], g[1], g[2], g[3] = min(g[0], c[0]), max(g[1], c[1]), min(g[2], c[2]), max(g[3], c[3]); continue
        groups.append(list(c))
    return groups

def tokens_of(line):
    """characters that produce one glyph group each; the double quote renders as two separate ticks."""
    t = []
    for ch in line:
        if ch == ' ': continue
        t.append(ch)
        if ch == '"': t.append('"2')
    return t

def stem_metrics(cov, box, ch):
    """area-based stem / bar thickness (px) for selected glyphs. box = integer (x0,x1,y0,y1). Returns dict name->px."""
    x0, x1, y0, y1 = box; w, h = x1 - x0 + 1, y1 - y0 + 1
    g = cov[y0:y1 + 1, x0:x1 + 1]
    out = {}
    rows = lambda a, b: slice(int(h * a), max(int(h * b), int(h * a) + 1))
    cols = lambda a, b: slice(int(w * a), max(int(w * b), int(w * a) + 1))
    if ch in ('l', 'I'):
        out['stem_' + ch] = float(np.median(g[rows(.30, .70)].sum(1)))
    elif ch == 'H':
        out['stem_H'] = float(np.median(g[rows(.15, .35), cols(0, .45)].sum(1)))
    elif ch == 'T':
        out['stem_T'] = float(np.median(g[rows(.40, .90)].sum(1)))
    elif ch == 'E':
        out['E_arm_top'] = float(np.median(g[:, cols(.70, .85)][rows(0, .30)].sum(0)))
        out['E_arm_bottom'] = float(np.median(g[:, cols(.70, .85)][rows(.70, 1)].sum(0)))
    elif ch == 'o':
        mid = g[rows(.45, .55)]
        out['o_sides'] = float(np.median(mid[:, :w // 2].sum(1)) + np.median(mid[:, w // 2:].sum(1))) / 2
        cc = g[:, cols(.45, .55)]
        out['o_top_bottom'] = float((np.median(cc[rows(0, .5)].sum(0)) * 0 + cc[rows(0, .5)].sum(0).mean() + cc[rows(.5, 1)].sum(0).mean()) / 2)
    elif ch == 'O':
        mid = g[rows(.45, .55)]
        out['O_sides'] = float(np.median(mid[:, :w // 2].sum(1)) + np.median(mid[:, w // 2:].sum(1))) / 2
    elif ch == 'z':
        out['z_bars'] = float((g[:, cols(.15, .30)][rows(0, .5)].sum(0).mean() + g[:, cols(.70, .85)][rows(.5, 1)].sum(0).mean()) / 2)
    return out

def measure_sheet(cap):
    cov = load(os.path.join(ROOT, cap['file']))
    on = (cov >= 0.5).sum(1) > 0; bands = []; s = None
    for y, v in enumerate(on):
        if v and s is None: s = y
        if (not v) and s is not None: bands.append((s, y - 1)); s = None
    assert len(bands) == len(cap['lines']), (cap['id'], len(bands), len(cap['lines']))
    glyphs = []; problems = []
    for li, ((y0, y1), line) in enumerate(zip(bands, cap['lines'])):
        toks = tokens_of(line); groups = line_groups(cov, y0, y1, toks)
        if len(groups) != len(toks):
            problems.append(dict(sheet=cap['id'], line=li, expected=len(toks), found=len(groups), text=line)); continue
        for tk, g in zip(toks, groups):
            l, r, t, b = box_subpixel(cov, *g)
            gl = dict(ch=('"' if tk == '"2' else tk), tick2=(tk == '"2'), line=li, left=l, right=r, top=t, bottom=b, w=r - l, h=b - t, ibox=g)
            gl.update(stem_metrics(cov, (g[0], g[1], g[2], g[3]), tk))
            glyphs.append(gl)
    # per-line baseline / heights from flat-edged letters (every line has its own baseline)
    FLAT_BASE = set('EFHIKLMNTXZhklmnrxzvw'); CAP_TOP = set('EFHIKLMNTXYZVW')
    per_line = {}
    for li in sorted({g['line'] for g in glyphs}):
        L = [g for g in glyphs if g['line'] == li and not g['tick2']]
        mv = lambda chars, key: ([float(np.median([g[key] for g in L if g['ch'] in chars]))] if any(g['ch'] in chars for g in L) else [None])[0]
        base = mv(FLAT_BASE, 'bottom')
        if base is None: continue
        d = dict(baseline=base)
        if sum(g['ch'] in CAP_TOP for g in L) >= 2: d['cap_px'] = base - mv(CAP_TOP, 'top')
        if sum(g['ch'] in 'xzvw' for g in L) >= 2: d['xh_px'] = base - mv(set('xzvw'), 'top')
        if sum(g['ch'] in 'bdhkl' for g in L) >= 2: d['asc_px'] = base - mv(set('bdhkl'), 'top')
        if sum(g['ch'] in 'pq' for g in L) >= 1: d['desc_px'] = mv(set('pq'), 'bottom') - base
        per_line[li] = d
    pick = lambda k: float(np.mean([d[k] for d in per_line.values() if k in d]))
    vert = dict(cap_px=pick('cap_px'), xh_px=pick('xh_px'), asc_px=pick('asc_px'), desc_px=pick('desc_px'), per_line=per_line)
    cap_px = vert['cap_px']
    ratios = dict(xh_over_cap=vert['xh_px'] / cap_px, asc_over_cap=vert['asc_px'] / cap_px, desc_over_cap=vert['desc_px'] / cap_px)
    return dict(id=cap['id'], bands=bands, glyphs=glyphs, problems=problems, vertical=vert, ratios=ratios, lines=cap['lines'])

# ---------------------------------------------------------------- font side
class Syn:
    def __init__(self, path):
        self.path = path; self.tt = TTFont(path); self.gs = self.tt.getGlyphSet(); self.cmap = self.tt.getBestCmap()
        self.upm = self.tt['head'].unitsPerEm
        self.hbfont = hb.Font(hb.Face(open(path, 'rb').read())); self.bounds = {}
    def bbox(self, gname):
        if gname not in self.bounds:
            bp = BoundsPen(self.gs); self.gs[gname].draw(bp); self.bounds[gname] = bp.bounds
        return self.bounds[gname]
    def shape(self, text):
        buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties(); hb.shape(self.hbfont, buf, {'kern': True, 'liga': False})
        x = 0; out = []
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            out.append((info.cluster, self.tt.getGlyphName(info.codepoint), x + pos.x_offset, pos.x_advance)); x += pos.x_advance
        return out, x
    def line_boxes(self, line):
        """ink boxes in font units for each token of a line, in token order (matching tokens_of)."""
        sh, total = self.shape(line); res = []
        for cl, gname, x, adv in sh:
            ch = line[cl]
            if ch == ' ': continue
            bb = self.bbox(gname)
            if ch == '"':      # the double quote is one glyph in the font; the reference renders two ticks. split at the glyph's middle for pairing
                res.append((ch, x + bb[0], x + bb[2], bb[1], bb[3], 'double')); continue
            res.append((ch, x + bb[0], x + bb[2], bb[1], bb[3], None))
        return res, total
    def glyph_cov(self, ch, em_px):
        f = ImageFont.truetype(self.path, size=em_px, layout_engine=ImageFont.Layout.BASIC)
        W = int(em_px * 1.6); H = int(em_px * 1.6)
        im = Image.new('L', (W, H), 255); d = ImageDraw.Draw(im)
        d.text((em_px * 0.3, em_px * 0.25), ch, font=f, fill=0)
        a = 1 - np.array(im).astype(float) / 255
        ys, xs = np.where(a >= 0.5)
        return a, (xs.min(), xs.max(), ys.min(), ys.max())

def syn_stems(syn, cap_px):
    em = cap_px / (CAP_U / 1000.0)
    out = {}
    for ch in 'lIHTEoOz':
        a, b = syn.glyph_cov(ch, em)
        out.update(stem_metrics(a, b, ch))
    return out

# ---------------------------------------------------------------- compare
def main():
    caps = json.load(open(os.path.join(ROOT, 'reference/captures/captures.json')))['captures']
    syn = Syn(FONT)
    sheets = [measure_sheet(c) for c in caps]
    report = dict(font=os.path.relpath(FONT, ROOT), method='see module docstring', px16_cap=PX16_CAP, sheets=[], aggregate={})
    per_char_w = {}; per_char_h = {}; per_pair = {}; per_stem = {}; line_w = {}
    for sh in sheets:
        cap_px = sh['vertical']['cap_px']
        # Synthetix boxes, token-aligned, per line
        syn_stems_u = syn_stems(syn, cap_px)
        for k, v in sh['glyphs'][0].items(): pass
        by_line = {}
        for g in sh['glyphs']: by_line.setdefault(g['line'], []).append(g)
        sheet_rows = []
        for li, gl in by_line.items():
            boxes, total = syn.line_boxes(sh['lines'][li])
            toks = [g for g in gl]
            # align: reference tokens include 2 ticks for '"'; font has one glyph -> merge the two reference ticks into one box
            merged = []; i = 0
            while i < len(toks):
                g = toks[i]
                if g['ch'] == '"' and not g['tick2'] and i + 1 < len(toks) and toks[i + 1]['tick2']:
                    t2 = toks[i + 1]; merged.append(dict(g, right=t2['right'], w=t2['right'] - g['left'], top=min(g['top'], t2['top']), bottom=max(g['bottom'], t2['bottom']))); i += 2
                else: merged.append(g); i += 1
            if len(merged) != len(boxes): continue
            # line ink width (first ink to last ink), in cap units
            sb = [(b[1], b[2]) for b in boxes]
            ref_w = (merged[-1]['right'] - merged[0]['left']) / cap_px; syn_w = (max(x[1] for x in sb) - min(x[0] for x in sb)) / CAP_U
            line_w.setdefault(sh['lines'][li], []).append(dict(sheet=sh['id'], ref_over_cap=ref_w, syn_over_cap=syn_w, err_px16=(ref_w - syn_w) * PX16_CAP))
            for g, b in zip(merged, boxes):
                ch = g['ch']; syn_w_u = b[2] - b[1]; syn_h_u = b[4] - b[3]
                per_char_w.setdefault(ch, []).append((g['w'] / cap_px - syn_w_u / CAP_U) * PX16_CAP)
                per_char_h.setdefault(ch, []).append((g['h'] / cap_px - syn_h_u / CAP_U) * PX16_CAP)
            for (g1, b1), (g2, b2) in zip(zip(merged, boxes), zip(merged[1:], boxes[1:])):
                if g1['ch'] in '"' or g2['ch'] in '"': continue
                ref_gap = (g2['left'] - g1['right']) / cap_px; syn_gap = (b2[1] - b1[2]) / CAP_U
                per_pair.setdefault(g1['ch'] + g2['ch'], []).append((ref_gap - syn_gap) * PX16_CAP)
        for g in sh['glyphs']:
            for k, v in g.items():
                if k.startswith(('stem_', 'E_arm', 'o_', 'O_', 'z_')) and isinstance(v, float):
                    per_stem.setdefault(k, []).append(v / cap_px)
        rs = dict(id=sh['id'], cap_px=cap_px, vertical=sh['vertical'], ratios=sh['ratios'], problems=sh['problems'], n_glyph_groups=len(sh['glyphs']))
        report['sheets'].append(rs)
    # synthetic reference of stems from the font at the mean cap
    mean_cap = float(np.mean([s['vertical']['cap_px'] for s in sheets]))
    syn_st = {k: v / mean_cap for k, v in syn_stems(syn, mean_cap).items()}
    A = report['aggregate']
    m = lambda v: float(np.mean(v)); sd = lambda v: float(np.std(v))
    A['vertical_ratio'] = {k: dict(reference_mean=m([s['ratios'][k] for s in sheets]), reference_sd=sd([s['ratios'][k] for s in sheets]),
                                  synthetix=dict(xh_over_cap=500 / CAP_U, asc_over_cap=729 / CAP_U, desc_over_cap=-syn.bbox('p')[1] / CAP_U)[k]) for k in ('xh_over_cap', 'asc_over_cap', 'desc_over_cap')}
    A['stems_over_cap'] = {k: dict(reference_mean=m(v), reference_sd=sd(v), n=len(v), synthetix=syn_st.get(k),
                                   ref_over_syn=(m(v) / syn_st[k]) if syn_st.get(k) else None) for k, v in sorted(per_stem.items())}
    A['glyph_width_err_px16'] = {k: dict(mean=m(v), sd=sd(v), n=len(v)) for k, v in sorted(per_char_w.items())}
    A['glyph_height_err_px16'] = {k: dict(mean=m(v), sd=sd(v), n=len(v)) for k, v in sorted(per_char_h.items())}
    A['pair_gap_err_px16'] = {k: dict(mean=m(v), sd=sd(v), n=len(v)) for k, v in sorted(per_pair.items())}
    A['line_ink_width'] = {k: v for k, v in line_w.items()}
    allw = [abs(x['mean']) for x in A['glyph_width_err_px16'].values()]; allp = [abs(x['mean']) for x in A['pair_gap_err_px16'].values()]
    A['summary'] = dict(
        glyph_width=dict(n=len(allw), within_0_5px=sum(v <= .5 for v in allw), within_1px=sum(v <= 1 for v in allw), mean_abs_px16=m(allw)),
        pair_gap=dict(n=len(allp), within_0_5px=sum(v <= .5 for v in allp), within_1px=sum(v <= 1 for v in allp), mean_abs_px16=m(allp), rms_px16=float(np.sqrt(np.mean(np.square([x['mean'] for x in A['pair_gap_err_px16'].values()]))))),
        measurement_noise_px16=dict(width_sd_mean=m([x['sd'] for x in A['glyph_width_err_px16'].values()]), gap_sd_mean=m([x['sd'] for x in A['pair_gap_err_px16'].values()])))
    out = os.path.join(ROOT, 'reports/session1/capture_measurements.json')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(report, open(out, 'w'), indent=1, default=float)
    print(json.dumps(dict(sheets=[(s['id'], round(s['cap_px'], 2), s['n_glyph_groups'], s['problems']) for s in report['sheets']], summary=A['summary'], vertical=A['vertical_ratio']), indent=1, default=float))

if __name__ == '__main__':
    main()
