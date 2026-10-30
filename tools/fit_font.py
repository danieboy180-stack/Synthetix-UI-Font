#!/usr/bin/env python3
"""
fit_font.py - score open-source fonts against the measured UI metrics and
emit the CSS numbers (font-size, weight, letter-spacing, word-spacing) that
make the font land on the measurements.

  pip install pillow numpy
  python fit_font.py --font Figtree-VariableFont_wght.ttf \
                     --font "DMSans[opsz,wght].ttf" \
                     --font InstrumentSans-Regular.ttf --font InstrumentSans-Bold.ttf

Static files: pass each weight as its own --font (grouped by family name before
the first '-'). Variable fonts: the wght axis is swept (300-800, step 10) and the
value whose stem/cap ratio is nearest the target is chosen per weight class.

Scale: css px = screenshot px / 4.5 (see metrics JSON meta). Change --scale if
you re-measure on a different device.
"""
import argparse, json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

SZ = 600
BL = int(SZ * 1.3)
HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_JSON = os.path.join(HERE, "..", "metrics", "pinterest-sans-measured.json")


def load_font(path, wght=None):
    f = ImageFont.truetype(path, SZ)
    axes = None
    try:
        axes = f.get_variation_axes()
    except Exception:
        pass
    if axes and wght is not None:
        vals = []
        for a in axes:
            name = a["name"].decode() if isinstance(a["name"], bytes) else a["name"]
            if name.lower().startswith("weight"):
                vals.append(min(max(wght, a["minimum"]), a["maximum"]))
            else:
                vals.append(a["default"])
        f.set_variation_by_axes(vals)
    return f, axes


def weight_range(axes):
    for a in axes or []:
        name = a["name"].decode() if isinstance(a["name"], bytes) else a["name"]
        if name.lower().startswith("weight"):
            return a["minimum"], a["maximum"]
    return None


def ink(font, s):
    im = Image.new("L", (int(SZ * (len(s) + 3)), SZ * 2), 0)
    ImageDraw.Draw(im).text((SZ // 2, BL), s, font=font, fill=255, anchor="ls")
    a = np.asarray(im).astype(float) / 255
    ys, xs = np.where(a > 0.5)
    if len(xs) == 0:
        return None
    return a, xs.min(), xs.max(), ys.min(), ys.max()


def metrics(font):
    H = ink(font, "H"); x = ink(font, "x"); l = ink(font, "l")
    p = ink(font, "p"); o = ink(font, "o"); n = ink(font, "n")
    cap = BL - H[3]; xh = BL - x[3]
    row = l[0][BL - xh // 2, :]
    return dict(cap=cap, xh=xh, asc=BL - l[3], desc=p[4] - BL + 1,
                ow=o[2] - o[1] + 1, nw=n[2] - n[1] + 1, stem=row.sum())


def pen_positions(font, text, track_px=0.0, word_px=0.0):
    x, pos = 0.0, []
    for i, ch in enumerate(text):
        pos.append(x)
        adv = font.getlength(ch)
        if i + 1 < len(text):
            adv += font.getlength(text[i:i + 2]) - font.getlength(ch) - font.getlength(text[i + 1])
        x += adv + track_px + (word_px if ch == " " else 0)
    return pos


def lsb(font, ch):
    r = ink(font, ch)
    return (r[1] - SZ // 2) if r else 0


def fit_group(font, samples, scale):
    m = metrics(font)
    rows_A, rows_b, per = [], [], []
    for s in samples:
        sc = ((s["cap_px"] / m["cap"]) * (s["xh_px"] / m["xh"])) ** 0.5   # compromise: cap & x-height
        em = SZ * sc
        pos = pen_positions(font, s["text"])
        cand, ci, k = [], 0, 0
        for i, ch in enumerate(s["text"]):
            if ch == " ":
                k += 1
                continue
            cand.append(((pos[i] + lsb(font, ch)) * sc, ci, k)); ci += 1
        tx = np.array(s["glyph_left_px"], float)
        if len(tx) != len(cand):
            continue
        c0 = cand[0][0]
        for (cx, ci, k), t in zip(cand, tx):
            rows_A.append([ci * em, k * em]); rows_b.append(t - (cx - c0))
        per.append(dict(sample=s["name"], font_size_css=float(em / scale)))
    A = np.array(rows_A); b = np.array(rows_b)
    sol = np.linalg.lstsq(A, b, rcond=None)[0]
    mae_b = float(np.abs(b).mean()); mae_a = float(np.abs(b - A @ sol).mean())
    return m, sol, mae_b, mae_a, per


def best_weight(path, axes, target_stem, cap_of=None):
    rng = weight_range(axes)
    if not rng:
        return None, None
    best = None
    for w in range(int(rng[0]), int(rng[1]) + 1, 10):
        if not (300 <= w <= 800):
            continue
        f, _ = load_font(path, w)
        m = metrics(f)
        e = abs(m["stem"] / m["cap"] - target_stem)
        if best is None or e < best[0]:
            best = (e, w)
    return best[1], best[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--font", action="append", required=True)
    ap.add_argument("--metrics", default=DEFAULT_JSON)
    ap.add_argument("--scale", type=float, default=None, help="px per css px (default from JSON)")
    ap.add_argument("--json-out", default=None)
    a = ap.parse_args()

    D = json.load(open(a.metrics))
    scale = a.scale or D["meta"]["scale_px_per_css"]
    tg = D["groups_ratio_to_cap"]
    by_group = {}
    for s in D["samples"]:
        by_group.setdefault(s["group"], []).append(s)

    families = {}
    for p in a.font:
        fam = os.path.basename(p).split("-")[0].split("[")[0]
        families.setdefault(fam, []).append(p)

    results = []
    for fam, paths in families.items():
        res = dict(family=fam, files=[os.path.basename(p) for p in paths], groups={})
        total = 0.0
        for g in ["regular", "semibold", "bold"]:
            t = tg[g]
            # 1) pick file/weight whose stem/cap is closest
            cands = []
            for p in paths:
                f, axes = load_font(p)
                if axes and weight_range(axes):
                    w, _ = best_weight(p, axes, t["stem"])
                    f, _ = load_font(p, w); cands.append((p, w, f))
                else:
                    cands.append((p, None, f))
            def stem_err(c):
                m = metrics(c[2]); return abs(m["stem"] / m["cap"] - t["stem"])
            p, w, f = min(cands, key=stem_err)
            m, sol, mae_b, mae_a, per = fit_group(f, by_group[g], scale)
            cap = m["cap"]
            err = dict(
                xh=m["xh"] / cap / t["xh"] - 1, asc=m["asc"] / cap / t["asc"] - 1,
                desc=m["desc"] / cap / t["desc"] - 1, ow=(m["ow"] / m["xh"]) / t["ow"] - 1,
                nw=(m["nw"] / m["xh"]) / t["nw"] - 1, stem=(m["stem"] / cap) / t["stem"] - 1)
            shape = float(np.mean([abs(err[k]) for k in ["xh", "asc", "ow", "nw"]]))
            total += shape
            res["groups"][g] = dict(
                file=os.path.basename(p), wght=w,
                font_size_css=[round(x["font_size_css"], 2) for x in per],
                letter_spacing_em=round(float(sol[0]), 4), word_spacing_em=round(float(sol[1]), 4),
                glyph_x_error_css_before=round(mae_b / scale, 2), glyph_x_error_css_after=round(mae_a / scale, 2),
                ratio_error_pct={k: round(float(v) * 100, 1) for k, v in err.items()})
        res["score"] = round(total / 3, 4)    # lower = closer proportions
        results.append(res)

    results.sort(key=lambda r: r["score"])
    for r in results:
        print(f"\n{r['family']}   proportion-error score {r['score']:.3f} (lower is better)")
        for g, v in r["groups"].items():
            print(f"  {g:9s} wght={v['wght']} file={v['file']}\n"
                  f"            size(css px per sample)={v['font_size_css']}\n"
                  f"            letter-spacing={v['letter_spacing_em']}em word-spacing={v['word_spacing_em']}em"
                  f"  glyph x-err {v['glyph_x_error_css_before']}->{v['glyph_x_error_css_after']} css px\n"
                  f"            ratio err % {v['ratio_error_pct']}")
    if a.json_out:
        json.dump(results, open(a.json_out, "w"), indent=1)


if __name__ == "__main__":
    sys.exit(main())
