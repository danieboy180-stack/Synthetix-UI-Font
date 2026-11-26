"""contract_check.py - evaluates the 10/10 contract (docs: CONTRACT_10_10.md) from saved artifacts. Never estimates: a gate that needs a tool or
reference that is not present is NOT MEASURED. Writes reports/contract_status.json and reports/CONTRACT_STATUS.md."""
import json, os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
J = lambda p: json.load(open(os.path.join(ROOT, p)))
rows = []
def gate(group, name, status, evidence): rows.append(dict(group=group, gate=name, status=status, evidence=evidence))
sc = J('reports/scorer/v4_Regular.json'); chk = J('reports/checks_v4.json'); rep = J('reports/reproducibility.json'); conf = J('reports/confusables.json'); con = J('reports/contrast.json')
gt = J('reference/v3-reports/glyph_table.json') if os.path.exists(os.path.join(ROOT, 'reference/v3-reports/glyph_table.json')) else None
# ---- hard gates
gate('Hard', 'Font Bakery universal + Google Fonts profiles: 0 FAIL', 'NOT MEASURED', 'fontbakery not installed and no network in the build sandbox. tools/run_checks.py::check_metadata is a small own subset, not a substitute.')
cov = chk['coverage']['passed']; shp = chk['language_shaping']
gate('Hard', 'Pri-African coverage + language shaping (Hausa, Yoruba, Igbo)', 'PASS' if cov and shp['passed'] else 'FAIL', 'coverage sets complete in 3 masters; %d NFC/NFD/reversed-mark render comparisons, %d failures (Chromium).' % (shp['comparisons'], len(shp['failures'])))
lc = J('reports/latin_core_letters.json')
gate('Hard', 'Latin Core coverage (official 324-glyph list)', 'PARTIAL' if lc['passed_letters'] else 'FAIL', 'official Core letters: 219/219 present in all 3 masters (source: googlefonts/glyphsets 0.6.19). NOT verified: the 104 non-letter Core glyphs (list not retrievable offline) and the unencoded /idotaccent glyph (absent).')
gate('Hard', 'Tabular figures equal width; no .notdef for required characters', 'PASS' if chk['tabular']['passed'] and cov else 'FAIL', 'static + 7 variable instances equal; no cmap entry maps to .notdef.')
gate('Hard', 'Clean-clone build reproduces recorded SHA-256', 'PASS' if rep['identical'] else 'FAIL', '%d/%d font files identical from a clean copy of the inputs (checked under two PYTHONHASHSEED values). Run inside the same sandbox, not on a separate machine/CI.' % (rep['files_compared'] - len(rep['mismatches']), rep['files_compared']))
vp = chk['variable_parity']
gate('Hard', 'Variable and static agree within 1 unit', 'PASS' if vp['passed'] else 'FAIL', 'max coordinate delta %s units at 400/500/600; advances identical.' % max(v['max_coordinate_delta_units'] for k, v in vp['detail'].items() if k in ('Regular', 'Medium', 'SemiBold')))
ch = chk['chromium']
gate('Hard', 'Advance widths identical across Chromium, Firefox, WebKit, native apps', 'NOT MEASURED', 'Chromium only: TTF/WOFF/WOFF2/variable agree (max delta %.3f px); DPR 1-3, dark, forced-colours, 200%% zoom/text agree (%.3f px). Firefox, WebKit, iOS, Android not run.' % (ch['format_parity_max_delta_px'], ch['environment_max_delta_px']))
ofl = open(os.path.join(ROOT, 'fonts/OFL.txt')).read(); ok = 'Instrument Sans Project Authors' in ofl and 'SIL OPEN FONT LICENSE VERSION 1.1' in ofl.upper()
gate('Hard', 'OFL text and copyright intact', 'PASS' if ok and chk['metadata_checks']['passed'] else 'FAIL', 'fonts/OFL.txt + name IDs 0/13/14 verified.')
gate('Hard', 'Name clearance recorded', 'RECORDED - DECISION OPEN', 'NAME_CLEARANCE.md: an established DeFi protocol named Synthetix exists (web search). Trademark/domain registries were not searched. Owner decision pending.')
gate('Hard', 'Zero open critical defects', 'FAIL', 'Open: name collision (critical for any public release), Q tail, J/K/R/a/C/G shape gaps, rn~m confusable, variable latin subset over budget. See V4_REPORT.md.')
# ---- fidelity
w, g_, v_, s_ = sc['widths'], sc['pair_gaps'], sc['vertical'], sc['stems']
gate('Fidelity', 'Shape similarity >= 0.85 on >= 90% of Match glyphs', 'FAIL (recorded, not re-measured)', ('V3 recorded raw IoU: 31/52 = 59.6% >= 0.85. The outlines are byte-identical in V4 (regression ledger), so the recorded values carry over. Reference bitmaps are absent: cannot re-measure.' if gt else 'no record'))
gate('Fidelity', 'Widths within 1 px for >= 90%', 'PASS' if w['pct'] >= 90 else 'FAIL', '%d/%d = %.1f%% (frozen scorer, Regular). Failing: %s' % (w['within_1px'], w['n'], w['pct'], ' '.join(repr(f['ch']) for f in w['failing'])))
gate('Fidelity', 'Held-out pair gaps within 1 px for >= 90%', 'FAIL', '%d/%d = %.1f%%; NOT held out (V3 fitted on the same pairs), so this is an upper bound.' % (g_['within_1px'], g_['n'], g_['pct']))
gate('Fidelity', 'Vertical metrics all within 1 px', 'PASS' if not v_['failed'] else 'FAIL', '%d/%d; failing: %s' % (v_['passed'], v_['n'], v_['failed']))
gate('Fidelity', 'Stems within 5% in all four weights from real references', 'FAIL / NOT MEASURABLE', 'Regular %d/%d (HIGH targets). Medium/SemiBold targets are inferred; no Bold exists; no heavier references. Cannot be met without new references.' % (s_['within_5pct'], s_['n']))
# ---- quality
gate('Quality', 'Small-size confusables (Il1, O0, rn~m at 12-14 px)', 'FAIL (default); passes with opt-in ss13', 'default worst-case Jaccard: %s; with ss13+zero: %s. Pre-registered threshold %.2f. Default fails %d of %d pairs; ss13+zero passes %d of %d.' % ({k.split('| ')[1]: v for k, v in conf['worst_case'].items() if k.startswith('default')}, {k.split('| ')[1]: v for k, v in conf['worst_case'].items() if k.startswith('ss13')}, conf['threshold'], sum(not v for k, v in conf['distinct'].items() if k.startswith('default')), sum(1 for k in conf['distinct'] if k.startswith('default')), sum(v for k, v in conf['distinct'].items() if k.startswith('ss13')), sum(1 for k in conf['distinct'] if k.startswith('ss13'))))
gate('Quality', 'WCAG 2.2 AA contrast pairs (light + dark)', 'PASS' if not con['failures'] else 'FAIL', '%d pairs, %d failures. Palette is a placeholder.' % (len(con['pairs']), len(con['failures'])))
sz = J('reports/subset_sizes.json'); bd = J('build/budgets.json'); over = []
for kind in ('static', 'variable'):
    for sub, lim in bd[kind].items():
        vals = [v for k, v in sz.items() if k.startswith(kind + '/') and k.endswith('/' + sub) or (kind == 'variable' and k == 'variable/' + sub)]
        if vals and max(vals) > lim: over.append('%s/%s %d > %d' % (kind, sub, max(vals), lim))
gate('Quality', 'Subset byte budgets (registered before first export)', 'FAIL' if over else 'PASS', 'over budget: %s. The variable latin-lite subset (core features + ss13) is %d B, within its 45,000 B limit; the owner decides which variable build ships.' % (over or 'none', sz.get('variable/latin-lite', 0)))
for name in ('Human review of named kerning pairs', 'Token adoption on real product screens (one per platform)', 'Native iOS/Android test apps', 'Firefox + WebKit rendering', 'Real-device checks'):
    gate('Quality', name, 'NOT DONE', 'needs people/devices/tools not available in this run (scaffolds provided where possible).')
gate('Identity', 'Blind identity review by two reviewers (IDENTITY_DIRECTION.md)', 'NOT DONE', 'requires two human reviewers.')
cnt = {}
for r in rows: cnt[r['status'].split(' ')[0]] = cnt.get(r['status'].split(' ')[0], 0) + 1
out = dict(verdict='NOT 10/10. Release candidate V4.0.10; V4.1.0 withheld.', counts=cnt, gates=rows)
json.dump(out, open(os.path.join(ROOT, 'reports/contract_status.json'), 'w'), indent=1)
md = ['# Contract status (generated by tools/contract_check.py)', '', '**Verdict: %s**' % out['verdict'], '', '| Group | Gate | Status | Evidence |', '|---|---|---|---|']
for r in rows: md.append('| %s | %s | **%s** | %s |' % (r['group'], r['gate'], r['status'], r['evidence'].replace('|', '/')))
open(os.path.join(ROOT, 'reports/CONTRACT_STATUS.md'), 'w').write('\n'.join(md) + '\n')
print(out['verdict'], cnt)
for r in rows: print('-', r['status'].ljust(34), r['gate'])
