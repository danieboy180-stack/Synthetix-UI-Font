"""Wordmark outlines from the SemiBold master (no custom kerning applied yet; GPOS kerning is not used here). Working-title text."""
import os, sys
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
f = TTFont(os.path.join(ROOT, 'fonts/ttf/SynthetixUI-SemiBold.ttf')); gs = f.getGlyphSet(); cm = f.getBestCmap()
text = sys.argv[1] if len(sys.argv) > 1 else 'Synthetix'
x = 0; paths = []
for ch in text:
    g = cm[ord(ch)]; pen = SVGPathPen(gs); gs[g].draw(TransformPen(pen, (1, 0, 0, -1, x, 0))); paths.append(pen.getCommands()); x += f['hmtx'][g][0]
d = ' '.join(paths); H = 1000
for name, fill, bg in (('light', '#111111', None), ('dark', '#F2F2F2', '#121212'), ('mono', 'currentColor', None)):
    rect = '<rect x="-60" y="-860" width="%d" height="%d" fill="%s"/>' % (x + 120, 1160, bg) if bg else ''
    open(os.path.join(ROOT, 'ui-kit/wordmark-%s.svg' % name), 'w').write(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="-60 -860 %d 1160" role="img" aria-label="%s">%s<path fill="%s" d="%s"/></svg>\n' % (x + 120, text, rect, fill, d))
print('wordmarks written; advance width', x)
