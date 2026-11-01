#!/usr/bin/env python3
"""
browser_fit.py - measure and fit in real Chromium (subpixel positioning ON), cap-height matched.

Why Chromium: Pillow ignores GPOS kerning, and default headless Chromium on Linux rounds glyph
advances to whole css px; both distort spacing numbers. This tool launches Chromium with
--font-render-hinting=none --enable-font-subpixel-positioning, like a phone.

  pip install playwright pillow numpy scipy && playwright install chromium

  # 1) fit tracking: edited-but-untracked weights -> leave-one-text-out model choice + coefficients
  python build_fork.py --regular R.ttf --bold B.ttf --out /tmp/unb --no-tracking
  python browser_fit.py fit --w420 /tmp/unb/Unbaked-Regular.ttf --w500 /tmp/unb/Unbaked-SemiBold.ttf --w610 /tmp/unb/Unbaked-Bold.ttf

  # 2) verify the built fork (and compare to plain Instrument Sans 400/700)
  python browser_fit.py verify --fonts ../fonts --plain-regular R.ttf --plain-bold B.ttf

Sizing: every string is rendered at font-size = measured cap height / 0.72 (Instrument Sans cap-height/em),
so vertical metrics are matched and any remaining horizontal mismatch is what tracking must fix.
Strings: 9 original samples + ui_strings (menu items at 3 display sizes, pangram sentences).
"""
import argparse, json, os, tempfile
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
SC = 4.5                    # screenshot px per css px (see metrics JSON)
CAP_EM = 0.72               # Instrument Sans cap height / em
CAP_CSS = 12.44             # measured body cap height in css px (for reporting errors in css px)
WT = {"regular": 400, "semibold": 600, "bold": 700}
WN = {"regular": 0.0, "semibold": 80 / 190, "bold": 1.0}
ARGS = ["--font-render-hinting=none", "--enable-font-subpixel-positioning"]


def glyph_lefts(png):
    a = np.asarray(Image.open(png).convert("RGB")).astype(int)
    d = (255 - a).sum(axis=2)                                   # white background
    lab, _ = ndi.label(d > 250, structure=np.ones((3, 3)))
    cs = [dict(x0=o[1].start, x1=o[1].stop - 1, y0=o[0].start, y1=o[0].stop - 1) for o in ndi.find_objects(lab)]
    cs.sort(key=lambda c: c["x0"]); used = [False] * len(cs)
    for i, c in enumerate(cs):                                   # merge i/j dots into their stems
        cw, ch = c["x1"] - c["x0"] + 1, c["y1"] - c["y0"] + 1; cx = (c["x0"] + c["x1"]) / 2
        for j, o in enumerate(cs):
            if i == j or used[j]: continue
            if (o["x0"] - 4 <= cx <= o["x1"] + 4 and c["y1"] < o["y0"] and ch <= 1.25 * cw + 4
                    and cw < (o["x1"] - o["x0"] + 1) * 1.6 and (o["y0"] - c["y1"]) < ch * 1.6
                    and (o["y1"] - o["y0"] + 1) > ch * 1.8):
                o["x0"] = min(o["x0"], c["x0"]); o["x1"] = max(o["x1"], c["x1"]); o["y0"] = min(o["y0"], c["y0"])
                used[i] = True; break
    cs = [c for i, c in enumerate(cs) if not used[i]]
    return np.array([c["x0"] for c in cs]), cs[-1]["x1"] - cs[0]["x0"] + 1


def render(strings, faces, size_adjust=1.0):
    """faces: {css_weight: font_path}. Returns {name: (lefts_rel_first_glyph, ink_width) or None}."""
    tmp = tempfile.mkdtemp()
    css = "".join(f'@font-face{{font-family:"T";src:url("file://{os.path.abspath(p)}");font-weight:{w};'
                  + (f"size-adjust:{size_adjust*100:.0f}%;" if size_adjust != 1 else "") + "}" for w, p in faces.items())
    body = "".join(f'<div id=s{i} style="font-family:T;font-weight:{WT[s["group"]]};'
                   f'font-size:{s["cap_px"] / SC / CAP_EM / size_adjust:.4f}px">{s["text"]}</div>' for i, s in enumerate(strings))
    hp = os.path.join(tmp, "t.html")
    open(hp, "w").write(f'<!doctype html><meta charset=utf-8><style>{css}body{{margin:0;background:#fff;color:#000;font-kerning:normal}}'
                        f'div{{white-space:nowrap;padding:12px 8px;display:inline-block}}</style>{body}')
    out = {}
    with sync_playwright() as p:
        b = p.chromium.launch(args=ARGS); pg = b.new_page(viewport={"width": 1000, "height": 300}, device_scale_factor=SC)
        pg.goto("file://" + hp); pg.wait_for_timeout(600)
        for i, s in enumerate(strings):
            png = os.path.join(tmp, f"s{i}.png"); pg.locator(f"#s{i}").screenshot(path=png)
            l, w = glyph_lefts(png)
            out[s["name"]] = (l - l[0], w) if len(l) == len(s["text"].replace(" ", "")) else None
        b.close()
    return out


def load(path):
    d = json.load(open(path))
    return d["samples"] + d.get("ui_strings", [])


def cmd_verify(a):
    S = load(a.metrics)
    def score(tag, faces, sa):
        R = render(S, faces, sa); by = {}
        for s in S:
            r = R[s["name"]]
            if r is None: continue
            xt = np.array(s["glyph_left_px"], float)
            e = np.abs(xt - r[0]).mean() / s["cap_px"] * CAP_CSS            # css px at the measured body size
            wd = 100 * (r[1] - s["ink_w_px"]) / s["ink_w_px"]
            by.setdefault(s["group"], []).append((e, wd)); by.setdefault("all", []).append((e, wd))
        print(f"{tag}")
        for g in ("regular", "semibold", "bold", "all"):
            if g in by:
                print(f"   {g:9s} n={len(by[g]):2d}  glyph x-error {np.mean([x[0] for x in by[g]]):.2f} css px   width |err| {np.mean([abs(x[1]) for x in by[g]]):.2f}%   bias {np.mean([x[1] for x in by[g]]):+.2f}%")
    score("Synthetix UI fork", {400: f"{a.fonts}/SynthetixUI-Regular.ttf", 600: f"{a.fonts}/SynthetixUI-SemiBold.ttf",
                                700: f"{a.fonts}/SynthetixUI-Bold.ttf"}, a.size_adjust)
    if a.plain_regular:
        score("Plain Instrument Sans 400/700 (same cap-matched size)", {400: a.plain_regular, 700: a.plain_bold}, 1.0)


def cmd_fit(a):
    S = load(a.metrics); W = {"regular": a.w420, "semibold": a.w500, "bold": a.w610}
    R = render(S, {WT[g]: p for g, p in W.items()}, 1.0)
    rows = []                                           # (text, count, space_count, weight_norm, y in cap units)
    for s in S:
        r = R[s["name"]]
        if r is None: continue
        xt = np.array(s["glyph_left_px"], float); xr = r[0]; gi = 0; sp = 0
        for ch in s["text"]:
            if ch == " ": sp += 1; continue
            if gi >= 1: rows.append((s["text"], gi, sp, WN[s["group"]], (xt[gi] - xr[gi]) / s["cap_px"]))
            gi += 1
    T = np.array([r[0] for r in rows]); cnt = np.array([r[1] for r in rows], float) / CAP_EM
    sp = np.array([r[2] for r in rows], float) / CAP_EM; wn = np.array([r[3] for r in rows]); Y = np.array([r[4] for r in rows])
    X = {"track": np.c_[cnt], "track(trend)": np.c_[cnt, cnt * wn], "ws": np.c_[sp], "track+ws": np.c_[cnt, sp],
         "track(trend)+ws": np.c_[cnt, cnt * wn, sp], "track(trend)+ws(trend)": np.c_[cnt, cnt * wn, sp, sp * wn]}
    base = np.mean([np.abs(Y[T == t]).mean() for t in set(T)]) * CAP_CSS
    print(f"untuned (edited weights, no tracking): {base:.2f} css px over {len(set(T))} texts")
    best = None
    for name, A in X.items():
        errs = []
        for t in sorted(set(T)):
            tr, te = T != t, T == t
            w = np.linalg.lstsq(A[tr], Y[tr], rcond=None)[0]; errs.append(np.abs(Y[te] - A[te] @ w).mean())
        m = float(np.mean(errs)) * CAP_CSS; print(f"  {name:24s} held-out (leave one text out) {m:.2f} css px")
        if best is None or m < best[0]: best = (m, name)
    print("best:", best[1])
    a0, a1 = np.linalg.lstsq(X["track(trend)"], Y, rcond=None)[0]
    print(f"track(trend): a0={a0:.5f} a1={a1:.5f} -> Regular {a0:+.5f}  SemiBold {a0 + a1 * 80 / 190:+.5f}  Bold {a0 + a1:+.5f} em")
    print("copy into fork_params.json (instances[].track_em) only if 'track(trend)' is the best model above.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    for n in ("verify", "fit"):
        p = sub.add_parser(n); p.add_argument("--metrics", default=os.path.join(HERE, "..", "metrics", "pinterest-sans-measured.json"))
    v = sub.choices["verify"]; v.add_argument("--fonts", required=True); v.add_argument("--plain-regular"); v.add_argument("--plain-bold")
    v.add_argument("--size-adjust", type=float, default=1.08)
    f = sub.choices["fit"]; [f.add_argument(x, required=True) for x in ("--w420", "--w500", "--w610")]
    a = ap.parse_args(); cmd_verify(a) if a.cmd == "verify" else cmd_fit(a)
