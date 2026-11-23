"""Export the family: static TTFs (all weights; only 300/400/500 are validated), UFO sources for the valid masters,
WOFF files, per-weight validity report, SHA-256 checksums.  Run after varbuild.py."""
import os, json, hashlib
import fontbuild, varbuild
from fontTools.ttLib import TTFont

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
VALID = (300, 400, 500)
names = {300: 'Light', 400: 'Regular', 500: 'Medium', 600: 'SemiBold', 700: 'Bold'}
for d in ('fonts/ttf', 'fonts/woff', 'sources/masters', 'reports/qa', 'reports/build_reports'):
    os.makedirs(f'{BASE}/{d}', exist_ok=True)

M, fit = varbuild.build_masters([300, 400, 500, 600, 700])
validity = {}
for w, nm in names.items():
    c, g, log = fontbuild.make_master('A', w)
    topo_bad = [n for n in g if len(g[n]['contours']) != len(M[400][1][n]['contours'])]
    validity[w] = {'style': nm, 'stem': round(c.v, 1), 'fit_err_max_units': fit[w],
                   'topology_differs_from_regular': topo_bad, 'valid_for_release': w in VALID}
    tag = '' if w in VALID else '-EXPERIMENTAL-NOT-VALIDATED'
    p = f'{BASE}/fonts/ttf/StackraSans-{nm}{tag}.ttf'
    fontbuild.build_ttf(p, g, c, family='Stackra Sans', style=nm, weight=w)
    if w in VALID:
        fontbuild.write_ufo(f'{BASE}/sources/masters/StackraSans-{nm}.ufo', 'A', w, g, c, style=nm)
    f = TTFont(p); f.flavor = 'woff'; f.save(f'{BASE}/fonts/woff/StackraSans-{nm}{tag}.woff')
vfp = f'{BASE}/fonts/variable/StackraSans-VF.ttf'
if os.path.exists(vfp):
    vf = TTFont(vfp); vf.flavor = 'woff'; vf.save(f'{BASE}/fonts/woff/StackraSans-VF.woff')
try:
    import brotli; has_brotli = True
except Exception:
    has_brotli = False
json.dump({'weights': validity, 'woff2': 'built' if has_brotli else 'NOT RUN: brotli module unavailable'},
          open(f'{BASE}/reports/qa/weights_validity.json', 'w'), indent=1)
sums = {}
for root, _, fs in os.walk(f'{BASE}/fonts'):
    for fn in sorted(fs):
        if fn.endswith(('.ttf', '.woff')) and 'proto' not in root:
            pth = os.path.join(root, fn); sums[os.path.relpath(pth, BASE)] = hashlib.sha256(open(pth, 'rb').read()).hexdigest()
json.dump(sums, open(f'{BASE}/reports/build_reports/checksums.json', 'w'), indent=1)
print('exported', len(sums), 'files; weights valid:', [w for w in names if validity[w]['valid_for_release']])
