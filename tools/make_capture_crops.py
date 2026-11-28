"""Phase B, steps 12/26 (partial): cut text-only crops of the reference pangram out of private phone screenshots.
Why crops: the raw screenshots contain account e-mail, phone numbers and usernames. Only the pangram text rows are kept
(no UI chrome, no personal data). The source file name + SHA-256 are recorded in reference/captures/captures.json so the crops stay traceable.
usage: python tools/make_capture_crops.py [source_dir]      (default: reference/captures_private/, which is git-ignored)"""
import os, sys, json, hashlib
import numpy as np
from PIL import Image
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'reference/captures_private')
PANGRAM_CORE = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
LOW = "abcdefghijklmnopqrstuvwxyz"
SENT = "Sphinx of black quartz, judge my vow."
PUNCT = "!?%&@#$()/-:;,.'\""
SHEETS = [  # id, source file, text of each rendered line (the bio edit sheet wraps differently at each system font size)
    ('A', 'Screenshot_20261031-125556_Pinterest.png', ["Sphinx of black quartz, judge my", "vow.", PANGRAM_CORE[:-2], "YZ " + LOW, "0123456789 " + PUNCT]),
    ('B', 'Screenshot_20261031-125615_Pinterest.png', [SENT, PANGRAM_CORE, LOW, "0123456789 " + PUNCT]),
    ('C', 'Screenshot_20261031-125641_Pinterest.png', [SENT, PANGRAM_CORE, LOW + " 0123456789 !?", PUNCT.replace("!?", "", 1)]),
]
out = []
for sid, fn, lines in SHEETS:
    p = os.path.join(SRC, fn)
    raw = open(p, 'rb').read()
    a = np.array(Image.open(p).convert('L')).astype(float); H, W = a.shape
    y0 = next(y for y in range(H) if (a[y] > 235).mean() > 0.6)            # first fully white row = sheet start
    on = (a[y0:] < 128).sum(1) > 0; bands = []; s = None
    for y, v in enumerate(on):
        if v and s is None: s = y
        if (not v) and s is not None: bands.append((s + y0, y - 1 + y0)); s = None
    text_bands = bands[-len(lines):]                                        # drop the header band (close icon + Edit)
    assert len(text_bands) == len(lines), (sid, bands)
    box = (0, text_bands[0][0] - 14, W, text_bands[-1][1] + 14)
    Image.fromarray(a[box[1]:box[3], box[0]:box[2]].astype(np.uint8), 'L').save(os.path.join(ROOT, 'reference/captures/pangram_%s.png' % sid), optimize=True)
    out.append(dict(id=sid, file='reference/captures/pangram_%s.png' % sid, source_file=fn, source_sha256=hashlib.sha256(raw).hexdigest(),
                    crop_box_xyxy=list(box), source_size_wh=[W, H], lines=lines, weight='Regular (UI body text)',
                    device_note='Android phone screenshot, grayscale antialiasing; system font-size differs per sheet (A largest, C smallest); app: Pinterest, bio edit sheet'))
json.dump(dict(reference='Pinterest Sans UI text as rendered on device (measurement only; no font file used)', captures=out), open(os.path.join(ROOT, 'reference/captures/captures.json'), 'w'), indent=1, ensure_ascii=False)
for o in out: print(o['id'], o['crop_box_xyxy'], o['source_sha256'][:12], 'lines', len(o['lines']))
