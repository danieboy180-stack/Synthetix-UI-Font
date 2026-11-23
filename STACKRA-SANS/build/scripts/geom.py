"""Stackra Sans geometry engine (original code, no third-party outlines).

Segments: ('L',p0,p1) | ('C',p0,p1,p2,p3).  Contour = list of segments (closed).
Glyph shapes are authored as skeleton strokes with per-node left/right widths;
overlaps are removed in boolop.py; orientation is fixed in finalize().
"""
import math
import numpy as np


def L(p0, p1): return ('L', tuple(p0), tuple(p1))
def C(p0, p1, p2, p3): return ('C', tuple(p0), tuple(p1), tuple(p2), tuple(p3))
def s0(s): return s[1]
def s1(s): return s[-1]
def add(a, b): return (a[0] + b[0], a[1] + b[1])
def sub(a, b): return (a[0] - b[0], a[1] - b[1])
def mul(a, k): return (a[0] * k, a[1] * k)
def dot(a, b): return a[0] * b[0] + a[1] * b[1]
def norm(a): return math.hypot(a[0], a[1])


def unit(a):
    n = norm(a)
    return (a[0] / n, a[1] / n) if n > 1e-12 else (1.0, 0.0)


def lerp(a, b, t): return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def rot(v, deg):
    r = math.radians(deg); c, s = math.cos(r), math.sin(r)
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)


def left_normal(d): return (-d[1], d[0])


def as_cubic(s):
    if s[0] == 'C': return s
    p0, p1 = s[1], s[2]
    return C(p0, lerp(p0, p1, 1 / 3), lerp(p0, p1, 2 / 3), p1)


def pt_at(s, t):
    if s[0] == 'L': return lerp(s[1], s[2], t)
    p0, p1, p2, p3 = s[1:]
    u = 1 - t
    return (u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
            u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1])


def d_at(s, t):
    if s[0] == 'L': return sub(s[2], s[1])
    p0, p1, p2, p3 = s[1:]
    u = 1 - t
    return (3 * u * u * (p1[0] - p0[0]) + 6 * u * t * (p2[0] - p1[0]) + 3 * t * t * (p3[0] - p2[0]),
            3 * u * u * (p1[1] - p0[1]) + 6 * u * t * (p2[1] - p1[1]) + 3 * t * t * (p3[1] - p2[1]))


def tangent_at(s, t):
    d = d_at(s, t)
    if norm(d) < 1e-9:
        d = d_at(s, 0.03 if t < 0.5 else 0.97)
    return unit(d)


def split(s, t):
    if s[0] == 'L':
        m = lerp(s[1], s[2], t); return L(s[1], m), L(m, s[2])
    p0, p1, p2, p3 = s[1:]
    a = lerp(p0, p1, t); b = lerp(p1, p2, t); c = lerp(p2, p3, t)
    d = lerp(a, b, t); e = lerp(b, c, t); f = lerp(d, e, t)
    return C(p0, a, d, f), C(f, e, c, p3)


def sub_seg(s, t0, t1):
    if t1 <= t0: return None
    r = split(s, t0)[1] if t0 > 0 else s
    if t1 >= 1: return r
    return split(r, (t1 - t0) / (1 - t0))[0]


def reverse(s):
    if s[0] == 'L': return L(s[2], s[1])
    return C(s[4], s[3], s[2], s[1])


def rev_contour(c): return [reverse(s) for s in reversed(c)]


def flatten_seg(s, n=32):
    if s[0] == 'L': return [s[1], s[2]]
    return [pt_at(s, i / n) for i in range(n + 1)]


def flatten(contour, n=48):
    pts = []
    for s in contour:
        pts.extend(flatten_seg(s, n)[:-1])
    return pts


def area(contour):
    p = flatten(contour, 24); a = 0.0
    for i in range(len(p)):
        x0, y0 = p[i]; x1, y1 = p[(i + 1) % len(p)]
        a += x0 * y1 - x1 * y0
    return a / 2


def bbox(contours):
    xs, ys = [], []
    for c in contours:
        for p in flatten(c, 48):
            xs.append(p[0]); ys.append(p[1])
    return min(xs), min(ys), max(xs), max(ys)


def translate(contours, dx, dy=0):
    return [[(s[0],) + tuple((p[0] + dx, p[1] + dy) for p in s[1:]) for s in c] for c in contours]


def transform(contours, fn):
    return [[(s[0],) + tuple(fn(p) for p in s[1:]) for s in c] for c in contours]


def arc(cx, cy, rx, ry, a0, a1, k=0.5523, tilt=0.0):
    """Elliptical arc as cubics split at multiples of 90 degrees (extrema get nodes).
    k = quarter-piece tension (0.5523 = true ellipse, larger = squarer/superelliptic)."""
    direction = 1 if a1 > a0 else -1
    cuts = [a0]; a = a0
    while True:
        nxt = (math.floor(a / 90 + 1e-9) + 1) * 90 if direction > 0 else (math.ceil(a / 90 - 1e-9) - 1) * 90
        if (direction > 0 and nxt >= a1 - 1e-9) or (direction < 0 and nxt <= a1 + 1e-9):
            cuts.append(a1); break
        cuts.append(nxt); a = nxt

    def P(th):
        r = math.radians(th)
        x, y = rot((rx * math.cos(r), ry * math.sin(r)), tilt)
        return (cx + x, cy + y)

    def D(th):
        r = math.radians(th)
        return rot((-rx * math.sin(r), ry * math.cos(r)), tilt)

    segs = []
    for i in range(len(cuts) - 1):
        ta, tb = cuts[i], cuts[i + 1]
        h = 4 / 3 * math.tan(math.radians(tb - ta) / 4)
        h *= 1 + (k / 0.5523 - 1) * min(1, abs(tb - ta) / 90)
        pa, pb = P(ta), P(tb); da, db = D(ta), D(tb)
        segs.append(C(pa, add(pa, mul(da, h)), sub(pb, mul(db, h)), pb))
    return segs


ERR_LOG = {'max': 0.0}


def _smooth(t): return t * t * (3 - 2 * t)


def _is_straight(seg):
    p0, p1, p2, p3 = seg[1:]
    d = unit(sub(p3, p0)); n = left_normal(d)
    return abs(dot(sub(p1, p0), n)) < 0.01 and abs(dot(sub(p2, p0), n)) < 0.01


def offset_seg(seg, w0, w1, side):
    """Offset of seg to `side` (+1 left of travel, -1 right), distance w0->w1 (smoothstep).
    One cubic out per cubic in (topology stays fixed across weights); end tangents preserved."""
    if seg[0] == 'L' or _is_straight(seg):
        p0, p3 = s0(seg), s1(seg)
        d = unit(sub(p3, p0)); n = left_normal(d)
        return L(add(p0, mul(n, side * w0)), add(p3, mul(n, side * w1)))
    N = 28
    ts = np.linspace(0, 1, N + 1)
    tgt = []
    for t in ts:
        t = float(t)
        n = left_normal(tangent_at(seg, t))
        w = w0 + (w1 - w0) * _smooth(t)
        c = pt_at(seg, t)
        tgt.append((c[0] + side * n[0] * w, c[1] + side * n[1] * w))
    tgt = np.array(tgt)
    P0, P3 = tgt[0], tgt[-1]
    u0 = np.array(tangent_at(seg, 0.0)); u1 = np.array(tangent_at(seg, 1.0))
    tp = ts.copy(); err = 0.0
    dense_t = np.linspace(0, 1, 400)
    for _ in range(3):
        b0 = (1 - tp)**3; b1 = 3 * (1 - tp)**2 * tp; b2 = 3 * (1 - tp) * tp**2; b3 = tp**3
        base = np.outer(b0 + b1, P0) + np.outer(b2 + b3, P3)
        r = tgt - base
        A1 = np.outer(b1, u0); A2 = -np.outer(b2, u1)
        M = np.array([[np.sum(A1 * A1), np.sum(A1 * A2)], [np.sum(A1 * A2), np.sum(A2 * A2)]])
        rhs = np.array([np.sum(A1 * r), np.sum(A2 * r)])
        try:
            al, be = np.linalg.solve(M, rhs)
        except np.linalg.LinAlgError:
            al = be = norm(sub(tuple(P3), tuple(P0))) / 3
        al = max(al, 1.0); be = max(be, 1.0)
        Q1 = P0 + al * u0; Q2 = P3 - be * u1
        bb0 = (1 - dense_t)**3; bb1 = 3 * (1 - dense_t)**2 * dense_t; bb2 = 3 * (1 - dense_t) * dense_t**2; bb3 = dense_t**3
        dense = np.outer(bb0, P0) + np.outer(bb1, Q1) + np.outer(bb2, Q2) + np.outer(bb3, P3)
        d2 = ((tgt[:, None, :] - dense[None, :, :])**2).sum(-1)
        tp = dense_t[d2.argmin(1)].copy(); tp[0] = 0; tp[-1] = 1
        err = math.sqrt(d2.min(1).max())
    ERR_LOG['max'] = max(ERR_LOG['max'], err)
    return C(tuple(P0), tuple(Q1), tuple(Q2), tuple(P3))


def line_isect(p, d, q, e):
    den = d[0] * e[1] - d[1] * e[0]
    if abs(den) < 1e-9: return None
    t = ((q[0] - p[0]) * e[1] - (q[1] - p[1]) * e[0]) / den
    return (p[0] + d[0] * t, p[1] + d[1] * t)


def _move_end(seg, which, newp):
    """Move first/last point of seg to newp along its tangent line, shifting the adjacent handle equally."""
    if seg[0] == 'L':
        return L(newp, seg[2]) if which == 0 else L(seg[1], newp)
    p0, p1, p2, p3 = seg[1:]
    if which == 0:
        return C(newp, add(p1, sub(newp, p0)), p2, p3)
    return C(p0, p1, add(p2, sub(newp, p3)), newp)


def Hcut(y): return ((0.0, y), 0.0)
def Vcut(x): return ((x, 0.0), 90.0)
def Acut(p, ang): return (p, ang)


def _chain(arr, closed=False):
    k = len(arr); res = []
    for j in range(k):
        res.append(arr[j])
        if j < k - 1 or closed:
            a, b = s1(arr[j]), s0(arr[(j + 1) % k])
            if norm(sub(a, b)) > 0.01: res.append(L(a, b))
    return res


def _wio(spec):
    if isinstance(spec[0], tuple): return spec[0], spec[1]
    return spec, spec


def stroke(segs, widths, cut0=None, cut1=None, closed=False, miter=3.2):
    """Variable-width stroke along a centerline.
    widths[i] = (left, right) offsets at node i, or ((l,r)_in, (l,r)_out) where the incoming and
    outgoing segment differ (corners). len = len(segs)+1 (len(segs) if closed).
    Returns contours (open -> 1 contour; closed -> outer+inner loops)."""
    n = len(segs)
    Win, Wout = [], []
    for w in widths:
        a, b = _wio(w); Win.append(a); Wout.append(b)
    if closed:
        Win.append(Win[0]); Wout.append(Wout[0])
    left = [offset_seg(sg, Wout[i][0], Win[i + 1][0], +1) for i, sg in enumerate(segs)]
    right = [offset_seg(sg, Wout[i][1], Win[i + 1][1], -1) for i, sg in enumerate(segs)]
    for i in (range(n) if closed else range(1, n)):
        a = segs[i - 1]; b = segs[i % n]
        ta = tangent_at(a, 1.0); tb = tangent_at(b, 0.0)
        ang = math.degrees(math.atan2(ta[0] * tb[1] - ta[1] * tb[0], dot(ta, tb)))
        if abs(ang) < 3: continue
        P = s1(a)
        for side, arr, ix in ((+1, left, 0), (-1, right, 1)):
            wa = Win[i][ix]; wb = Wout[i % n][ix]
            pa = add(P, mul(left_normal(ta), side * wa)); pb = add(P, mul(left_normal(tb), side * wb))
            M = line_isect(pa, ta, pb, tb)
            if M is not None and norm(sub(M, P)) <= miter * max(wa, wb, 1):
                arr[i - 1] = _move_end(arr[i - 1], 1, M)
                arr[i % n] = _move_end(arr[i % n], 0, M)

    def apply_cut(idx, which, spec, arr):
        Q, ang = spec
        sg = arr[idx]
        P = s0(sg) if which == 0 else s1(sg)
        tg = tangent_at(sg, 0.0 if which == 0 else 1.0)
        M = line_isect(P, tg, Q, (math.cos(math.radians(ang)), math.sin(math.radians(ang))))
        if M is not None: arr[idx] = _move_end(sg, which, M)

    if closed:
        return [_chain(left, True), _chain(right, True)]
    if cut0:
        apply_cut(0, 0, cut0, left); apply_cut(0, 0, cut0, right)
    if cut1:
        apply_cut(n - 1, 1, cut1, left); apply_cut(n - 1, 1, cut1, right)
    contour = _chain(left)
    contour.append(L(s1(left[-1]), s1(right[-1])))
    contour.extend(rev_contour(_chain(right)))
    contour.append(L(s0(right[0]), s0(left[0])))
    return [contour]


def rect(x0, y0, x1, y1):
    return [L((x0, y0), (x1, y0)), L((x1, y0), (x1, y1)), L((x1, y1), (x0, y1)), L((x0, y1), (x0, y0))]


def poly(pts):
    n = len(pts)
    return [L(pts[i], pts[(i + 1) % n]) for i in range(n)]


def ring(cx, cy, rxo, ryo, v, h, k=0.56, tilt=0.0, kin=None):
    """Closed round form: outer ellipse + inner ellipse (inner may be rotated to tilt the stress axis)."""
    return [arc(cx, cy, rxo, ryo, 0, 360, k), arc(cx, cy, rxo - v, ryo - h, 0, -360, kin or k, tilt)]
