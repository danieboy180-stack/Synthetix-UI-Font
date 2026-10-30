#!/usr/bin/env python3
"""
loo_validate.py - honest accuracy check for the tracking / word-spacing fit.

Fits letter-spacing and word-spacing on N-1 samples of a weight class, then
measures glyph left-edge error on the held-out sample. The in-sample number
(what fit_font.py reports) is optimistic; the held-out number is the real one.

  python loo_validate.py --regular InstrumentSans-Regular.ttf --bold InstrumentSans-Bold.ttf
Semibold uses the bold file for static fonts; pass a variable font to --regular
and --bold to test real weights (not done in the original run: no network).
"""
import argparse, json, os
import numpy as np
import fit_font as ff

HERE = os.path.dirname(os.path.abspath(__file__))


def sample_rows(font, m, s, scale):
    sc = ((s["cap_px"] / m["cap"]) * (s["xh_px"] / m["xh"])) ** 0.5
    em = ff.SZ * sc
    pos = ff.pen_positions(font, s["text"])
    cand, ci, k = [], 0, 0
    for i, ch in enumerate(s["text"]):
        if ch == " ":
            k += 1
            continue
        cand.append(((pos[i] + ff.lsb(font, ch)) * sc, ci, k)); ci += 1
    tx = np.array(s["glyph_left_px"], float)
    if len(tx) != len(cand):
        return None
    c0 = cand[0][0]
    A = np.array([[ci * em, k * em] for _, ci, k in cand])
    b = np.array([t - (cx - c0) for (cx, _, _), t in zip(cand, tx)])
    return A, b


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--regular", required=True)
    ap.add_argument("--bold", required=True)
    ap.add_argument("--metrics", default=os.path.join(HERE, "..", "metrics", "pinterest-sans-measured.json"))
    a = ap.parse_args()
    D = json.load(open(a.metrics)); scale = D["meta"]["scale_px_per_css"]
    files = {"regular": a.regular, "semibold": a.bold, "bold": a.bold}
    for g, path in files.items():
        f, _ = ff.load_font(path); m = ff.metrics(f)
        S = [s for s in D["samples"] if s["group"] == g]
        rows = {s["name"]: sample_rows(f, m, s, scale) for s in S}
        rows = {k: v for k, v in rows.items() if v}
        if len(rows) < 2:
            print(f"{g:9s} n/a (needs >= 2 samples, has {len(rows)})"); continue
        ins, outs, base = [], [], []
        for held in rows:
            tr = [n for n in rows if n != held]
            A = np.vstack([rows[n][0] for n in tr]); b = np.concatenate([rows[n][1] for n in tr])
            sol = np.linalg.lstsq(A, b, rcond=None)[0]
            ins.append(np.abs(b - A @ sol).mean())
            Ah, bh = rows[held]
            outs.append(np.abs(bh - Ah @ sol).mean()); base.append(np.abs(bh).mean())
        print(f"{g:9s} untuned {np.mean(base)/scale:.2f}  in-sample {np.mean(ins)/scale:.2f}  "
              f"HELD-OUT {np.mean(outs)/scale:.2f} css px mean glyph x-error  (n={len(rows)})")


if __name__ == "__main__":
    main()
