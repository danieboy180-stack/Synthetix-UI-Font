"""Make glyph masters point-compatible: insert nodes (shape-preserving splits) until counts match,
align start points, unify segment types. Returns None if contour topology differs."""
import math
from geom import *
from geom import split


def _dist_seg(s, p, n=24):
    best = (1e18, 0.0)
    for i in range(n + 1):
        t = i / n; q = pt_at(s, t); d = (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2
        if d < best[0]: best = (d, t)
    return best


def insert_nodes(S, R):
    S = list(S)
    while len(S) < len(R):
        Sn = [s0(x) for x in S]; Rn = [s0(x) for x in R]
        pairs = sorted(((math.dist(r, s), i, j) for i, r in enumerate(Rn) for j, s in enumerate(Sn)))
        ra, sa = set(), set()
        for d, i, j in pairs:
            if i in ra or j in sa: continue
            ra.add(i); sa.add(j)
        un = [i for i in range(len(Rn)) if i not in ra]
        p = Rn[un[0]] if un else Rn[-1]
        best = min(((_dist_seg(sg, p), k) for k, sg in enumerate(S)), key=lambda x: x[0][0])
        (d2, t), k = best
        t = min(max(t, 0.15), 0.85)
        a, b = split(S[k], t)
        S[k:k + 1] = [a, b]
    return S


def align(S, R):
    n = len(S); best = None
    for k in range(n):
        cost = sum(math.dist(s0(S[(i + k) % n]), s0(R[i])) ** 2 for i in range(n))
        if best is None or cost < best[0]: best = (cost, k)
    k = best[1]
    return S[k:] + S[:k]


def harmonize(masters):
    """masters: list (per master) of contour lists. Returns harmonized copy or None."""
    if len({len(m) for m in masters}) != 1: return None
    out = [[] for _ in masters]
    for ci in range(len(masters[0])):
        segs = [m[ci] for m in masters]
        ref_i = max(range(len(segs)), key=lambda i: len(segs[i]))
        R = segs[ref_i]
        segs = [insert_nodes(s, R) if len(s) < len(R) else s for s in segs]
        if len({len(s) for s in segs}) != 1: return None
        segs = [align(s, segs[ref_i]) if i != ref_i else s for i, s in enumerate(segs)]
        for i in range(len(R)):
            kinds = {s[i][0] for s in segs}
            if len(kinds) > 1:
                for s in segs: s[i] = as_cubic(s[i])
        for mi, s in enumerate(segs): out[mi].append(s)
    return out
