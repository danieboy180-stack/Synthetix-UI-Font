import sys, json
import fontbuild
from geom import s0, bbox


def canon(cs):
    """Canonical ordering: contours sorted by bbox, each started at its lowest-then-leftmost node."""
    out = []
    for c in cs:
        nodes = [s0(s) for s in c]
        i = min(range(len(nodes)), key=lambda k: (round(nodes[k][1]), round(nodes[k][0])))
        out.append(c[i:] + c[:i])
    out.sort(key=lambda c: (round(bbox([c])[1]), round(bbox([c])[0]), round(bbox([c])[3])))
    return out


def sig(cs): return [[s[0] for s in c] for c in cs]


if __name__ == '__main__':
    ws = [300, 400, 700] if len(sys.argv) < 2 else [int(x) for x in sys.argv[1:]]
    M = {}
    for w in ws:
        c, g, log = fontbuild.make_master('A', w); M[w] = g
        for k, v in g.items(): v['contours'] = canon(v['contours'])
    bad = {}
    for n in M[ws[0]]:
        ref = sig(M[ws[0]][n]['contours'])
        for w in ws[1:]:
            if sig(M[w][n]['contours']) != ref: bad.setdefault(n, []).append(w)
    print('weights', ws, 'glyphs', len(M[ws[0]]), 'incompatible', len(bad))
    for n, v in bad.items():
        print(n, v, [(w, [len(c) for c in M[w][n]['contours']]) for w in ws])
