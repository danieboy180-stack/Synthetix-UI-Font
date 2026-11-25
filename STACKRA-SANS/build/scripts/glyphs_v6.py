"""Stackra Sans V6 - glyph redraws and geometry repairs layered on the frozen V5 drawing functions.

glyphset.py applies OVERRIDES after building the V5 registry, so every V6 change is a reviewable, named diff
(defect -> fix -> proof) and the V5 drawings stay available for regression comparison.
Rule (plan items 14, 22, 25): fix the construction, never the symptom; prove it with the raster/topology gates.
"""
import math
from geom import *
from boolop import B, finalize
import glyphs_uc as _U


def _xc(p0, p1, y):
    """x of the line through p0,p1 at height y."""
    return p0[0] + (p1[0] - p0[0]) * (y - p0[1]) / (p1[1] - p0[1])


def g_Y(c):
    """Y as ONE analytic outline (union of two diagonal arms and the stem).

    V5 defect: at wght 300 the arm/stem corners lie ~4.6 units inside the stem edge, which defeats the
    overlap-removal chaining and adds a spurious triangle to the left arm (raster mismatch 17.8 %, plan items
    26-28 / 54).  The union of this construction is a plain 10-vertex polygon, so no Boolean step is needed and
    the vertex order is identical in every master."""
    v, CAP, dg = c.v, c.CAP, c.dg
    W = 668 + 0.2 * v; ym = 0.40 * CAP; t = dg * 0.86
    hx = W / 2
    L0, L1 = (dg / 2, CAP), (hx, ym - 34)            # left arm centre line (same end points as V5)
    R0, R1 = (W - dg / 2, CAP), (hx, ym - 20)        # right arm centre line
    sl, sr = hx - v / 2, hx + v / 2                   # stem edges
    # inner edges meet at the notch N:  xcL(y)+t/2 = xcR(y)-t/2
    mL = (L1[0] - L0[0]) / (L1[1] - L0[1]); mR = (R1[0] - R0[0]) / (R1[1] - R0[1])
    bL = L0[0] - mL * L0[1]; bR = R0[0] - mR * R0[1]
    yN = (bR - bL - t) / (mL - mR); xN = mL * yN + bL + t / 2
    # outer edges meet the stem edges:  xcL(y)-t/2 = sl ; xcR(y)+t/2 = sr
    yl = (sl + t / 2 - bL) / mL; yr = (sr - t / 2 - bR) / mR
    pts = [(L0[0] - t / 2, CAP), (L0[0] + t / 2, CAP), (xN, yN), (R0[0] - t / 2, CAP), (R0[0] + t / 2, CAP),
           (sr, yr), (sr, 0), (sl, 0), (sl, yl)]
    return B([poly(pts)])


def _mirror_x(cs, W):
    """Reflect contours about the vertical axis x = W/2 and RESTORE the winding direction (a reflection flips it)."""
    return finalize([rev_contour(c) for c in transform(cs, lambda p: (round(W) - p[0], p[1]))])


def g_bracketright(c):
    """V5 defect: the mirrored bracketleft kept the reflected (wrong) winding, so the outer contour was
    counter-clockwise in the source; the QA winding gate (item 27) flags it in every shipped file."""
    cs = _U.g_bracketleft(c)
    return _mirror_x(cs, bbox(cs)[2])


def g_greater(c):
    """Same defect and fix as bracketright, for the mirrored 'less'."""
    cs = _U.g_less(c); bb = bbox(cs)
    return _mirror_x(cs, bb[2] + bb[0])


OVERRIDES = {'Y': g_Y, 'bracketright': g_bracketright, 'greater': g_greater}
