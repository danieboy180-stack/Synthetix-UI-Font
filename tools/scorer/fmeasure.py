"""Report-style measurement of a font in real Chromium (grayscale AA, subpixel positioning, DPR 1).
Extraction mirrors the forensic report: ink threshold luminance<=160, 8-connected components, per-glyph ink boxes,
baseline = median bottom of flat-bottom glyphs, gaps g(i,j)=x0(j)-x1(i)-1, stems from sub-pixel coverage sums."""
import os, json, tempfile, numpy as np
from PIL import Image
from scipy import ndimage as ndi
from playwright.sync_api import sync_playwright
from fontTools.ttLib import TTFont
ARGS=['--font-render-hinting=none','--enable-font-subpixel-positioning']
TEXT={'pangram':"Sphinx of black quartz, judge my vow.",'caps':"ABCDEFGHIJKLMNOPQRSTUVWXYZ",'lower':"abcdefghijklmnopqrstuvwxyz",'digits':"0123456789 !?%&@#$()/-:;,.'\""}
FLATBOT=set('nmrzxvwuhlkdbEFHILTZMNAKXYWVBDPR147')
THR=160
def font_cap_em(path):
    f=TTFont(path); gs=f.getGlyphSet(); from fontTools.pens.boundsPen import BoundsPen
    bp=BoundsPen(gs); gs['H'].draw(bp); return bp.bounds[3]/f['head'].unitsPerEm
def render(path, texts, px, weight=400, extra_css=''):
    tmp=tempfile.mkdtemp()
    css=f'@font-face{{font-family:"F";src:url("file://{os.path.abspath(path)}");font-weight:{weight}}}'
    body=''.join(f'<div id=s{i}>{t.replace("&","&amp;").replace("<","&lt;")}</div>' for i,t in enumerate(texts))
    open(tmp+'/t.html','w').write(f'<!doctype html><meta charset=utf-8><style>{css}body{{margin:0;background:#fff;color:#000;font-kerning:normal}}div{{font-family:F;font-weight:{weight};font-size:{px:.4f}px;line-height:2;white-space:pre;display:inline-block;padding:20px 60px;{extra_css}}}</style>{body}')
    out=[]
    with sync_playwright() as p:
        b=p.chromium.launch(args=ARGS); pg=b.new_page(viewport={'width':1800,'height':400},device_scale_factor=1)
        pg.goto('file://'+tmp+'/t.html'); pg.wait_for_timeout(500)
        ok=pg.evaluate("Array.from(document.fonts).map(f=>f.status)")
        for i,t in enumerate(texts):
            rects=pg.evaluate("""(i)=>{const el=document.getElementById('s'+i);const tn=el.firstChild;const er=el.getBoundingClientRect();const r=document.createRange();const o=[];for(let k=0;k<tn.length;k++){r.setStart(tn,k);r.setEnd(tn,k+1);const b=r.getBoundingClientRect();o.push([b.left-er.left,b.right-er.left]);}return {rects:o,w:er.width,h:er.height};}""",i)
            pg.locator(f'#s{i}').screenshot(path=f'{tmp}/s{i}.png'); out.append((f'{tmp}/s{i}.png',rects))
        b.close()
    return out,ok
def analyse(png,rects,text):
    a=np.asarray(Image.open(png).convert('L')).astype(float); ink=a<=THR
    lab,n=ndi.label(ink,structure=np.ones((3,3))); objs=ndi.find_objects(lab)
    chars=[(i,c) for i,c in enumerate(text) if c!=' ']; rc=rects['rects']
    boxes={i:None for i,_ in chars}
    for o in objs:
        x0,x1,y0,y1=o[1].start,o[1].stop-1,o[0].start,o[0].stop-1; cx=(x0+x1)/2
        best=min(chars,key=lambda ic: 0 if rc[ic[0]][0]-1<=cx<=rc[ic[0]][1]+1 else min(abs(cx-rc[ic[0]][0]),abs(cx-rc[ic[0]][1])))[0]
        b=boxes[best]; boxes[best]=[x0,x1,y0,y1] if b is None else [min(b[0],x0),max(b[1],x1),min(b[2],y0),max(b[3],y1)]
    glyphs=[]
    for i,c in chars:
        b=boxes[i]
        if b: glyphs.append(dict(ch=c,x0=b[0],x1=b[1],y0=b[2],y1=b[3],W=b[1]-b[0]+1,H=b[3]-b[2]+1,adv=(rc[i][0],rc[i][1])))
    fb=[g['y1'] for g in glyphs if g['ch'] in FLATBOT]; base=int(np.median(fb)) if fb else None
    return dict(glyphs=glyphs,base=base,gray=a)
def cov(a): return (255-a)/255.0
def measure_all(path,cap_px=49.0,weight=400):
    ce=font_cap_em(path); px=cap_px/ce
    texts=[TEXT['pangram'],TEXT['caps'],TEXT['lower'],TEXT['digits']]
    out,ok=render(path,texts,px,weight)
    R={k:analyse(png,rc,t) for k,(png,rc),t in zip(['pangram','caps','lower','digits'],out,texts)}
    R['_px']=px; R['_ok']=ok; R['_cap_em']=ce; return R
