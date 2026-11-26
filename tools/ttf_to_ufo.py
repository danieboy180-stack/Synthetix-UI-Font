"""Step 6: convert the shipped V4 static TTFs into UFO sources (one per master) with extractor.
usage: python tools/ttf_to_ufo.py   -> sources/SynthetixUI-<Style>.ufo
Outlines stay quadratic (TrueType) so the round trip can be compared point for point (step 7)."""
import os, sys, shutil
import ufoLib2, extractor
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
STYLES = ['Regular', 'Medium', 'SemiBold']
os.makedirs(os.path.join(ROOT, 'sources'), exist_ok=True)
for s in STYLES:
    src = os.path.join(ROOT, 'fonts/ttf/SynthetixUI-%s.ttf' % s)
    dst = os.path.join(ROOT, 'sources/SynthetixUI-%s.ufo' % s)
    if os.path.exists(dst): shutil.rmtree(dst)
    ufo = ufoLib2.Font()
    extractor.extractUFO(src, ufo)
    # Layout is NOT authored as .fea in this project (the build grafts baseline GSUB/GPOS and merges small fragments).
    # The extracted 700 KB feature text does not recompile (Unknown lookup "MarkToLigature6"), so it is dropped and the
    # three layout tables are stored as raw byte snapshots under sources/layout/ and grafted back after compile.
    ufo.features.text = ''
    ufo.save(dst, overwrite=True)
    ldir = os.path.join(ROOT, 'sources/layout/%s' % s); os.makedirs(ldir, exist_ok=True)
    from fontTools.ttLib import TTFont
    f = TTFont(src)
    for tag in ('GDEF', 'GSUB', 'GPOS'):
        open(os.path.join(ldir, tag + '.bin'), 'wb').write(f.reader[tag])
    print(s, 'glyphs', len(ufo), 'features chars', len(ufo.features.text or ''), '->', os.path.relpath(dst, ROOT))
