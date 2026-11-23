"""Coverage + measured-metrics QA of the variable font. (The pixel-XOR interpolation comparison that used to live
here was removed: renders of different font files are offset, so it was invalid. Use interp_test.py.)"""
import os, json
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
VF = f'{BASE}/fonts/variable/StackraSans-VF.ttf'
rep = {}
f = TTFont(VF)
rep['axes'] = [(a.axisTag, a.minValue, a.defaultValue, a.maxValue) for a in f['fvar'].axes]
rep['tables'] = sorted(f.keys())
cmap = f.getBestCmap()
glyf = f['glyf']
empty = [n for cp, n in cmap.items() if cp != 32 and glyf[n].numberOfContours == 0]
rep['coverage'] = {'mapped': len(cmap), 'mapped_to_notdef': [n for cp, n in cmap.items() if n == '.notdef'], 'mapped_but_empty': empty}
reg = instancer.instantiateVariableFont(TTFont(VF), {'wght': 400}, inplace=False)
g = reg['glyf']


def yb(n):
    gl = g[n]; gl.recalcBounds(g); return gl.yMin, gl.yMax


rep['metrics_regular'] = {'x_height(x)': yb('x')[1], 'cap(H)': yb('H')[1], 'ascender(l)': yb('l')[1], 'descender(p)': yb('p')[0],
                          'o_overshoot': yb('o'), 'O_overshoot': yb('O'), 'zero': yb('zero'), 'one': yb('one'), 'asc(d)': yb('d')[1]}
os.makedirs(f'{BASE}/reports/qa', exist_ok=True)
json.dump(rep, open(f'{BASE}/reports/qa/vf_qa.json', 'w'), indent=1, default=str)
print(json.dumps(rep, indent=1, default=str)[:2800])
