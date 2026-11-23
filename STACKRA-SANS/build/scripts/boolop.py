"""Overlap removal on Bezier contours (original implementation).

Method: split every segment at all mutual intersections, keep the sub-segments that
lie on the boundary of the nonzero-winding union (fill on exactly one side), chain them.
Inputs must be normalised: fills counter-clockwise, holes clockwise (see normalise()).
"""
import math
import numpy as np
from geom import *
from geom import _move_end


def normalise(fills, holes):
    out = []
    for c in fills:
        out.append(c if area(c) > 0 else rev_contour(c))
    for c in holes:
        out.append(c if area(c) < 0 else rev_contour(c))
    return out


def _bb(s):
    xs = [p[0] for p in s[1:]]; ys = [p[1] for p in s[1:]]
    return min(xs), min(ys), max(xs), max(ys)


def _bb_overlap(a, b, eps=0.01):
    return not (a[2] < b[0] - eps or b[2] < a[0] - eps or a[3] < b[1] - eps or b[3] < a[1] - eps)


def _flat(s, tol=0.04):
    if s[0] == 'L': return True
    p0, p1, p2, p3 = s[1:]
    d = unit(sub(p3, p0)); n = left_normal(d)
    return abs(dot(sub(p1, p0), n)) < tol and abs(dot(sub(p2, p0), n)) < tol


def _line_line(a, b):
    p, q = s0(a), s0(b); d = sub(s1(a), p); e = sub(s1(b), q)
    den = d[0] * e[1] - d[1] * e[0]
    out = []
    if abs(den) < 1e-9:
        # collinear overlap -> endpoint hits
        dd = dot(d, d)
        if dd < 1e-12: return out
        cr = abs((q[0] - p[0]) * d[1] - (q[1] - p[1]) * d[0]) / math.sqrt(dd)
        if cr > 0.02: return out
        ee = dot(e, e)
        for tb, pt in ((0.0, s0(b)), (1.0, s1(b))):
            ta = dot(sub(pt, p), d) / dd
            if 1e-6 < ta < 1 - 1e-6: out.append((ta, tb))
        for ta, pt in ((0.0, s0(a)), (1.0, s1(a))):
            tb = dot(sub(pt, q), e) / ee if ee > 1e-12 else -1
            if 1e-6 < tb < 1 - 1e-6: out.append((ta, tb))
        return out
    ta = ((q[0] - p[0]) * e[1] - (q[1] - p[1]) * e[0]) / den
    tb = ((q[0] - p[0]) * d[1] - (q[1] - p[1]) * d[0]) / den
    if -1e-9 <= ta <= 1 + 1e-9 and -1e-9 <= tb <= 1 + 1e-9:
        out.append((min(max(ta, 0), 1), min(max(tb, 0), 1)))
    return out


def intersections(a, b):
    if a[0] == 'L' and b[0] == 'L': return _line_line(a, b)
    hits = []

    def rec(A, a0, a1, B, b0, b1, depth):
        if len(hits) > 40: return
        if not _bb_overlap(_bb(A), _bb(B)): return
        if _flat(A) and _flat(B) and depth > 0:
            r = _line_line(L(s0(A), s1(A)), L(s0(B), s1(B)))
            for ta, tb in r:
                hits.append((a0 + ta * (a1 - a0), b0 + tb * (b1 - b0)))
            return
        if depth > 26:
            hits.append(((a0 + a1) / 2, (b0 + b1) / 2)); return
        am, bm = (a0 + a1) / 2, (b0 + b1) / 2
        A1, A2 = split(A, 0.5); B1, B2 = split(B, 0.5)
        for (x, xa, xb) in ((A1, a0, am), (A2, am, a1)):
            for (y, ya, yb) in ((B1, b0, bm), (B2, bm, b1)):
                rec(x, xa, xb, y, ya, yb, depth + 1)

    rec(as_cubic(a), 0.0, 1.0, as_cubic(b), 0.0, 1.0, 0)
    if len(hits) > 12: return []
    # refine by alternating closest-point Newton
    ref = []
    for ta, tb in hits:
        for _ in range(4):
            pa, pb = pt_at(a, ta), pt_at(b, tb)
            da, db = d_at(a, ta), d_at(b, tb)
            den = da[0] * db[1] - da[1] * db[0]
            if abs(den) < 1e-9: break
            r = sub(pb, pa)
            dta = (r[0] * db[1] - r[1] * db[0]) / den
            dtb = (r[0] * da[1] - r[1] * da[0]) / den
            ta = min(max(ta + dta, 0), 1); tb = min(max(tb + dtb, 0), 1)
        ref.append((ta, tb))
    ded = []
    for h in ref:
        if not any(abs(h[0] - g[0]) < 1e-3 and abs(h[1] - g[1]) < 1e-3 for g in ded): ded.append(h)
    return ded


def _winding(poly, px, py):
    x0 = poly[:, 0]; y0 = poly[:, 1]
    x1 = np.roll(x0, -1); y1 = np.roll(y0, -1)
    up = (y0 <= py) & (y1 > py)
    dn = (y0 > py) & (y1 <= py)
    cross = (x1 - x0) * (py - y0) - (px - x0) * (y1 - y0)
    return int(np.sum(up & (cross > 0)) - np.sum(dn & (cross < 0)))


def remove_overlaps(contours, eps=1.0, groups=None, rule=None):
    n = len(contours)
    groups = groups or [0] * n
    ngroups = max(groups) + 1
    rule = rule or (lambda ins: any(ins))
    polys = [np.array(flatten(c, 80)) for c in contours]
    orient = [1 if area(c) > 0 else -1 for c in contours]
    splits = {}  # (ci,si) -> list of (t, P)
    for ci in range(n):
        for cj in range(ci, n):
            for si, sa in enumerate(contours[ci]):
                ba = _bb(sa)
                for sj, sb in enumerate(contours[cj]):
                    if ci == cj:
                        m_ = len(contours[ci])
                        if sj <= si or (sj - si) % m_ <= 1 or (si - sj) % m_ <= 1: continue
                    if not _bb_overlap(ba, _bb(sb)): continue
                    for ta, tb in intersections(sa, sb):
                        P = pt_at(sa, ta)
                        splits.setdefault((ci, si), []).append((ta, P))
                        splits.setdefault((cj, sj), []).append((tb, P))
    pieces = []
    for ci, c in enumerate(contours):
        for si, sg in enumerate(c):
            lst = sorted(splits.get((ci, si), []), key=lambda x: x[0])
            cuts = []
            for t, P in lst:
                if t <= 1e-6:
                    cuts.append((0.0, s0(sg)))  # snap start
                elif t >= 1 - 1e-6:
                    cuts.append((1.0, s1(sg)))
                else:
                    if cuts and abs(cuts[-1][0] - t) < 1e-4: continue
                    cuts.append((t, P))
            ts = [(0.0, s0(sg))] + [c_ for c_ in cuts if 0 < c_[0] < 1] + [(1.0, s1(sg))]
            for k in range(len(ts) - 1):
                (ta, Pa), (tb, Pb) = ts[k], ts[k + 1]
                if tb - ta < 1e-6: continue
                piece = sub_seg(sg, ta, tb)
                if sum(norm(sub(piece[i+1], piece[i])) for i in range(1, len(piece)-1)) < 0.5: continue
                if ta > 0: piece = _move_end(piece, 0, Pa)
                if tb < 1: piece = _move_end(piece, 1, Pb)
                pieces.append(dict(seg=piece, ci=ci, si=si, t0=ta, t1=tb, orig=sg, rev=False))
    kept = []
    for pc in pieces:
        sg = pc['seg']
        M = pt_at(sg, 0.5); T = tangent_at(sg, 0.5); N = left_normal(T)
        wl = [0] * ngroups; wr = [0] * ngroups
        pl = (M[0] + N[0] * eps, M[1] + N[1] * eps); pr = (M[0] - N[0] * eps, M[1] - N[1] * eps)
        for cj in range(n):
            wl[groups[cj]] += _winding(polys[cj], *pl); wr[groups[cj]] += _winding(polys[cj], *pr)
        inl = bool(rule([w != 0 for w in wl])); inr = bool(rule([w != 0 for w in wr]))
        if inl == inr: continue
        if inr and not inl:
            pc['seg'] = reverse(sg); pc['rev'] = True
        kept.append(pc)
    # dedupe identical coincident pieces
    uniq = []
    for pc in kept:
        sg = pc['seg']; m = pt_at(sg, 0.5)
        dup = False
        for q in uniq:
            qs = q['seg']
            if norm(sub(s0(sg), s0(qs))) < 0.05 and norm(sub(s1(sg), s1(qs))) < 0.05 and norm(sub(m, pt_at(qs, 0.5))) < 0.05:
                dup = True; break
        if not dup: uniq.append(pc)
    # chain
    tol = 0.7
    used = [False] * len(uniq)
    loops = []
    for i in range(len(uniq)):
        if used[i]: continue
        loop = [uniq[i]]; used[i] = True
        start = s0(uniq[i]['seg']); cur = s1(uniq[i]['seg'])
        guard = 0
        while norm(sub(cur, start)) > tol and guard < 500:
            guard += 1
            cand = [j for j in range(len(uniq)) if not used[j] and norm(sub(s0(uniq[j]['seg']), cur)) < tol]
            if not cand: break
            if len(cand) > 1:
                # prefer the sharpest left turn so loops stay simple
                Tin = tangent_at(loop[-1]['seg'], 1.0)
                def turn(j):
                    Tj = tangent_at(uniq[j]['seg'], 0.0)
                    return math.atan2(Tin[0] * Tj[1] - Tin[1] * Tj[0], dot(Tin, Tj))
                cand.sort(key=turn, reverse=True)
            j = cand[0]; used[j] = True; loop.append(uniq[j]); cur = s1(uniq[j]['seg'])
        loops.append(loop)
    out = []
    for loop in loops:
        # merge contiguous pieces of the same original segment
        merged = []
        for pc in loop:
            if merged:
                m = merged[-1]
                if m['orig'] is pc['orig'] and m['rev'] == pc['rev']:
                    if not pc['rev'] and abs(m['t1'] - pc['t0']) < 1e-7:
                        m['t1'] = pc['t1']; m['seg'] = None; continue
                    if pc['rev'] and abs(pc['t1'] - m['t0']) < 1e-7:
                        m['t0'] = pc['t0']; m['seg'] = None; continue
            merged.append(dict(pc))
        # wrap-around merge
        if len(merged) > 1:
            a, b = merged[-1], merged[0]
            if a['orig'] is b['orig'] and a['rev'] == b['rev']:
                if not a['rev'] and abs(a['t1'] - b['t0']) < 1e-7:
                    b['t0'] = a['t0']; b['seg'] = None; merged.pop()
                elif a['rev'] and abs(b['t1'] - a['t0']) < 1e-7:
                    b['t1'] = a['t1']; b['seg'] = None; merged.pop()
        segs = []
        for m in merged:
            if m['seg'] is None:
                sg = sub_seg(m['orig'], m['t0'], m['t1'])
                if m['rev']: sg = reverse(sg)
            else:
                sg = m['seg']
            segs.append(sg)
        # snap continuity
        for k in range(len(segs)):
            nxt = segs[(k + 1) % len(segs)]
            if norm(sub(s1(segs[k]), s0(nxt))) > 1e-9:
                segs[k] = _move_end(segs[k], 1, s0(nxt))
        out.append(segs)
    return out


def simplify(contour):
    segs = [s for s in contour if norm(sub(s0(s), s1(s))) > 1e-6 or s[0] == 'C']
    res = []
    for s in segs:
        if res and s[0] == 'L' and res[-1][0] == 'L':
            a = unit(sub(s1(res[-1]), s0(res[-1]))); b = unit(sub(s1(s), s0(s)))
            if abs(a[0] * b[1] - a[1] * b[0]) < 1e-4 and dot(a, b) > 0:
                res[-1] = L(s0(res[-1]), s1(s)); continue
        res.append(s)
    if len(res) > 1 and res[0][0] == 'L' and res[-1][0] == 'L':
        a = unit(sub(s1(res[-1]), s0(res[-1]))); b = unit(sub(s1(res[0]), s0(res[0])))
        if abs(a[0] * b[1] - a[1] * b[0]) < 1e-4 and dot(a, b) > 0:
            res[0] = L(s0(res[-1]), s1(res[0])); res.pop()
    return res


def add_extrema(contour):
    out = []
    for s in contour:
        if s[0] == 'L': out.append(s); continue
        p0, p1, p2, p3 = s[1:]
        ts = []
        for ax in (0, 1):
            A = 3 * (-p0[ax] + 3 * p1[ax] - 3 * p2[ax] + p3[ax]); B = 6 * (p0[ax] - 2 * p1[ax] + p2[ax]); Cc = 3 * (p1[ax] - p0[ax])
            if abs(A) < 1e-9:
                if abs(B) > 1e-9: ts.append(-Cc / B)
            else:
                disc = B * B - 4 * A * Cc
                if disc >= 0:
                    r = math.sqrt(disc)
                    ts.extend([(-B + r) / (2 * A), (-B - r) / (2 * A)])
        keep = []
        for t in ts:
            if not (0.004 < t < 0.996): continue
            pt = pt_at(s, t)
            for ax in (0, 1):
                lo_, hi_ = min(p0[ax], p3[ax]), max(p0[ax], p3[ax])
                if pt[ax] > hi_ + 0.75 or pt[ax] < lo_ - 0.75: keep.append(t); break
        ts = sorted(set(round(t, 6) for t in keep))
        cur = s; prev = 0.0
        for t in ts:
            tt = (t - prev) / (1 - prev)
            a, b = split(cur, tt)
            out.append(a); cur = b; prev = t
        out.append(cur)
    return out


def finalize(contours):
    """Round to integer font units, keeping axis-aligned handles/lines exactly aligned."""
    res = []
    for c in contours:
        c = add_extrema(simplify(c))
        if len(c) < 2 or abs(area(c)) < 150: continue
        nodes = [s0(s) for s in c]
        start = (round(nodes[0][0]), round(nodes[0][1]))
        cur = start; segs = []
        for j, s in enumerate(c):
            end_raw = s1(s)
            end = (round(end_raw[0]), round(end_raw[1]))
            if j == len(c) - 1: end = start
            if s[0] == 'L':
                dx, dy = end_raw[0] - s0(s)[0], end_raw[1] - s0(s)[1]
                if abs(dx) < 0.06 and j < len(c) - 1: end = (cur[0], end[1])
                if abs(dy) < 0.06 and j < len(c) - 1: end = (end[0], cur[1])
                segs.append(L(cur, end))
            else:
                p0, p1, p2, p3 = s[1:]
                h1 = (round(p1[0]), round(p1[1])); h2 = (round(p2[0]), round(p2[1]))
                if abs(p1[1] - p0[1]) < 0.06: h1 = (h1[0], cur[1])
                if abs(p1[0] - p0[0]) < 0.06: h1 = (cur[0], h1[1])
                if abs(p2[1] - p3[1]) < 0.06: h2 = (h2[0], end[1])
                if abs(p2[0] - p3[0]) < 0.06: h2 = (end[0], h2[1])
                segs.append(C(cur, h1, h2, end))
            cur = end
        res.append(segs)
    return res


def build(fills, holes=()):
    """fills/holes: lists of contours -> clean, integer, overlap-free contours."""
    cs = remove_overlaps(normalise(fills, list(holes)))
    return finalize(cs)


def build_clip(fills, holes, clip_fills):
    """(union of fills minus holes) INTERSECT union(clip_fills)."""
    a = normalise(fills, list(holes)); b = normalise(clip_fills, [])
    cs = remove_overlaps(a + b, groups=[0] * len(a) + [1] * len(b), rule=lambda ins: ins[0] and ins[1])
    return finalize(cs)


def B(shapes, clip=None):
    """Union of shapes, each a contour (filled) or a tuple (outer, inner) = a ring with its own hole.
    clip: optional list of contours; result is intersected with their union."""
    conts, groups = [], []
    for gi, sh in enumerate(shapes):
        if isinstance(sh, tuple):
            outer, inner = sh
            if abs(area(inner)) > abs(area(outer)): outer, inner = inner, outer
            conts += normalise([outer], [inner]); groups += [gi, gi]
        else:
            conts += normalise([sh], []); groups.append(gi)
    ng = len(shapes)
    rule = lambda ins: any(ins)
    raw = list(conts); raw_groups = list(groups)
    if clip:
        for c in clip:
            conts += normalise([c], []); groups.append(ng)
        rule = lambda ins: any(ins[:-1]) and ins[-1]
    res = finalize(remove_overlaps(conts, groups=groups, rule=rule))
    if VALIDATE:
        QA_LOG.append(_validate(raw if not clip else conts, groups, rule, res))
    return res


VALIDATE = False
QA_LOG = []


def _validate(conts, groups, rule, res):
    """Raster check: result fill must equal rule(groupwise nonzero fills) of the inputs."""
    from raster import winding_grid
    allc = conts + res
    x0 = min(bbox([c])[0] for c in allc) - 6; y0 = min(bbox([c])[1] for c in allc) - 6
    x1 = max(bbox([c])[2] for c in allc) + 6; y1 = max(bbox([c])[3] for c in allc) + 6
    step = 5.0
    ng = max(groups) + 1
    ins = []
    for g in range(ng):
        cs = [c for c, gg in zip(conts, groups) if gg == g]
        ins.append(winding_grid(cs, x0, y0, x1, y1, step=step, n=24) != 0)
    stack = np.stack(ins, 0)
    ref = np.array([[bool(rule(list(stack[:, i, j]))) for j in range(stack.shape[2])] for i in range(stack.shape[1])])
    got = winding_grid(res, x0, y0, x1, y1, step=step, n=24) != 0
    mism = int((ref ^ got).sum()); tot = int(ref.sum())
    return (mism, tot)
