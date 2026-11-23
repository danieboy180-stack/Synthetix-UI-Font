"""Stackra Sans - lowercase construction (original drawings, skeleton + width model).
Every glyph is a function of Ctx (design direction + weight) so all weights share topology."""
import math
from geom import *
from boolop import B


def _interp(pts, w):
    ks = sorted(pts)
    if w <= ks[0]: return pts[ks[0]]
    if w >= ks[-1]: return pts[ks[-1]]
    for a, b in zip(ks, ks[1:]):
        if a <= w <= b:
            return pts[a] + (pts[b] - pts[a]) * (w - a) / (b - a)


class Ctx:
    STEM = {300: 54, 400: 84, 500: 98, 600: 112, 700: 130}

    def __init__(s, d='A', w=400, XH=515):
        s.d = d; s.w = w
        s.XH = XH; s.CAP = 700; s.ASC = 735; s.DESC = -185; s.OS = 12
        s.v = _interp(Ctx.STEM, w)
        con = {'A': 0.90, 'B': 0.84, 'C': 0.96}[d]
        s.h = s.v * con
        s.hb = s.v * (con - 0.04)
        s.k = {'A': 0.575, 'B': 0.55, 'C': 0.615}[d]
        s.term = {'A': 'v', 'B': 'p', 'C': 'h'}[d]
        s.tilt = {'A': 0, 'B': 8, 'C': 0}[d]
        s.sa = {'A': 66, 'B': 62, 'C': 72}[d]          # shoulder start angle
        wd = {'A': 1.0, 'B': 1.0, 'C': 0.95}[d]
        s.Wn = (430 + 0.30 * s.v) * wd
        s.Wo = (508 + 0.35 * s.v) * wd
        s.Wsp = (385 + 0.28 * s.v) * wd                  # m arch span
        s.dg = s.v * 0.97                                # diagonal horizontal thickness
        s.ts = 25 if d != 'C' else 0                     # t top cut slant


def hw(c, th, f=1.0):
    ct = math.cos(math.radians(th)) ** 2
    return f * (c.h + (c.v - c.h) * ct) / 2


def cuts_of(a0, a1):
    d = 1 if a1 > a0 else -1
    cuts = [a0]; a = a0
    while True:
        nxt = (math.floor(a / 90 + 1e-9) + 1) * 90 if d > 0 else (math.ceil(a / 90 - 1e-9) - 1) * 90
        if (d > 0 and nxt >= a1 - 1e-9) or (d < 0 and nxt <= a1 + 1e-9):
            cuts.append(a1); break
        cuts.append(nxt); a = nxt
    return cuts


def sk_arc(c, cx, cy, rxc, ryc, a0, a1, tf0=1.0, tf1=1.0, tilt=0.0):
    """Skeleton (centerline) elliptical arc + node half-widths following stress."""
    segs = arc(cx, cy, rxc, ryc, a0, a1, c.k, tilt)
    cs = cuts_of(a0, a1)
    ws = []
    for i, a in enumerate(cs):
        f = tf0 if i == 0 else (tf1 if i == len(cs) - 1 else 1.0)
        ws.append((hw(c, a, f), hw(c, a, f)))
    return segs, ws


def cat(*paths):
    segs = []; ws = []
    for sg, w in paths:
        if not segs:
            segs = list(sg); ws = list(w)
        else:
            last = ws[-1]; first = w[0]
            ws[-1] = last if last == first else (last, first)
            segs += sg; ws += w[1:]
    return segs, ws


def line_path(p0, p1, w0, w1):
    return [L(p0, p1)], [(w0, w0), (w1, w1)]


def tcut(c, P, slant=None):
    if slant is not None: return Acut(P, slant)
    if c.term == 'v': return Vcut(P[0])
    if c.term == 'h': return Hcut(P[1])
    return None


def pt_on_ellipse(cx, cy, rx, ry, th, tilt=0.0):
    r = math.radians(th)
    x, y = rot((rx * math.cos(r), ry * math.sin(r)), tilt)
    return (cx + x, cy + y)


def ring_item(c, cx, cy, rxo, ryo, v=None, h=None):
    o, i = ring(cx, cy, rxo, ryo, v or c.v, h or c.h, c.k, c.tilt)
    return (o, i)


# ------------------------------------------------------------------ arches / stems
def arch(c, x0, W, sy=0.62, ey=0.36, apex=0.53):
    v, h, XH = c.v, c.h, c.XH
    S = (x0 + v / 2 - 4, sy * XH)
    T = (x0 + W * apex, XH + c.OS - h / 2)
    E = (x0 + W - v / 2, ey * XH)
    d = (math.cos(math.radians(c.sa)), math.sin(math.radians(c.sa)))
    L1 = norm(sub(T, S)); k = c.k
    s1_ = C(S, add(S, mul(d, 0.42 * L1)), (T[0] - 0.62 * (T[0] - S[0]), T[1]), T)
    s2_ = C(T, (T[0] + (E[0] - T[0]) * k, T[1]), (E[0], E[1] + (T[1] - E[1]) * k), E)
    s3_ = L(E, (E[0], 0))
    return stroke([s1_, s2_, s3_], [(h * 0.52,) * 2, (h / 2,) * 2, (v / 2,) * 2, (v / 2,) * 2], cut1=Hcut(0))


def g_n(c): return B([rect(0, 0, c.v, c.XH)] + arch(c, 0, c.Wn))
def g_h(c): return B([rect(0, 0, c.v, c.ASC)] + arch(c, 0, c.Wn))


def g_m(c):
    v, XH = c.v, c.XH
    return B([rect(0, 0, v, XH), rect(c.Wsp - v, 0, c.Wsp, 0.68 * XH)] + arch(c, 0, c.Wsp) + arch(c, c.Wsp - v, c.Wsp))


def g_u(c):
    W = c.Wn
    cs = B([rect(0, 0, c.v, c.XH)] + arch(c, 0, W))
    return B(transform(cs, lambda p: (W - p[0], c.XH - p[1])))


def g_r(c):
    v, h, XH = c.v, c.h, c.XH
    Wr = 318 + 0.25 * v
    S = (v / 2 - 4, 0.60 * XH); T = (0.50 * Wr, XH + c.OS - h / 2); E = (Wr - 8, 0.845 * XH)
    d = (math.cos(math.radians(c.sa)), math.sin(math.radians(c.sa)))
    L1 = norm(sub(T, S))
    s1_ = C(S, add(S, mul(d, 0.42 * L1)), (T[0] - 0.62 * (T[0] - S[0]), T[1]), T)
    de = (math.cos(math.radians(-30)), math.sin(math.radians(-30)))
    s2_ = C(T, (T[0] + 0.42 * (E[0] - T[0]), T[1]), sub(E, mul(de, 0.40 * (E[0] - T[0]))), E)
    arm = stroke([s1_, s2_], [(h * 0.60,) * 2, (h * 0.52,) * 2, (h * 0.56,) * 2], cut1=tcut(c, E))
    return B([rect(0, 0, v, XH)] + arm)


# ------------------------------------------------------------------ round forms
def g_o(c):
    rx = c.Wo / 2; ry = c.XH / 2 + c.OS
    return B([ring_item(c, rx, c.XH / 2, rx, ry)])


def g_c(c):
    rx0 = c.Wo / 2 - 8; ry0 = c.XH / 2 + c.OS
    cx, cy = rx0, c.XH / 2
    segs, ws = sk_arc(c, cx, cy, rx0 - c.v / 2, ry0 - c.h / 2, 42, 318, 0.95, 0.95)
    a = pt_on_ellipse(cx, cy, rx0 - c.v / 2, ry0 - c.h / 2, 42); b = pt_on_ellipse(cx, cy, rx0 - c.v / 2, ry0 - c.h / 2, 318)
    return B(stroke(segs, ws, cut0=tcut(c, a), cut1=tcut(c, b)))


def g_e(c):
    v, h, hb, XH = c.v, c.h, c.hb, c.XH
    rx0 = c.Wo / 2 - 4; ry0 = XH / 2 + c.OS; cx, cy = rx0, XH / 2
    rxc, ryc = rx0 - v / 2, ry0 - h / 2
    ybar = cy - 4
    phi0 = math.degrees(math.asin((ybar - cy) / ryc))
    ea = 322 - max(0.0, min(0.5 * (v - 84), 30.0)) + max(0.0, min(0.2 * (84 - v), 6.0))
    segs, ws = sk_arc(c, cx, cy, rxc, ryc, phi0, ea, 1.0, 0.95)
    end = pt_on_ellipse(cx, cy, rxc, ryc, ea)
    P0 = (cx - rxc, ybar); P1 = pt_on_ellipse(cx, cy, rxc, ryc, phi0)
    bar = line_path(P0, P1, hb / 2, hb / 2)
    sg, w = cat(bar, (segs, ws))
    w[1] = ((hb / 2, hb / 2), (v / 2, v / 2))
    return B(stroke(sg, w, cut1=tcut(c, end)))


def g_bd_bowl(c, left, desc=False):
    """stem+bowl ring clipped; left=True -> b/p (stem on left); else d/q."""
    v, h, XH = c.v, c.h, c.XH
    Wb = c.Wo - 6
    ry = XH / 2 + c.OS
    ext = 18
    if left:
        cx = (-ext + Wb) / 2; rx = (Wb + ext) / 2
        stem = rect(0, c.DESC if desc else 0, v, c.ASC if not desc else XH)
        clip = [rect(0, -400, Wb + 50, 900)]
    else:
        cx = (0 + Wb + ext) / 2; rx = (Wb + ext) / 2
        stem = rect(Wb - v, c.DESC if desc else 0, Wb, c.ASC if not desc else XH)
        clip = [rect(-50, -400, Wb, 900)]
    ringi = ring_item(c, cx, XH / 2, rx, ry)
    return B([stem, ringi], clip=clip)


def g_b(c): return g_bd_bowl(c, True)
def g_d(c): return g_bd_bowl(c, False)
def g_p(c): return g_bd_bowl(c, True, desc=True)
def g_q(c): return g_bd_bowl(c, False, desc=True)


def g_a(c):
    v, h, XH = c.v, c.h, c.XH
    Wa = 0.90 * c.Wo + 0.1 * v
    T0 = (0.085 * Wa + 6, 0.785 * XH); Tp = (0.50 * Wa, XH + c.OS - h / 2); E = (Wa - v / 2, 0.58 * XH)
    d0 = (math.cos(math.radians(48)), math.sin(math.radians(48)))
    L1 = norm(sub(Tp, T0)); k = c.k
    s1_ = C(T0, add(T0, mul(d0, 0.34 * L1)), (Tp[0] - 0.58 * (Tp[0] - T0[0]), Tp[1]), Tp)
    s2_ = C(Tp, (Tp[0] + (E[0] - Tp[0]) * k, Tp[1]), (E[0], E[1] + (Tp[1] - E[1]) * k), E)
    s3_ = L(E, (E[0], 0))
    top = stroke([s1_, s2_, s3_], [(h * 0.46,) * 2, (h / 2,) * 2, (v / 2,) * 2, (v / 2,) * 2],
                 cut0=tcut(c, T0), cut1=Hcut(0))
    xL = 0.04 * Wa + 2; xR = Wa + 30; ytop = 0.655 * XH
    bowl = ring_item(c, (xL + xR) / 2, (ytop - c.OS) / 2, (xR - xL) / 2, (ytop + c.OS) / 2, v * 0.95, h * 0.90)
    return B(top + [bowl], clip=[rect(-50, -300, Wa, 900)])


def g_g(c):
    v, h, XH = c.v, c.h, c.XH
    Wg = 0.97 * c.Wo + 0.05 * v
    ry = XH / 2 + c.OS; ext = 16
    bowl = ring_item(c, (Wg + ext) / 2, XH / 2, (Wg + ext) / 2, ry)
    xs = Wg - v / 2
    ryt = 128; rxt = 0.44 * Wg
    cy_t = c.DESC + h / 2 + ryt + 4
    ang_end = -152
    segs, ws = sk_arc(c, xs - rxt, cy_t, rxt, ryt, 0, ang_end, 1.0, 0.95)
    ws[0] = (v / 2, v / 2)
    endp = pt_on_ellipse(xs - rxt, cy_t, rxt, ryt, ang_end)
    sg, w = cat(line_path((xs, XH), (xs, cy_t), v / 2, v / 2), (segs, ws))
    tail = stroke(sg, w, cut0=Hcut(XH), cut1=tcut(c, endp))
    return B(tail + [bowl], clip=[rect(0, -400, Wg, 900)])


def s_curve(c, W, y0, y1):
    """Two elliptical bowls joined by an S-spine (cubic through a 26-degree diagonal)."""
    v, h = c.v, c.h
    H = y1 - y0
    hv = v * 0.94
    Ytop = y1 + c.OS - h / 2; Ybot = y0 - c.OS + h / 2
    ryu = 0.236 * H; ryl = 0.252 * H
    rxu = 0.335 * W; rxl = 0.355 * W
    cxu = 0.065 * W + hv / 2 + rxu; cyu = Ytop - ryu
    cxl = 0.965 * W - hv / 2 - rxl; cyl = Ybot + ryl
    dvv = max(0.0, (v - 84) / 46.0)
    a_up = 34 + 12 * dvv; a_lo = -146 - 12 * dvv
    up, ws_u = sk_arc(c, cxu, cyu, rxu, ryu, a_up, 180, 0.95 - 0.04 * dvv, 1.0)
    lo, ws_l = sk_arc(c, cxl, cyl, rxl, ryl, 0, a_lo, 1.0, 0.95 - 0.04 * dvv)
    N2 = (cxu - rxu, cyu); N4 = (cxl + rxl, cyl)
    N3 = ((N2[0] + N4[0]) / 2, (N2[1] + N4[1]) / 2)
    d3 = (math.cos(math.radians(-27)), math.sin(math.radians(-27)))
    a = C(N2, (N2[0], N2[1] - 0.58 * (N2[1] - N3[1])), sub(N3, mul(d3, 0.22 * abs(N4[0] - N2[0]))), N3)
    b = C(N3, add(N3, mul(d3, 0.22 * abs(N4[0] - N2[0]))), (N4[0], N4[1] + 0.58 * (N3[1] - N4[1])), N4)
    wsp = ((h + v) / 4) * 1.10
    a1, a2 = split(a, 0.5); b1, b2 = split(b, 0.5)
    wm = (hv / 2 + wsp) / 2
    spine_w = [(hv / 2,) * 2, (wm,) * 2, (wsp,) * 2, (wm,) * 2, (hv / 2,) * 2]
    sg = list(up) + [a1, a2, b1, b2] + list(lo)
    ws = ws_u[:-1] + spine_w + ws_l[1:]
    sa_ = pt_on_ellipse(cxu, cyu, rxu, ryu, a_up); sb_ = pt_on_ellipse(cxl, cyl, rxl, ryl, a_lo)
    return stroke(sg, ws, cut0=tcut(c, sa_), cut1=tcut(c, sb_))


def g_s(c): return B(s_curve(c, 0.80 * c.Wo + 6, 0, c.XH))


def g_t(c):
    v, h, hb, XH = c.v, c.h, c.hb, c.XH
    xs = 76 + 0.1 * v; ytop = 640
    rxh = 128; ryh = 122
    cy_h = -c.OS + h / 2 + ryh
    segs, ws = sk_arc(c, xs + rxh, cy_h, rxh, ryh, 180, 306, 1.0, 0.95)
    ws[0] = (v / 2, v / 2)
    endp = pt_on_ellipse(xs + rxh, cy_h, rxh, ryh, 306)
    sg, w = cat(line_path((xs, ytop), (xs, cy_h), v / 2, v / 2), (segs, ws))
    cut0 = Acut((xs, ytop), c.ts) if c.ts else Hcut(ytop)
    stem = stroke(sg, w, cut0=cut0, cut1=tcut(c, endp))
    bar = rect(0, XH - hb, xs + v / 2 + 98, XH)
    return B(stem + [bar])


def g_l(c): return B([rect(0, 0, c.v, c.ASC)])   # superseded by the tailed l in glyphs_uc.py


def dot(c, cx, cy, r=None):
    r = r or 0.56 * c.v + 3
    return arc(cx, cy, r, r, 0, 360, 0.5523)


def g_i(c): return B([rect(0, 0, c.v, c.XH), dot(c, c.v / 2, 664)])


def g_j(c):
    v, h, XH = c.v, c.h, c.XH
    xs = v / 2
    ryt = 110; rxt = 0.80 * (v + 70) + 30
    xsc = xs + 130
    cy_t = c.DESC + h / 2 + ryt + 4
    segs, ws = sk_arc(c, xsc - rxt, cy_t, rxt, ryt, 0, -150, 1.0, 0.92)
    ws[0] = (v / 2, v / 2)
    endp = pt_on_ellipse(xsc - rxt, cy_t, rxt, ryt, -150)
    sg, w = cat(line_path((xsc, XH), (xsc, cy_t), v / 2, v / 2), (segs, ws))
    st = stroke(sg, w, cut0=Hcut(XH), cut1=tcut(c, endp))
    return B(st + [dot(c, xsc, 664)])
