#!/usr/bin/env python3
"""
browser_fit.py - measure and fit in real Chromium (subpixel positioning ON, 4.5x DPR).

Why Chromium: Pillow ignores GPOS kerning, and default headless Chromium on Linux rounds
glyph advances to whole css px; both distort spacing numbers. This tool launches Chromium with
--font-render-hinting=none --enable-font-subpixel-positioning, like a phone.

  pip install playwright pillow numpy scipy && playwright install chromium

  # 1) fit: unbaked calibrated weights -> leave-one-out model choice + tracking coefficients
  python build_fork.py --regular R.ttf --bold B.ttf --out /tmp/unb --no-tracking
  python browser_fit.py fit --w420 /tmp/unb/Unbaked-Regular.ttf --w500 /tmp/unb/Unbaked-SemiBold.ttf --w610 /tmp/unb/Unbaked-Bold.ttf

  # 2) verify the built fork (and compare to plain Instrument Sans 400/700)
  python browser_fit.py verify --fonts ../fonts --plain-regular R.ttf --plain-bold B.ttf
"""
import argparse, json, os, tempfile
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
SC = 4.5                                   # screenshot px per css px (see metrics JSON)
K = 17.6 / (56 / SC)                       # css px of font-size per css px of measured cap height
WT = {"regular": 400, "semibold": 600, "bold": 700}
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


def render(samples, faces, size_adjust=1.0):
    """faces: {css_weight: font_path}. Returns {name: (lefts_rel_first_glyph, ink_width)}."""
    tmp = tempfile.mkdtemp()
    css = "".join(f'@font-face{{font-family:"T";src:url("file://{os.path.abspath(p)}");font-weight:{w};'
                  + (f"size-adjust:{size_adjust*100:.0f}%;" if size_adjust != 1 else "") + "}" for w, p in faces.items())
    body = "".join(f'<div id=s{i} style="font-family:T;font-weight:{WT[s["group"]]};'
                   f'font-size:{s["cap_px"] / SC * K / size_adjust:.4f}px">{s["text"]}</div>' for i, s in enumerate(samples))
    hp = os.path.join(tmp, "t.html")
    open(hp, "w").write(f'<!doctype html><meta charset=utf-8><style>{css}body{{margin:0;background:#fff;color:#000;font-kerning:normal}}'
                        f'div{{white-space:nowrap;padding:12px 8px;display:inline-block}}</style>{body}')
    out = {}
    with sync_playwright() as p:
        b = p.chromium.launch(args=ARGS); pg = b.new_page(viewport={"width": 900, "height": 300}, device_scale_factor=SC)
        pg.goto("file://" + hp); pg.wait_for_timeout(600)
        for i, s in enumerate(samples):
            png = os.path.join(tmp, f"s{i}.png"); pg.locator(f"#s{i}").screenshot(path=png)
            l, w = glyph_lefts(png)
            out[s["name"]] = (l - l[0], w) if len(l) == len(s["text"].replace(" ", "")) else None
        b.close()
    return out


def load(path):
    return json.load(open(path))["samples"]


def cmd_verify(a):
    S = load(a.metrics)
    def score(tag, faces, sa):
        R = render(S, faces, sa); errs, wd = [], []
        for s in S:
            r = R[s["name"]]
            if r is None: continue
            errs.append(np.abs(np.array(s["glyph_left_px"], float) - r[0]).mean() / SC)
            wd.append(100 * (r[1] - s["ink_w_px"]) / s["ink_w_px"])
        print(f"{tag:34s} glyph x-error {np.mean(errs):.2f} css px   width |err| {np.mean(np.abs(wd)):.2f}%  (n={len(errs)})")
    score("Synthetix UI fork", {400: f"{a.fonts}/SynthetixUI-Regular.ttf", 600: f"{a.fonts}/SynthetixUI-SemiBold.ttf",
                                700: f"{a.fonts}/SynthetixUI-Bold.ttf"}, 1.10)
    if a.plain_regular:
        score("Plain Instrument Sans 400/700", {400: a.plain_regular, 700: a.plain_bold}, 1.0)


def cmd_fit(a):
    S = load(a.metrics); W = {"regular": a.w420, "semibold": a.w500, "bold": a.w610}
    faces = {WT[g]: p for g, p in W.items()}; R = render(S, faces, 1.0)
    wn = {"regular": 0.0, "semibold": 80 / 190, "bold": 1.0}; rows = []
    for s in S:
        r = R[s["name"]]
        if r is None: continue
        em = s["cap_px"] * K; w = wn[s["group"]]; ci = 0; A = []
        for _ in s["glyph_left_px"]:
            A.append([ci * em, ci * em * w, 0, 0]); ci += 1
        k = 0; ci = 0
        for ch in s["text"]:                                     # word-space columns
            if ch == " ": k += 1; continue
            A[ci][2] = k * em; A[ci][3] = k * em * w; ci += 1
        rows.append((s["name"], np.array(A), np.array(s["glyph_left_px"], float) - r[0]))
    base = np.mean([np.abs(b).mean() for _, _, b in rows]) / SC
    print(f"untuned (calibrated weights, no tracking): {base:.2f} css px")
    models = {"track(const)": [0], "ws(const)": [2], "track+ws(const)": [0, 2], "ws(trend)": [2, 3],
              "track(trend)": [0, 1], "track+ws(trend)": [0, 1, 2, 3]}
    best = None
    for name, cols in models.items():
        outs = []
        for h in range(len(rows)):
            tr = [i for i in range(len(rows)) if i != h]
            A = np.vstack([rows[i][1][:, cols] for i in tr]); b = np.concatenate([rows[i][2] for i in tr])
            sol = np.linalg.lstsq(A, b, rcond=None)[0]
            outs.append(np.abs(rows[h][2] - rows[h][1][:, cols] @ sol).mean() / SC)
        m = float(np.mean(outs)); print(f"  {name:18s} held-out {m:.2f} css px")
        if best is None or m < best[0]: best = (m, name, cols)
    print("best by leave-one-out:", best[1])
    cols = [0, 1]; A = np.vstack([r[1][:, cols] for r in rows]); b = np.concatenate([r[2] for r in rows])
    a0, a1 = np.linalg.lstsq(A, b, rcond=None)[0]
    print(f"track(trend): a0={a0:.5f} a1={a1:.5f}  ->  Regular {a0:+.5f}  SemiBold {a0 + a1 * 80 / 190:+.5f}  Bold {a0 + a1:+.5f} em")
    print("copy into fork_params.json (instances[].track_em) only if 'track(trend)' is the best model above.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    for n in ("verify", "fit"):
        p = sub.add_parser(n); p.add_argument("--metrics", default=os.path.join(HERE, "..", "metrics", "pinterest-sans-measured.json"))
    v = sub.choices["verify"]; v.add_argument("--fonts", required=True); v.add_argument("--plain-regular"); v.add_argument("--plain-bold")
    f = sub.choices["fit"]; [f.add_argument(x, required=True) for x in ("--w420", "--w500", "--w610")]
    a = ap.parse_args(); cmd_verify(a) if a.cmd == "verify" else cmd_fit(a)
