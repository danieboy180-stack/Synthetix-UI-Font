import numpy as np
from geom import *


def winding_grid(contours, x0, y0, x1, y1, step=2.0, n=60):
    xs = np.arange(x0, x1, step) + step / 2; ys = np.arange(y0, y1, step) + step / 2
    X, Y = np.meshgrid(xs, ys)
    W = np.zeros(X.shape, dtype=int)
    for c in contours:
        p = np.array(flatten(c, n))
        xa, ya = p[:, 0], p[:, 1]; xb, yb = np.roll(xa, -1), np.roll(ya, -1)
        for i in range(len(xa)):
            if ya[i] == yb[i]: continue
            up = (ya[i] <= Y) & (yb[i] > Y)
            dn = (ya[i] > Y) & (yb[i] <= Y)
            cr = (xb[i] - xa[i]) * (Y - ya[i]) - (X - xa[i]) * (yb[i] - ya[i])
            W += (up & (cr > 0)).astype(int) - (dn & (cr < 0)).astype(int)
    return W
