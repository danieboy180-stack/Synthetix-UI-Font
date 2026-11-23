"""Stackra Sans - uppercase, figures, punctuation and remaining lowercase."""
import math
from geom import *
from boolop import B, finalize
from glyphs_lc import *


def dstroke(c, p0, p1, tw=None, cut0=None, cut1=None, taper=1.0):
    """Diagonal stroke whose HORIZONTAL thickness is tw (default c.dg)."""
    tw = tw or c.dg
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    n = math.hypot(dx, dy)
    pt = tw * abs(dy) / n if abs(dy) > 1e-6 else c.h
    return stroke([L(p0, p1)], [(pt / 2,) * 2, (pt / 2 * taper,) * 2], cut0=cut0, cut1=cut1)


def zig(c, pts, apex_w=None, ytop=None, ybot=None):
    """Zig-zag of diagonal strokes through vertices pts=[(x,y)...]; interior vertices get flat apexes."""
    aw = apex_w or c.dg * 1.08
    d = (aw - c.dg) / 2
    out = []
    n = len(pts)
    for i in range(n - 1):
        a = list(pts[i]); b = list(pts[i + 1])
        if i > 0:
            a[0] = pts[i][0] + (d if pts[i + 1][0] > pts[i][0] else -d)
        if i + 1 < n - 1:
            b[0] = pts[i + 1][0] + (-d if pts[i + 1][0] > pts[i][0] else d)
        out += dstroke(c, tuple(a), tuple(b), cut0=Hcut(a[1]), cut1=Hcut(b[1]))
    return out


def bowl_path(c, xs, ytc, ybc, xrc, rx_e=None):
    """Centerline of an open bowl: bar - half ellipse - bar, starting/ending at stem centre xs."""
    hb, v = c.hb, c.v
    ry = (ytc - ybc) / 2; cy = (ytc + ybc) / 2
    rx = rx_e if rx_e is not None else min(xrc - xs - 40, 0.9 * ry + 20)
    xe = xrc - rx
    top = L((xs, ytc), (xe, ytc))
    ar = arc(xe, cy, rx, ry, 90, -90, c.k)
    bot = L((xe, ybc), (xs, ybc))
    segs = [top] + ar + [bot]
    ws = [(hb / 2,) * 2, (hb / 2,) * 2, (v / 2,) * 2, (hb / 2,) * 2, (hb / 2,) * 2]
    return stroke(segs, ws)


# ============================================================ remaining lowercase
def g_k(c):
    v, XH = c.v, c.XH
    W = 468 + 0.2 * v
    arm = dstroke(c, (v * 0.55, 0.37 * XH), (W - c.dg / 2, XH), cut1=Hcut(XH))
    m = pt_at(L((v * 0.55, 0.37 * XH), (W - c.dg / 2, XH)), 0.50)
    leg = dstroke(c, (m[0] - 6, m[1] - 4), (W - c.dg / 2, 0), cut1=Hcut(0))
    return B([rect(0, 0, v, c.ASC)] + arm + leg)


def g_v(c):
    W = 478 + 0.15 * c.v
    return B(zig(c, [(c.dg / 2, c.XH), (W / 2, 0), (W - c.dg / 2, c.XH)]))


def g_w(c):
    W = 726 + 0.2 * c.v; dg = c.dg
    return B(zig(c, [(dg / 2, c.XH), (W * 0.25 + dg * 0.05, 0), (W / 2, c.XH), (W * 0.75 - dg * 0.05, 0), (W - dg / 2, c.XH)]))


def g_x(c):
    W = 474 + 0.15 * c.v; dg = c.dg
    return B(dstroke(c, (dg / 2, c.XH), (W - dg / 2, 0), cut0=Hcut(c.XH), cut1=Hcut(0)) +
             dstroke(c, (W - dg / 2, c.XH), (dg / 2, 0), cut0=Hcut(c.XH), cut1=Hcut(0), tw=dg * 0.96))


def g_y(c):
    W = 478 + 0.15 * c.v; dg = c.dg; XH = c.XH
    p0 = (W - dg / 2, XH); p1 = (0.16 * W + dg / 2, c.DESC)
    t0 = XH / (XH - c.DESC); xb = p0[0] + t0 * (p1[0] - p0[0])
    r = dstroke(c, p0, p1, cut0=Hcut(XH), cut1=Hcut(c.DESC))
    l = dstroke(c, (dg / 2, XH), (xb - dg * 0.05, 0), cut0=Hcut(XH), cut1=Hcut(0))
    return B(r + l)


def g_z(c):
    W = 440 + 0.15 * c.v; hb, XH = c.hb, c.XH; dg = c.dg
    d = dstroke(c, (W - dg * 0.45, XH - hb / 2), (dg * 0.45, hb / 2), tw=dg * 0.92,
                cut0=Hcut(XH - hb * 0.45), cut1=Hcut(hb * 0.45))
    return B([rect(0, XH - hb, W, XH), rect(0, 0, W, hb)] + d)


def g_f(c):
    v, h, hb, XH = c.v, c.h, c.hb, c.XH
    xs = 90 + 0.1 * v
    rxf, ryf = 112, 104
    cy_f = c.ASC + 6 - h / 2 - ryf
    segs, ws = sk_arc(c, xs + rxf, cy_f, rxf, ryf, 180, 62, 1.0, 0.95)
    ws[0] = (v / 2, v / 2)
    endp = pt_on_ellipse(xs + rxf, cy_f, rxf, ryf, 62)
    sg, w = cat(line_path((xs, 0), (xs, cy_f), v / 2, v / 2), (segs, ws))
    st = stroke(sg, w, cut0=Hcut(0), cut1=tcut(c, endp))
    bar = rect(xs - v / 2 - 62, XH - hb, xs + v / 2 + 118, XH)
    return B(st + [bar])


# l carries a tail so I / l / 1 separate in the default design (measured Jaccard I~l = 1.00 before the tail)
def g_l(c):
    v, h = c.v, c.h
    xs = v / 2
    rxh, ryh = 104, 112
    cy_h = -c.OS + h / 2 + ryh
    segs, ws = sk_arc(c, xs + rxh, cy_h, rxh, ryh, 180, 312, 1.0, 0.92)
    ws[0] = (v / 2, v / 2)
    endp = pt_on_ellipse(xs + rxh, cy_h, rxh, ryh, 312)
    sg, w = cat(line_path((xs, c.ASC), (xs, cy_h), v / 2, v / 2), (segs, ws))
    return B(stroke(sg, w, cut0=Hcut(c.ASC), cut1=tcut(c, endp)))


# ============================================================ uppercase
def g_I(c): return B([rect(0, 0, c.v, c.CAP)])


def g_H(c):
    v, hb, CAP = c.v, c.hb, c.CAP
    W = 560 + 0.35 * v
    return B([rect(0, 0, v, CAP), rect(W - v, 0, W, CAP), rect(v * 0.5, CAP * 0.515 - hb / 2, W - v * 0.5, CAP * 0.515 + hb / 2)])


def g_E(c):
    v, hb, CAP = c.v, c.hb, c.CAP
    W = 462 + 0.25 * v
    return B([rect(0, 0, v, CAP), rect(0, CAP - hb, W, CAP), rect(0, 0, W, hb * 1.02),
              rect(0, CAP * 0.52 - hb / 2, W * 0.90, CAP * 0.52 + hb / 2)])


def g_F(c):
    v, hb, CAP = c.v, c.hb, c.CAP
    W = 446 + 0.25 * v
    return B([rect(0, 0, v, CAP), rect(0, CAP - hb, W, CAP), rect(0, CAP * 0.52 - hb / 2, W * 0.88, CAP * 0.52 + hb / 2)])


def g_L(c):
    v, hb, CAP = c.v, c.hb, c.CAP
    W = 424 + 0.25 * v
    return B([rect(0, 0, v, CAP), rect(0, 0, W, hb * 1.02)])


def g_T(c):
    v, hb, CAP = c.v, c.hb, c.CAP
    W = 520 + 0.25 * v
    return B([rect(0, CAP - hb, W, CAP), rect(W / 2 - v / 2, 0, W / 2 + v / 2, CAP)])


def g_O(c):
    rx = (722 + 0.3 * c.v) / 2; ry = c.CAP / 2 + c.OS
    return B([ring_item(c, rx, c.CAP / 2, rx, ry)])


def g_Q(c):
    rx = (722 + 0.3 * c.v) / 2; ry = c.CAP / 2 + c.OS; W = 2 * rx
    tail = dstroke(c, (W * 0.60, 0.22 * c.CAP), (W * 0.90, -66), tw=c.dg * 1.02, cut1=Hcut(-66))
    return B([ring_item(c, rx, c.CAP / 2, rx, ry)] + tail)


def g_C(c):
    rx0 = (700 + 0.3 * c.v) / 2; ry0 = c.CAP / 2 + c.OS
    cx, cy = rx0, c.CAP / 2
    segs, ws = sk_arc(c, cx, cy, rx0 - c.v / 2, ry0 - c.h / 2, 40, 320, 0.95, 0.95)
    a = pt_on_ellipse(cx, cy, rx0 - c.v / 2, ry0 - c.h / 2, 40); b = pt_on_ellipse(cx, cy, rx0 - c.v / 2, ry0 - c.h / 2, 320)
    return B(stroke(segs, ws, cut0=tcut(c, a), cut1=tcut(c, b)))


def g_G(c):
    v, hb = c.v, c.hb
    rx0 = (716 + 0.3 * v) / 2; ry0 = c.CAP / 2 + c.OS
    cx, cy = rx0, c.CAP / 2
    rxc, ryc = rx0 - v / 2, ry0 - c.h / 2
    ybar = cy - 6
    phi1 = math.degrees(math.asin((ybar - cy) / ryc)) + 360
    segs, ws = sk_arc(c, cx, cy, rxc, ryc, 38, phi1, 0.95, 1.0)
    endp = pt_on_ellipse(cx, cy, rxc, ryc, phi1)
    a = pt_on_ellipse(cx, cy, rxc, ryc, 38)
    bar = line_path(endp, (0.52 * 2 * rx0, endp[1]), hb / 2, hb / 2)
    sg, w = cat((segs, ws), bar)
    w[-2] = ((v / 2, v / 2), (hb / 2, hb / 2))
    return B(stroke(sg, w, cut0=tcut(c, a)))


def g_A(c):
    v, hb, CAP, dg = c.v, c.hb, c.CAP, c.dg
    W = 692 + 0.2 * v
    aw = dg * 1.12
    lt = (W / 2 - aw / 2 + dg / 2, CAP); rt = (W / 2 + aw / 2 - dg / 2, CAP)
    l = dstroke(c, (dg / 2, 0), lt, cut0=Hcut(0), cut1=Hcut(CAP))
    r = dstroke(c, (W - dg / 2, 0), rt, cut0=Hcut(0), cut1=Hcut(CAP))
    yb = 0.235 * CAP
    def xat(p0, p1, y): return p0[0] + (p1[0] - p0[0]) * (y - p0[1]) / (p1[1] - p0[1])
    xl = xat((dg / 2, 0), lt, yb); xr = xat((W - dg / 2, 0), rt, yb)
    return B(l + r + [rect(xl, yb - hb * 0.5, xr, yb + hb * 0.5)])


def g_V(c):
    W = 672 + 0.2 * c.v
    return B(zig(c, [(c.dg / 2, c.CAP), (W / 2, 0), (W - c.dg / 2, c.CAP)]))


def g_W(c):
    W = 960 + 0.2 * c.v; dg = c.dg
    return B(zig(c, [(dg / 2, c.CAP), (W * 0.25 + dg * 0.05, 0), (W / 2, c.CAP), (W * 0.75 - dg * 0.05, 0), (W - dg / 2, c.CAP)]))


def g_X(c):
    W = 668 + 0.2 * c.v; dg = c.dg
    return B(dstroke(c, (dg / 2, c.CAP), (W - dg / 2, 0), cut0=Hcut(c.CAP), cut1=Hcut(0)) +
             dstroke(c, (W - dg / 2, c.CAP), (dg / 2, 0), cut0=Hcut(c.CAP), cut1=Hcut(0), tw=dg * 0.96))


def g_Y(c):
    v, CAP, dg = c.v, c.CAP, c.dg
    W = 668 + 0.2 * v; ym = 0.40 * CAP
    l = dstroke(c, (dg / 2, CAP), (W / 2, ym - 34), tw=dg * 0.86, cut0=Hcut(CAP), cut1=Hcut(ym - 34))
    r = dstroke(c, (W - dg / 2, CAP), (W / 2, ym - 20), tw=dg * 0.86, cut0=Hcut(CAP), cut1=Hcut(ym - 20))
    return B(l + r + [rect(W / 2 - v / 2, 0, W / 2 + v / 2, ym + 40)])


def g_Z(c):
    W = 560 + 0.2 * c.v; hb, CAP, dg = c.hb, c.CAP, c.dg
    d = dstroke(c, (W - dg * 0.40, CAP - hb / 2), (dg * 0.40, hb / 2), tw=dg * 0.94,
                cut0=Hcut(CAP - hb * 0.45), cut1=Hcut(hb * 0.45))
    return B([rect(0, CAP - hb, W, CAP), rect(0, 0, W, hb)] + d)


def g_N(c):
    v, CAP, dg = c.v, c.CAP, c.dg
    W = 630 + 0.3 * v
    d = dstroke(c, (dg / 2, CAP), (W - dg / 2, 0), cut0=Hcut(CAP), cut1=Hcut(0))
    return B([rect(0, 0, v, CAP), rect(W - v, 0, W, CAP)] + d)


def g_M(c):
    v, CAP, dg = c.v, c.CAP, c.dg
    W = 790 + 0.3 * v
    aw = dg * 1.1
    l = dstroke(c, (dg / 2, CAP), (W / 2 - aw / 2 + dg / 2, 0), cut0=Hcut(CAP), cut1=Hcut(0))
    r = dstroke(c, (W - dg / 2, CAP), (W / 2 + aw / 2 - dg / 2, 0), cut0=Hcut(CAP), cut1=Hcut(0))
    return B([rect(0, 0, v, CAP), rect(W - v, 0, W, CAP)] + l + r)


def g_K(c):
    v, CAP, dg = c.v, c.CAP, c.dg
    W = 600 + 0.2 * v
    p0 = (v * 0.55, 0.30 * CAP); p1 = (W - dg / 2, CAP)
    arm = dstroke(c, p0, p1, cut1=Hcut(CAP))
    m = pt_at(L(p0, p1), 0.50)
    leg = dstroke(c, (m[0] - 8, m[1] - 4), (W - dg / 2, 0), cut1=Hcut(0))
    return B([rect(0, 0, v, CAP)] + arm + leg)


def g_B(c):
    v, hb, CAP = c.v, c.hb, c.CAP
    W = 520 + 0.3 * v; ym = 0.545 * CAP
    up = bowl_path(c, v / 2, CAP - hb / 2, ym, W * 0.88 - v / 2 + 6, None)
    lo = bowl_path(c, v / 2, ym, hb / 2, W - v / 2, None)
    return B([rect(0, 0, v, CAP)] + up + lo)


def g_D(c):
    v, hb, CAP = c.v, c.hb, c.CAP
    W = 620 + 0.3 * v
    bw = bowl_path(c, v / 2, CAP - hb / 2, hb / 2, W - v / 2, rx_e=(W - v / 2) * 0.56)
    return B([rect(0, 0, v, CAP)] + bw)


def g_P(c):
    v, hb, CAP = c.v, c.hb, c.CAP
    W = 520 + 0.25 * v
    bw = bowl_path(c, v / 2, CAP - hb / 2, 0.40 * CAP + hb / 2, W - v / 2, None)
    return B([rect(0, 0, v, CAP)] + bw)


def g_R(c):
    v, hb, CAP, dg = c.v, c.hb, c.CAP, c.dg
    W = 540 + 0.25 * v; yb = 0.40 * CAP + hb / 2
    bw = bowl_path(c, v / 2, CAP - hb / 2, yb, W * 0.93 - v / 2, None)
    leg = dstroke(c, (W * 0.40, yb - hb * 0.3), (W - dg * 0.5, 0), cut1=Hcut(0), tw=dg * 1.02)
    return B([rect(0, 0, v, CAP)] + bw + leg)


def g_U(c):
    v, h, CAP = c.v, c.h, c.CAP
    W = 560 + 0.3 * v
    ryc = 250; ybend = -c.OS + h / 2 + ryc
    rxc = W / 2 - v / 2
    ar, wa = sk_arc(c, W / 2, ybend, rxc, ryc, 180, 360, 1.0, 1.0)
    wa[0] = (v / 2, v / 2); wa[-1] = (v / 2, v / 2)
    l = line_path((v / 2, CAP), (v / 2, ybend), v / 2, v / 2)
    r = line_path((W - v / 2, ybend), (W - v / 2, CAP), v / 2, v / 2)
    sg, w = cat(l, (ar, wa), r)
    return B(stroke(sg, w, cut0=Hcut(CAP), cut1=Hcut(CAP)))


def g_J(c):
    v, h, CAP = c.v, c.h, c.CAP
    W = 400 + 0.2 * v
    xs = W - v / 2; ryt = 150; rxt = 125
    cy_t = -c.OS + h / 2 + ryt
    segs, ws = sk_arc(c, xs - rxt, cy_t, rxt, ryt, 0, -150, 1.0, 0.95)
    ws[0] = (v / 2, v / 2)
    endp = pt_on_ellipse(xs - rxt, cy_t, rxt, ryt, -150)
    sg, w = cat(line_path((xs, CAP), (xs, cy_t), v / 2, v / 2), (segs, ws))
    return B(stroke(sg, w, cut0=Hcut(CAP), cut1=tcut(c, endp)))


def g_S(c): return B(s_curve(c, 520 + 0.2 * c.v, 0, c.CAP))


# ============================================================ figures
FW = lambda c: 520 + 0.30 * c.v          # tabular figure ink width (design basis)


def g_zero(c):
    rx = FW(c) / 2; ry = c.CAP / 2 + c.OS
    return B([ring_item(c, rx, c.CAP / 2, rx, ry)])


def g_one(c):
    v, CAP, h = c.v, c.CAP, c.h
    xs = 150 + 0.1 * v
    fl = stroke([L((xs + 6, CAP - 36), (14, CAP - 168))], [(h * 0.43,) * 2, (h * 0.43,) * 2], cut1=Vcut(14))
    return B([rect(xs, 0, xs + v, CAP)] + fl)


def g_two(c):
    v, h, hb, CAP, dg = c.v, c.h, c.hb, c.CAP, c.dg
    W = FW(c) - 20
    rxc = W / 2 - v / 2; ryc = 0.5 * 360 - h / 2
    cx = W / 2; cy = CAP + c.OS - h / 2 - ryc
    segs, ws = sk_arc(c, cx, cy, rxc, ryc, 158, -18, 0.95, 1.0)
    # arc ends on the right side heading down-left; continue with a diagonal to bottom-left
    endp = pt_on_ellipse(cx, cy, rxc, ryc, -18)
    P = (0.065 * W + dg * 0.35, hb * 0.9)
    dirv = unit(sub(P, endp))
    bend = C(endp, add(endp, mul(unit(d_at(segs[-1], 1.0)), 90)), sub((endp[0] + (P[0] - endp[0]) * 0.55, endp[1] + (P[1] - endp[1]) * 0.55), mul(dirv, 60)), (endp[0] + (P[0] - endp[0]) * 0.55, endp[1] + (P[1] - endp[1]) * 0.55))
    mid = bend[-1]
    diag = L(mid, P)
    a = pt_on_ellipse(cx, cy, rxc, ryc, 158)
    sg = list(segs) + [bend, diag]
    w = ws[:-1] + [(v * 0.45,) * 2, (v * 0.47,) * 2, (hb / 2,) * 2]
    return B(stroke(sg, w, cut0=tcut(c, a)) + [rect(P[0] - dg * 0.40, 0, W, hb * 1.02)])


def g_three(c):
    v, h, hb, CAP = c.v, c.h, c.hb, c.CAP
    W = FW(c) - 24
    ym = 0.545 * CAP
    rxc = W / 2 - v / 2 - 24
    cx = W / 2 - 14
    cyu = ym + (CAP + c.OS - h / 2 - ym) / 2; ryu = (CAP + c.OS - h / 2 - ym) / 2
    segs_u, ws_u = sk_arc(c, cx, cyu, rxc * 0.94, ryu, 156, -90, 0.95, 1.0)
    cyl = (ym + (-c.OS + h / 2)) / 2; ryl = (ym - (-c.OS + h / 2)) / 2
    segs_l, ws_l = sk_arc(c, cx + 8, cyl, rxc * 1.04, ryl, 90, -156, 1.0, 0.95)
    a = pt_on_ellipse(cx, cyu, rxc * 0.94, ryu, 156); b = pt_on_ellipse(cx + 8, cyl, rxc * 1.04, ryl, -156)
    up = stroke(segs_u, ws_u, cut0=tcut(c, a), cut1=Vcut(cx - 4))
    lo = stroke(segs_l, ws_l, cut0=Vcut(cx + 12), cut1=tcut(c, b))
    return B(up + lo)


def g_four(c):
    v, hb, CAP, dg = c.v, c.hb, c.CAP, c.dg
    W = FW(c) + 20; xs = W * 0.70
    yb = 0.255 * CAP
    d = dstroke(c, (xs - v * 0.1, CAP), (14 + dg * 0.45, yb + hb * 0.2), tw=dg * 0.98, cut0=Hcut(CAP))
    return B([rect(xs, 0, xs + v, CAP), rect(0, yb - hb / 2, W, yb + hb / 2)] + d)


def g_five(c):
    v, h, hb, CAP = c.v, c.h, c.hb, c.CAP
    W = FW(c) - 20
    xs = 0.10 * W + v / 2
    yj = 0.52 * CAP
    bar = rect(xs - v / 2, CAP - hb, W * 0.93, CAP)
    stem = rect(xs - v / 2, yj - 10, xs + v / 2, CAP)
    cx = W / 2 - 8; cyb = (0.64 * CAP + (-c.OS + h / 2)) / 2; ryb = (0.64 * CAP - (-c.OS + h / 2)) / 2
    rxb = W / 2 - v / 2 - 4
    ar, wa = sk_arc(c, cx, cyb, rxb, ryb, 140, -156, 1.0, 0.95)
    b = pt_on_ellipse(cx, cyb, rxb, ryb, -156)
    bowl = stroke(ar, wa, cut0=None, cut1=tcut(c, b))
    return B([bar, stem] + bowl)


def g_six(c):
    v, h, CAP = c.v, c.h, c.CAP
    W = FW(c)
    dvv = max(0.0, (v - 84) / 46.0)
    ryo = 0.322 * CAP * 1.0 + c.OS + 20 - 14 * dvv; cyo = ryo - c.OS
    rx = W / 2
    bowl = ring_item(c, rx, cyo, rx, ryo)
    xl = v / 2
    P0 = (xl, cyo); T = (W * 0.50, CAP + c.OS - h / 2); E = (W * (0.90 - 0.03 * dvv), (0.80 + 0.045 * dvv) * CAP)
    s1_ = C(P0, (P0[0], P0[1] + 0.55 * (T[1] - P0[1])), (T[0] - 0.52 * (T[0] - P0[0]), T[1]), T)
    s2_ = C(T, (T[0] + 0.30 * (E[0] - T[0]), T[1]), (E[0] - 20, E[1] + 70), E)
    arm = stroke([s1_, s2_], [(v / 2,) * 2, (h / 2,) * 2, (h * 0.46,) * 2], cut1=tcut(c, E))
    return B(arm + [bowl])


# nine rotates the BUILT six (the counter must keep its orientation, so no re-union)
def g_nine(c):
    cs = g_six(c); W = FW(c)
    return finalize(transform(cs, lambda p: (round(W) - p[0], c.CAP - p[1])))


def g_seven(c):
    v, hb, CAP, dg = c.v, c.hb, c.CAP, c.dg
    W = FW(c) - 6
    d = dstroke(c, (W - dg * 0.55, CAP - hb / 2), (W * 0.28 + dg * 0.2, 0), tw=dg * 0.98, cut0=Hcut(CAP - hb * 0.45), cut1=Hcut(0))
    return B([rect(0, CAP - hb, W, CAP)] + d)


def g_eight(c):
    v, h, CAP = c.v, c.h, c.CAP
    W = FW(c) - 10
    ym = 0.54 * CAP
    ryu = (CAP + c.OS - (ym - 0.0)) / 2 + 8; cyu = CAP + c.OS - ryu
    ryl = (ym + c.OS) / 2 + 22; cyl = -c.OS + ryl
    rxu = W * 0.455; rxl = W / 2
    up = ring_item(c, W / 2, cyu, rxu, ryu, v * 0.92, h * 0.96)
    lo = ring_item(c, W / 2, cyl, rxl, ryl, v * 0.96, h * 0.98)
    return B([up, lo])


GLYPH_FIGS = {'zero': g_zero, 'one': g_one, 'two': g_two, 'three': g_three, 'four': g_four,
              'five': g_five, 'six': g_six, 'seven': g_seven, 'eight': g_eight, 'nine': g_nine}


# ============================================================ punctuation
def g_period(c):
    r = 0.58 * c.v + 4
    return B([dot(c, r, r - 1, r)])


def g_comma(c):
    r = 0.58 * c.v + 4
    tail = poly([(r - 0.80 * r, 0.6 * r), (r + 0.80 * r, 0.6 * r), (r + 0.42 * r, -40), (r - 0.60 * r, -142)])
    return B([dot(c, r, r - 1, r), tail])


def g_colon(c):
    r = 0.58 * c.v + 4
    return B([dot(c, r, r - 1, r), dot(c, r, c.XH - r + 1, r)])


def g_semicolon(c):
    r = 0.58 * c.v + 4
    tail = poly([(r - 0.80 * r, 0.6 * r), (r + 0.80 * r, 0.6 * r), (r + 0.42 * r, -40), (r - 0.60 * r, -142)])
    return B([dot(c, r, r - 1, r), tail, dot(c, r, c.XH - r + 1, r)])


def g_exclam(c):
    v, CAP = c.v, c.CAP
    r = 0.58 * c.v + 4
    w = 2 * r
    st = poly([(0, CAP), (w, CAP), (w * 0.5 + v * 0.36, 215), (w * 0.5 - v * 0.36, 215)])
    return B([st, dot(c, r, r - 1, r)])


def g_hyphen(c):
    return B([rect(0, 0.30 * c.CAP - c.hb / 2 + 24, 270 + 0.1 * c.v, 0.30 * c.CAP + c.hb / 2 + 24)])


def g_quotesingle(c):
    v = c.v; w = v * 0.92
    return B([poly([(0, c.CAP), (w, c.CAP), (w * 0.5 + v * 0.30, c.CAP - 190), (w * 0.5 - v * 0.30, c.CAP - 190)])])


def g_quotedbl(c):
    v = c.v; w = v * 0.92; g = 0.62 * w + 56
    def one(x):
        return poly([(x, c.CAP), (x + w, c.CAP), (x + w * 0.5 + v * 0.30, c.CAP - 190), (x + w * 0.5 - v * 0.30, c.CAP - 190)])
    return B([one(0), one(w + g)])


def g_plus(c):
    v, hb = c.v, c.hb; W = 440 + 0.1 * v; cy = 0.5 * c.XH + 10
    return B([rect(0, cy - hb / 2, W, cy + hb / 2), rect(W / 2 - v / 2, cy - W / 2, W / 2 + v / 2, cy + W / 2)])


def g_equal(c):
    hb = c.hb; W = 440 + 0.1 * c.v; cy = 0.5 * c.XH + 10; g = 0.20 * W
    return B([rect(0, cy - g - hb / 2, W, cy - g + hb / 2), rect(0, cy + g - hb / 2, W, cy + g + hb / 2)])


def g_slash(c):
    W = 380 + 0.1 * c.v; dg = c.dg * 0.82
    return B(dstroke(c, (dg * 0.45, -90), (W - dg * 0.45, c.ASC), tw=dg, cut0=Hcut(-90), cut1=Hcut(c.ASC)))


def g_parenleft(c):
    v = c.v; h = c.h
    cx = 330; cy = (c.ASC + c.DESC) / 2 + 20
    ryc = (c.ASC - c.DESC) / 2 + 20 - h / 2; rxc = 250
    segs, ws = sk_arc(c, cx, cy, rxc, ryc, 118, 242, 0.95, 0.95)
    ws = [(v * 0.40,) * 2 if i in (0, len(ws) - 1) else (v * 0.46,) * 2 for i in range(len(ws))]
    return B(stroke(segs, ws))


def g_parenright(c):
    cs = g_parenleft(c); bb = bbox(cs)
    W = bb[2] + bb[0]
    return B(transform(cs, lambda p: (W - p[0], p[1])))


def g_question(c):
    v, h, hb, CAP = c.v, c.h, c.hb, c.CAP
    W = 420 + 0.2 * v
    cx = W / 2; ryc = 0.285 * CAP; rxc = W / 2 - v / 2
    cy = CAP + c.OS - h / 2 - ryc
    segs, ws = sk_arc(c, cx, cy, rxc, ryc, 160, 0, 0.95, 1.0)
    ws[-1] = (v / 2, v / 2)
    a = pt_on_ellipse(cx, cy, rxc, ryc, 160)
    endp = pt_on_ellipse(cx, cy, rxc, ryc, 0)
    tx = W * 0.50; y1 = 0.40 * CAP; dy = endp[1] - y1
    tail = C(endp, (endp[0], endp[1] - 0.52 * dy), (tx, y1 + 0.52 * dy), (tx, y1))
    t1, t2 = split(tail, 0.5)
    ln = L((tx, y1), (tx, 0.265 * CAP))
    sg = list(segs) + [t1, t2, ln]
    w = ws + [(v * 0.5,) * 2, (v * 0.5,) * 2, (v / 2,) * 2]
    w = w[:len(sg) + 1]
    r = 0.58 * v + 4
    return B(stroke(sg, w, cut0=tcut(c, a), cut1=Hcut(0.265 * CAP)) + [dot(c, tx, r - 1, r)])


def g_naira(c):
    cs = g_N(c); W = bbox(cs)[2]; hb = c.hb
    ys = (c.CAP * 0.40, c.CAP * 0.60)
    bars = [rect(-34, y - hb * 0.42, W + 34, y + hb * 0.42) for y in ys]
    return B(list(cs) + bars)


def g_space(c): return []


def g_endash(c): return B([rect(0, 0.30 * c.CAP - c.hb / 2 + 24, 470 + 0.1 * c.v, 0.30 * c.CAP + c.hb / 2 + 24)])
def g_emdash(c): return B([rect(0, 0.30 * c.CAP - c.hb / 2 + 24, 900 + 0.1 * c.v, 0.30 * c.CAP + c.hb / 2 + 24)])
def g_underscore(c): return B([rect(0, -150, 560 + 0.1 * c.v, -150 + c.hb)])
def g_bar(c): return B([rect(0, c.DESC, c.v, c.ASC)])


def g_bracketleft(c):
    v, hb = c.v, c.hb; W = 250 + 0.1 * v
    return B([rect(0, c.DESC, v, c.ASC), rect(0, c.ASC - hb, W, c.ASC), rect(0, c.DESC, W, c.DESC + hb)])


def g_bracketright(c):
    cs = g_bracketleft(c); W = bbox(cs)[2]
    return finalize(transform(cs, lambda p: (W - p[0], p[1])))


def g_less(c):
    W = 440 + 0.1 * c.v; cy = 0.5 * c.XH + 10; dg = c.dg * 0.80
    return B(dstroke(c, (W - 20, cy + W * 0.40), (28, cy), tw=dg * 1.3, cut0=None) +
             dstroke(c, (28, cy), (W - 20, cy - W * 0.40), tw=dg * 1.3, cut1=None))


def g_greater(c):
    cs = g_less(c); W = bbox(cs)[2] + bbox(cs)[0]
    return finalize(transform(cs, lambda p: (round(W) - p[0], p[1])))


def g_asterisk(c):
    r = 120; cx, cy = r + 10, c.CAP - 120; out = []
    for a in (90, 90 + 72, 90 + 144, 90 + 216, 90 + 288):
        p1 = (cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
        out += stroke([L((cx, cy), p1)], [(c.v * 0.30,) * 2, (c.v * 0.30,) * 2])
    return B(out)


def g_quoteright(c):
    cs = g_comma(c); r = 0.58 * c.v + 4
    return finalize(translate(cs, 0, c.CAP - 2 * r + 10))


def g_quoteleft(c):
    cs = g_quoteright(c); bb = bbox(cs); cx = (bb[0] + bb[2]) / 2; cy = (bb[1] + bb[3]) / 2
    return finalize(transform(cs, lambda p: (round(2 * cx) - p[0], round(2 * cy) - p[1])))


def _double(c, one):
    cs = one(c); bb = bbox(cs); w = bb[2] - bb[0]; gap = 0.45 * w + 40
    return finalize(cs + translate(cs, w + gap, 0))


def g_quotedblright(c): return _double(c, g_quoteright)
def g_quotedblleft(c): return _double(c, g_quoteleft)
def g_modifierapostrophe(c): return g_quoteright(c)
