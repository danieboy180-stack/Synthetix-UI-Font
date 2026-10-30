#!/usr/bin/env python3
"""
browser_check.py - render the CSS tokens in headless Chromium at the measured
device scale (4.5x) and compare ink width / first-glyph height to the targets.

  pip install playwright && playwright install chromium
  python browser_check.py --regular /path/InstrumentSans-Regular.ttf --bold /path/InstrumentSans-Bold.ttf
For variable fonts pass the same file to both and set --wght-regular / --wght-bold.
"""
import argparse, json, os, tempfile
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
TESTS = [  # id, text, css class, target sample name
    ("a", "Log in to find ideas and", "reg", "web_b1"),
    ("b", "words required", "reg", "web_b3"),
    ("c", "Endless inspiration awaits", "h1", "web_h1"),
]


def ink(path):
    d = 255 - np.asarray(Image.open(path).convert("L")).astype(float)
    m = d > 127
    xs = np.where(m.any(axis=0))[0]
    lab, _ = ndi.label(m, structure=np.ones((3, 3)))
    objs = ndi.find_objects(lab)
    first = sorted(objs, key=lambda o: o[1].start)[0]
    return xs.max() - xs.min() + 1, first[0].stop - first[0].start


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--regular", required=True); ap.add_argument("--bold", required=True)
    ap.add_argument("--wght-regular", default="400"); ap.add_argument("--wght-bold", default="700")
    ap.add_argument("--metrics", default=os.path.join(HERE, "..", "metrics", "pinterest-sans-measured.json"))
    ap.add_argument("--scale", type=float, default=4.5)
    a = ap.parse_args()
    D = {s["name"]: s for s in json.load(open(a.metrics))["samples"]}
    html = f"""<!doctype html><meta charset=utf-8><style>
@font-face{{font-family:T;src:url("file://{os.path.abspath(a.regular)}");font-weight:{a.wght_regular}}}
@font-face{{font-family:T;src:url("file://{os.path.abspath(a.bold)}");font-weight:{a.wght_bold}}}
body{{margin:0;background:#fff;color:#000;font-family:T;font-kerning:normal}}
div{{white-space:nowrap;padding:10px 6px}}
.reg{{font-size:17.6px;font-weight:{a.wght_regular};letter-spacing:.0072em}}
.h1{{font-size:22.3px;font-weight:{a.wght_bold};letter-spacing:-.0183em;word-spacing:.0497em}}
</style>""" + "".join(f'<div class={c} id={i}>{t}</div>' for i, t, c, _ in TESTS)
    tmp = tempfile.mkdtemp(); hp = os.path.join(tmp, "t.html"); open(hp, "w").write(html)
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": 420, "height": 200}, device_scale_factor=a.scale)
        pg.goto("file://" + hp); pg.wait_for_timeout(500)
        for i, *_ in TESTS:
            pg.locator("#" + i).screenshot(path=os.path.join(tmp, i + ".png"))
        b.close()
    for i, t, c, name in TESTS:
        w, h = ink(os.path.join(tmp, i + ".png")); tw = D[name]["ink_w_px"]
        print(f"{t!r:34s} ink width {w:5d} px vs target {tw:5d}  ({100*(w-tw)/tw:+.1f}%)  first glyph h {h}")


if __name__ == "__main__":
    main()
