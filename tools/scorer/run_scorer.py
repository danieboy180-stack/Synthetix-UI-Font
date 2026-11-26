"""Runner around the frozen v3 scorer (fmeasure.py + evalref.py, path-only port).

It computes only what can be measured from the repo's reference data (reference/report_reference.json):
vertical metrics, glyph widths, pair gaps, space gaps, string ink widths, stems.
It does NOT compute shape IoU (needs reference bitmaps, absent) or the UI held-out set (browser_fit.py absent).
Those two are reported as NOT MEASURED by tools/contract_check.py, never estimated.

usage: python tools/scorer/run_scorer.py <font.ttf|woff|woff2> <weight> <out.json>
"""
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from evalref import evaluate

# Regular stem targets (HIGH confidence, from v3 make_scores.py). Heavier targets are scaled by the report's
# measured lc-stem ratio (7.26/5.82 and 8.96/5.82): inferred (MEDIUM/LOW), flagged as such in every report.
T0 = {'H': 6.13, 'T': 6.10, 'n': 5.82, 'l': 5.82, 'o_sides': 6.15, 'O_sides': 6.52, 'E_arms': 6.0,
      'O_tb': 6.0, 'o_tb': 5.65, 'z_bars': 5.67, 'e_cb': 5.02}
HEAVY_K = {400: 1.0, 500: 7.26 / 5.82, 600: 8.96 / 5.82}


def summarise(path, weight):
    E, R = evaluate(path, weight=weight)
    w = [(ch, c, r) for ch, c, r in E['widths']]
    wfail = [(ch, c, r, c - r) for ch, c, r in w if abs(c - r) > 1]
    vert = E['vertical']
    vfail = [k for k, (a, b) in vert.items() if a is None or abs(a - b) > 1.0]
    allgaps = {**E['pair_gaps']['upper'], **E['pair_gaps']['lower']}
    gd = {k: c - r for k, (c, r) in allgaps.items()}
    sg = {k: c - r for k, (c, r) in E['space_gaps'].items()}
    st = E['stems']
    stems = {'H': np.mean([st['H stem L'], st['H stem R']]), 'T': st['T stem'], 'n': st['n stem'], 'l': st['l stem'],
             'o_sides': np.mean(st['o sides']), 'O_sides': np.mean(st['O sides']),
             'E_arms': np.mean(st['E arms']) if st['E arms'] else float('nan'),
             'O_tb': np.mean(st['O top/bottom']), 'o_tb': np.mean(st['o top/bottom']),
             'z_bars': np.mean(st['z bars']), 'e_cb': st['e crossbar'] if st['e crossbar'] else float('nan')}
    k = HEAVY_K[weight]
    spass = {kk: bool(not np.isnan(stems[kk]) and abs(stems[kk] / (T0[kk] * k) - 1) <= 0.05) for kk in T0}
    strs = {q: dict(candidate=a, reference=b, pass_1pct=bool(abs(a - b) / b <= 0.01)) for q, (a, b) in E['strings'].items()}
    return dict(
        font=os.path.basename(path), weight=weight, px_per_em=E['_meta']['px'],
        vertical=dict(n=len(vert), passed=len(vert) - len(vfail), failed=vfail,
                      values={kk: dict(candidate=(None if a is None else float(a)), reference=b) for kk, (a, b) in vert.items()}),
        widths=dict(n=len(w), within_1px=len(w) - len(wfail), pct=100 * (len(w) - len(wfail)) / len(w),
                    mape=E['width_stats']['mape'], failing=[dict(ch=a, cand=b, ref=c, delta=d) for a, b, c, d in wfail]),
        pair_gaps=dict(n=len(gd), within_1px=int(sum(abs(v) <= 1 for v in gd.values())),
                       pct=100 * float(np.mean([abs(v) <= 1 for v in gd.values()])), rms=E['gap_stats']['rms'],
                       failing={kk: v for kk, v in gd.items() if abs(v) > 1}),
        space_gaps=dict(n=len(sg), within_1px=int(sum(abs(v) <= 1 for v in sg.values())), delta=sg),
        pangram_word_gap_rms=E['pangram_word_gap_stats']['rms'],
        strings=strs,
        stems=dict(measured={kk: float(v) for kk, v in stems.items()},
                   target_scale=k, target_confidence=('HIGH' if weight == 400 else 'INFERRED (MEDIUM/LOW)'),
                   n=len(T0), within_5pct=int(sum(spass.values())), per_stem=spass))


if __name__ == '__main__':
    path, weight, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    res = summarise(path, weight)
    json.dump(res, open(out, 'w'), indent=1, default=float)
    v, w_, g, s = res['vertical'], res['widths'], res['pair_gaps'], res['stems']
    print(f"{res['font']} w{weight}: vertical {v['passed']}/{v['n']} {v['failed']} | widths {w_['within_1px']}/{w_['n']} "
          f"({w_['pct']:.1f}%) MAPE {w_['mape']:.2f} | gaps {g['within_1px']}/{g['n']} RMS {g['rms']:.2f} | "
          f"stems {s['within_5pct']}/{s['n']} ({s['target_confidence']})")
